// Resources/script.js
(function() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileNameSpan = document.getElementById('file-name');
    const detectBtn = document.getElementById('detect-btn');
    const loadingDiv = document.getElementById('loading');
    const messageDiv = document.getElementById('message');
    const resultModal = document.getElementById('result-modal');
    const resultImg = document.getElementById('result-img');
    const closeModalBtn = document.querySelector('.close-modal');
    const modalOverlay = document.querySelector('.modal-overlay');

    let currentFile = null;
    let isDetecting = false;

    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.classList.remove('hidden');
        setTimeout(() => {
            if (messageDiv && !messageDiv.classList.contains('hidden')) {
                messageDiv.classList.add('hidden');
            }
        }, 3000);
    }

    function hideMessage() {
        messageDiv.classList.add('hidden');
    }

    function resetPage() {
        isDetecting = false;
        currentFile = null;
        if (fileInput) fileInput.value = '';
        if (fileNameSpan) fileNameSpan.textContent = '';
        if (detectBtn) detectBtn.disabled = true;
        if (loadingDiv) loadingDiv.classList.add('hidden');
        hideMessage();
        if (resultModal) resultModal.classList.remove('active');
        if (resultImg) resultImg.src = '';
    }

    function showModal() {
        if (resultModal) resultModal.classList.add('active');
    }

    function hideModal() {
        if (resultModal) resultModal.classList.remove('active');
    }

    function handleFileSelect(file) {
        if (!file) return;
        if (!file.type.startsWith('image/')) {
            showMessage('请选择有效的图片文件（jpg, png, bmp等）', 'error');
            return;
        }
        currentFile = file;
        fileNameSpan.textContent = `已选择: ${file.name}`;
        detectBtn.disabled = false;
        hideMessage();
        if (resultModal && resultModal.classList.contains('active')) {
            hideModal();
        }
    }

    if (uploadArea) {
        uploadArea.addEventListener('click', () => fileInput.click());
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            } else {
                currentFile = null;
                fileNameSpan.textContent = '';
                detectBtn.disabled = true;
            }
        });
    }

    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.backgroundColor = '#e8f4fc';
            uploadArea.style.borderColor = '#2980b9';
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.backgroundColor = '#f8fafc';
            uploadArea.style.borderColor = '#3498db';
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.backgroundColor = '#f8fafc';
            uploadArea.style.borderColor = '#3498db';
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                if (file.type.startsWith('image/')) {
                    handleFileSelect(file);
                } else {
                    showMessage('仅支持图片文件拖拽', 'error');
                }
            }
        });
    }

    if (detectBtn) {
        detectBtn.addEventListener('click', async () => {
            if (!currentFile) {
                showMessage('请先选择一张图片', 'error');
                return;
            }
            if (isDetecting) {
                showMessage('检测进行中，请稍后...', 'error');
                return;
            }

            isDetecting = true;
            detectBtn.disabled = true;
            loadingDiv.classList.remove('hidden');
            hideMessage();
            if (resultModal && resultModal.classList.contains('active')) {
                hideModal();
            }

            const formData = new FormData();
            formData.append('file', currentFile);

            try {
                const API_URL = 'https://api.ptcr-check.xyz/predict';
                const response = await fetch(API_URL, {
                    method: 'POST',
                    body: formData,
                    signal: AbortSignal.timeout ? AbortSignal.timeout(30000) : undefined,
                });

                if (!response.ok) {
                    let errorDetail = `HTTP ${response.status}`;
                    try {
                        const errData = await response.json();
                        errorDetail = errData.message || errData.detail || errorDetail;
                    } catch (e) {}
                    throw new Error(`请求失败: ${errorDetail}`);
                }

                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.message || '服务器返回失败状态');
                }
                if (!data.image) {
                    throw new Error('服务器未返回检测结果图片');
                }

                resultImg.src = data.image;
                showModal();
            } catch (error) {
                console.error('检测失败:', error);
                let friendlyMsg = error.message || '网络异常或服务器不可用';
                if (friendlyMsg.includes('Failed to fetch') || friendlyMsg.includes('NetworkError')) {
                    friendlyMsg = '无法连接服务器，请稍后再试';
                } else if (friendlyMsg.includes('timeout')) {
                    friendlyMsg = '检测超时，请检查网络或稍后重试';
                }
                showMessage(`检测失败: ${friendlyMsg}`, 'error');
            } finally {
                isDetecting = false;
                detectBtn.disabled = false;
                loadingDiv.classList.add('hidden');
            }
        });
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            hideModal();
        });
    }
    if (modalOverlay) {
        modalOverlay.addEventListener('click', () => hideModal());
    }
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && resultModal && resultModal.classList.contains('active')) {
            hideModal();
        }
    });
    if (resultImg) {
        resultImg.addEventListener('click', (e) => e.stopPropagation());
    }

    resetPage();
})();