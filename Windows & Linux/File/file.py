import cv2
import numpy as np
import os
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
from ultralytics import YOLO

# --- 全局配置 ---
CONFIG = {
    "model_path": os.path.join("weights", "best.pt"),
    "font_path_image": "./NotoSansHans.ttf",
    "save_dir": "./defect_logs",
    "interval": 2.0  # 视频截帧频率
}

CLASS_CONFIG = {
    "ptcr": {"cn": "PTCR", "priority": 1, "color": (34, 197, 94)},
    "laohua": {"cn": "老化", "priority": 2, "color": (255, 165, 0)},
    "dianjipianyi": {"cn": "电极偏移", "priority": 3, "color": (255, 0, 255)},
    "mosun": {"cn": "磨损", "priority": 4, "color": (0, 122, 255)},
    "quesun": {"cn": "缺损", "priority": 5, "color": (255, 50, 50)},
    "shaodianji": {"cn": "烧电极", "priority": 6, "color": (250, 204, 21)}
}

class PTCRCrossPlatformAnalyzer:
    def __init__(self, window):
        self.window = window
        self.window.title("PTCR 缺陷检测监控终端 ~ PTCR Defect Monitor")
        self.window.geometry("1400x850")
        self.window.configure(bg="#0a0a0a")

        # 核心状态逻辑
        self.active_thread_id = 0 
        self.current_cap = None
        
        # 加载环境
        if not os.path.exists(CONFIG["save_dir"]): 
            os.makedirs(CONFIG["save_dir"])
            
        self.model = YOLO(CONFIG["model_path"])
        
        self.init_ui()

    def init_ui(self):
        # 字体兼容处理：Windows用微软雅黑，其他系统用默认sans-serif
        ui_font_name = "微软雅黑" if os.name == 'nt' else "sans-serif"
        self.f_title = (ui_font_name, 18, "bold")
        self.f_sm = (ui_font_name, 11)
        self.f_mono = (ui_font_name, 10)
        self.f_big_status = (ui_font_name, 18, "bold") 

        # --- 顶部导航 ---
        header = tk.Frame(self.window, bg="#1a1a1a", height=70)
        header.pack(fill=tk.X)
        tk.Label(header, text="PTCR 缺陷检测监控终端 / PTCR Defect Monitor", fg="#FACC15", bg="#1a1a1a", font=self.f_title).pack(side=tk.LEFT, padx=30)
        
        # 统一操作按钮
        tk.Button(header, text="📂 导入文件 (IMAGE/VIDEO)", command=self.select_file, 
                  bg="#007aff", fg="#000", relief=tk.FLAT, padx=20, font=self.f_sm).pack(side=tk.RIGHT, padx=30, pady=15)

        # --- 主操作区 ---
        self.main_frame = tk.Frame(self.window, bg="#0a0a0a")
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        self.main_frame.columnconfigure(0, weight=1, uniform="group")
        self.main_frame.columnconfigure(1, weight=1, uniform="group")
        self.main_frame.rowconfigure(0, weight=1)

        # 左栏：实时/当前分析
        self.l_box = tk.LabelFrame(self.main_frame, text=" [ 当前分析源 / SOURCE ] ", fg="#666", bg="#0a0a0a", font=self.f_mono, labelanchor="n")
        self.l_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.l_view = tk.Label(self.l_box, bg="#000", text="等待文件导入...", fg="#444")
        self.l_view.pack(expand=True, fill=tk.BOTH)

        # 右栏：异常存档
        self.r_box = tk.LabelFrame(self.main_frame, text=" [ 最近异常记录 / DEFECT ] ", fg="#FACC15", bg="#0a0a0a", font=self.f_mono, labelanchor="n")
        self.r_box.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.r_view = tk.Label(self.r_box, bg="#000", text="暂无记录", fg="#444")
        self.r_view.pack(expand=True, fill=tk.BOTH)

        # 底部状态
        self.status = tk.Label(self.window, text="SYSTEM_READY | AWAITING_INPUT", fg="#22c55e", bg="#0a0a0a", font=self.f_mono, pady=5)
        self.status.pack(fill=tk.X)

    def select_file(self):
        # 跨平台标准文件对话框
        path = filedialog.askopenfilename(filetypes=[("Media Files", "*.jpg *.png *.jpeg *.mp4 *.avi *.mov")])
        if path:
            self.dispatch_task(path)

    def dispatch_task(self, path):
        """ 任务分发器：支持随时切换文件 """
        self.active_thread_id += 1 # 变更ID，强制让正在跑的旧视频线程退出循环
        if self.current_cap:
            self.current_cap.release()

        # UI 视觉重置
        self.l_view.configure(image='', text="PROCESSING...")
        self.status.config(text=f"LOADING: {os.path.basename(path)}", fg="#FACC15")

        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.png', '.jpeg']:
            threading.Thread(target=self.process_static, args=(path,), daemon=True).start()
        elif ext in ['.mp4', '.avi', '.mov']:
            threading.Thread(target=self.process_video, args=(path, self.active_thread_id), daemon=True).start()

    def process_static(self, path):
        frame = cv2.imread(path)
        if frame is not None:
            # 左侧展示原图
            self.update_ui_image(self.l_view, frame)
            
            # 推理
            results = self.model.predict(source=frame, conf=0.25, verbose=False)
            annotated, has_defect = self.render_chinese(frame, results)
            
            if has_defect:
                self.update_ui_image(self.r_view, annotated)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(CONFIG["save_dir"], f"static_defect_{ts}.jpg")
                cv2.imwrite(save_path, annotated)
                
                self.status.config(text=f"⚠️ 分析完成：检测到缺陷！已保存至 {save_path}", fg="#ef4444")
            else:
                self.r_view.configure(
                    image='', 
                    text="样 本 正 常\n(PASS)", 
                    fg="#22c55e", 
                    font=self.f_big_status 
                )
                self.status.config(text="✅ 分析完成：该样本未发现异常", fg="#22c55e")

    def process_video(self, path, tid):
        cap = cv2.VideoCapture(path)
        self.current_cap = cap
        last_check_time = 0
        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        while tid == self.active_thread_id:
            ret, frame = cap.read()
            if not ret: break

            # --- 始终在左侧显示原始视频流 ---
            self.update_ui_image(self.l_view, frame)

            now = time.time()
            if now - last_check_time > CONFIG["interval"]:
                last_check_time = now
                # 后台默默推理，不干扰左侧画面
                results = self.model.predict(source=frame, conf=0.25, verbose=False)
                annotated, has_defect = self.render_chinese(frame, results)
                
                if has_defect:
                    self.update_ui_image(self.r_view, annotated)
                    ts = datetime.now().strftime("%H%M%S")
                    cv2.imwrite(os.path.join(CONFIG["save_dir"], f"alert_{ts}.jpg"), annotated)
                    self.status.config(text=f"⚠️ DETECTION ALERT @ {ts}", fg="#ef4444")
            
            time.sleep(1/fps)
        
        cap.release()

    def render_chinese(self, bgr_img, results):
        """ 保持标注渲染与云端/监控端一致 """
        pil_img = Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        try:
            font = ImageFont.truetype(CONFIG["font_path_image"], size=24)
        except:
            font = ImageFont.load_default()

        has_defect = False
        detections = []
        for box in results[0].boxes:
            name = results[0].names[int(box.cls)].lower().strip()
            if name != "ptcr": has_defect = True
            cfg = CLASS_CONFIG.get(name, {"cn": name, "priority": 0, "color": (128,128,128)})
            detections.append({
                "box": box.xyxy[0].tolist(), "cn": cfg["cn"], "color": cfg["color"], 
                "priority": cfg["priority"], "label": f"{cfg['cn']} {float(box.conf):.2f}"
            })

        detections.sort(key=lambda x: x["priority"])
        for d in detections:
            draw.rectangle(d["box"], outline=d["color"], width=4)
            tw, th = font.getbbox(d["label"])[2:]
            draw.rectangle([d["box"][0], d["box"][1]-th-5, d["box"][0]+tw+8, d["box"][1]], fill=d["color"])
            draw.text((d["box"][0]+4, d["box"][1]-th-5), d["label"], font=font, fill=(0,0,0))
            
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR), has_defect

    def update_ui_image(self, label, cv_img):
        """ 自动适配窗口大小的图像缩放渲染 """
        try:
            # 获取容器当前尺寸
            self.window.update_idletasks()
            w_w, w_h = label.winfo_width(), label.winfo_height()
            if w_w < 10: w_w, w_h = 600, 450

            img_h, img_w = cv_img.shape[:2]
            ratio = min(w_w/img_w, w_h/img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))

            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb).resize(new_size, Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            
            label.imgtk = tk_img
            label.configure(image=tk_img)
        except:
            pass

    def on_closing(self):
        self.active_thread_id += 1 
        if self.current_cap: self.current_cap.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PTCRCrossPlatformAnalyzer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()