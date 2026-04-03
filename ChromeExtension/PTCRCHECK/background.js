const SITE_URL = "https://ptcr-check.xyz/";

// 1. 创建右键菜单
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "analyzePTCR",
    title: "分析此图片的PTCR缺陷",
    contexts: ["image"]
  });
});

// 2. 监听右键点击
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "analyzePTCR") {
    const imageUrl = info.srcUrl;
    // 将 URL 存入本地存储，供 content.js 读取
    chrome.storage.local.set({ "targetImageUrl": imageUrl }, () => {
      chrome.tabs.create({ url: `${SITE_URL}?from_ext=1` });
    });
  }
});

// 3. 监听左键点击扩展图标
chrome.action.onClicked.addListener(() => {
  chrome.tabs.create({ url: SITE_URL });
});

// 4. 核心：帮前台下载跨域图片
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "downloadImage") {
    fetch(message.url)
      .then(response => response.blob())
      .then(blob => {
        // 将 blob 转为 base64 字符串传回
        const reader = new FileReader();
        reader.onloadend = () => sendResponse({ data: reader.result });
        reader.readAsDataURL(blob);
      })
      .catch(error => {
        console.error("下载失败:", error);
        sendResponse({ error: error.message });
      });
    return true; // 保持异步通道
  }
});