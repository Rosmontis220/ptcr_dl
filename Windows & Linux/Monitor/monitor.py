import cv2
import numpy as np
import os
import time
from datetime import datetime
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from ultralytics import YOLO

# --- 配置区 ---
CONFIG = {
    "model_path": "weights/best.pt",
    "font_path_image": "./NotoSansHans.ttf",
    "save_dir": "./defect_logs",
    "interval": 1.5,
    "camera_id": 0
}

CLASS_CONFIG = {
    "ptcr": {"cn": "PTCR", "priority": 1, "color": (34, 197, 94)},
    "laohua": {"cn": "老化", "priority": 2, "color": (255, 165, 0)},
    "dianjipianyi": {"cn": "电极偏移", "priority": 3, "color": (255, 0, 255)},
    "mosun": {"cn": "磨损", "priority": 4, "color": (0, 122, 255)},
    "quesun": {"cn": "缺损", "priority": 5, "color": (255, 50, 50)},
    "shaodianji": {"cn": "烧电极", "priority": 6, "color": (250, 204, 21)}
}

class PTCRMonitorApp:
    def __init__(self, window):
        self.window = window
        self.window.title("PTCR 缺陷检测监控终端 ~ PTCR Defect Monitor")
        self.window.geometry("1440x900") 
        self.window.configure(bg="#0a0a0a")
        
        self.current_camera_idx = 0
        self.cap = None
        self.last_analysis_time = 0
        
        # UI 字体
        self.ui_font_main = ("微软雅黑", 18, "bold")
        self.ui_font_sm = ("微软雅黑", 11)
        self.ui_font_mono = ("Consolas", 10)

        if not os.path.exists(CONFIG["save_dir"]): os.makedirs(CONFIG["save_dir"])
        self.model = YOLO(CONFIG["model_path"])
        
        self.init_ui()
        self.init_camera(self.current_camera_idx)
        self.update_loop()

    def init_ui(self):
        # 顶部栏
        self.header = tk.Frame(self.window, bg="#1a1a1a", height=70)
        self.header.pack(fill=tk.X)
        tk.Label(self.header, text="PTCR 缺陷检测监控终端 / PTCR Defect Monitor", 
                 fg="#FACC15", bg="#1a1a1a", font=self.ui_font_main).pack(side=tk.LEFT, padx=30)
        
        tk.Button(self.header, text="📷 切换摄像头 / SWITCH", 
                  command=self.switch_camera, bg="#333", fg="#fff", 
                  relief=tk.FLAT, padx=20, font=self.ui_font_sm).pack(side=tk.RIGHT, padx=30, pady=15)

        # --- 核心布局：强制 50/50 分割 ---
        self.main_frame = tk.Frame(self.window, bg="#0a0a0a")
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        
        # 这里的 uniform="group1" 是让两列宽度严格相等的关键
        self.main_frame.columnconfigure(0, weight=1, uniform="group1")
        self.main_frame.columnconfigure(1, weight=1, uniform="group1")
        self.main_frame.rowconfigure(0, weight=1)

        # 左栏：LIVE_FEED
        self.left_box = tk.LabelFrame(self.main_frame, text=" [ LIVE_SAMPLE_ANALYSIS ] ", 
                                     fg="#666", bg="#0a0a0a", font=self.ui_font_mono, labelanchor="n")
        self.left_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # 为了让图片居中，Label 使用 pack 填充
        self.left_view = tk.Label(self.left_box, bg="#000")
        self.left_view.pack(expand=True, fill=tk.BOTH)

        # 右栏：DEFECT_ALERT
        self.right_box = tk.LabelFrame(self.main_frame, text=" [ LATEST_DEFECT_DETECTED ] ", 
                                      fg="#FACC15", bg="#0a0a0a", font=self.ui_font_mono, labelanchor="n")
        self.right_box.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.right_view = tk.Label(self.right_box, bg="#000")
        self.right_view.pack(expand=True, fill=tk.BOTH)

        # 底部栏
        self.footer = tk.Frame(self.window, bg="#111", height=35)
        self.footer.pack(fill=tk.X)
        self.status_label = tk.Label(self.footer, text="SYSTEM_READY | CAM_ID: 0", 
                                    fg="#22c55e", bg="#111", font=self.ui_font_mono)
        self.status_label.pack(side=tk.LEFT, padx=30)

    def init_camera(self, idx):
        if self.cap: self.cap.release()
        self.cap = cv2.VideoCapture(idx)
        if not self.cap.isOpened(): self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        return self.cap.isOpened()

    def switch_camera(self):
        new_idx = self.current_camera_idx + 1
        if self.init_camera(new_idx):
            self.current_camera_idx = new_idx
        else:
            self.current_camera_idx = 0
            self.init_camera(0)

    def draw_annotations(self, bgr_img, results):
        img_pil = Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        try:
            font = ImageFont.truetype(CONFIG["font_path_image"], size=24)
        except:
            font = ImageFont.load_default()

        has_defect = False
        detections = []
        for box in results[0].boxes:
            raw_name = results[0].names[int(box.cls)].lower().strip()
            conf = float(box.conf)
            if raw_name != "ptcr": has_defect = True
            config = CLASS_CONFIG.get(raw_name, {"cn": raw_name, "priority": 0, "color": (128,128,128)})
            detections.append({
                "box": box.xyxy[0].tolist(), "cn": config["cn"], "color": config["color"],
                "priority": config["priority"], "label": f"{config['cn']} {conf:.2f}"
            })

        detections.sort(key=lambda x: x["priority"])
        for d in detections:
            draw.rectangle(d["box"], outline=d["color"], width=4)
            tw, th = font.getbbox(d["label"])[2:]
            draw.rectangle([d["box"][0], d["box"][1]-th-5, d["box"][0]+tw+8, d["box"][1]], fill=d["color"])
            draw.text((d["box"][0]+4, d["box"][1]-th-5), d["label"], font=font, fill=(0,0,0)) 

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR), has_defect

    def update_loop(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                now = time.time()
                if now - self.last_analysis_time > CONFIG["interval"]:
                    self.last_analysis_time = now
                    results = self.model.predict(source=frame, conf=0.25, verbose=False)
                    annotated, has_defect = self.draw_annotations(frame, results)
                    self.set_tk_image(self.left_view, annotated)
                    if has_defect:
                        self.set_tk_image(self.right_view, annotated)
                        ts = datetime.now().strftime("%H%M%S")
                        cv2.imwrite(os.path.join(CONFIG["save_dir"], f"defect_{ts}.jpg"), annotated)
                        self.status_label.config(text=f"⚠️ ALERT: DEFECT DETECTED AT {ts}", fg="#ef4444")
                else:
                    self.set_tk_image(self.left_view, frame)

        self.window.after(20, self.update_loop)

    def set_tk_image(self, label_widget, cv_img):
        """ 强化版图片自适应：不抢占空间，只填充空间 """
        # 强制刷新布局以获取最新容器尺寸
        label_widget.update_idletasks()
        
        # 获取 LabelFrame 给 Label 分配的内部实际像素（减去 padding）
        win_w = label_widget.winfo_width()
        win_h = label_widget.winfo_height()

        # 初始加载时的兜底尺寸
        if win_w < 50: win_w = self.window.winfo_width() // 2 - 40
        if win_h < 50: win_h = 600

        img_h, img_w = cv_img.shape[:2]
        
        # 寻找不拉伸图片的最佳缩放比例
        ratio = min(win_w / img_w, win_h / img_h)
        new_w = max(1, int(img_w * ratio))
        new_h = max(1, int(img_h * ratio))

        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb).resize((new_w, new_h), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(pil_img)
        
        label_widget.imgtk = tk_img
        label_widget.configure(image=tk_img)

    def on_closing(self):
        if self.cap: self.cap.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PTCRMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()