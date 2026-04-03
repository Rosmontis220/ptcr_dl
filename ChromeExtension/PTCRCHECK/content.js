(async function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('from_ext') === '1') {
        
        // 1. 从存储中读取待处理图片 URL
        chrome.storage.local.get(["targetImageUrl"], function(result) {
            const imageUrl = result.targetImageUrl;
            if (!imageUrl) return;

            console.log("正在准备检测图片...");

            // 2. 请求后台下载（避开跨域403）
            chrome.runtime.sendMessage({
                action: "downloadImage",
                url: imageUrl
            }, async function(response) {
                if (response && response.data) {
                    await injectToWebPage(response.data);
                } else {
                    alert("图片读取失败，可能是源站限制了访问。");
                }
            });
        });
    }
})();

async function injectToWebPage(base64Data) {
    try {
        // 1. 转为 File 对象
        const res = await fetch(base64Data);
        const blob = await res.blob();
        const file = new File([blob], "ptcr_image.png", { type: blob.type });

        // 2. 获取网页上的元素
        const fileInput = document.getElementById('file-input');
        const detectBtn = document.getElementById('detect-btn');

        if (fileInput && detectBtn) {
            // 3. 模拟文件填充
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;

            // 4. 触发 script.js 里的 onchange 事件 (handleSample)
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
    } catch (e) {
        console.error("注入失败", e);
    }
}