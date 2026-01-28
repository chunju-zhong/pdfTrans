// 文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 获取表单元素
    const form = document.getElementById('translate-form');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const resultContainer = document.getElementById('result-container');
    const downloadLink = document.getElementById('download-link');
    const cancelBtn = document.getElementById('cancel-btn');
    
    // 页码选择相关元素
    const fileInput = document.getElementById('pdf_file');
    const totalPagesElement = document.getElementById('total-pages');
    const selectAllPagesCheckbox = document.getElementById('select-all-pages');
    const pageRangeInput = document.getElementById('page-range');
    
    let progressInterval = null;
    let translationTaskId = null;
    let currentTotalPages = 0;
    
    // 表单提交事件处理
    form.addEventListener('submit', function(e) {
        // 阻止表单默认提交行为
        e.preventDefault();
        
        // 显示进度容器，隐藏结果容器
        progressContainer.style.display = 'block';
        resultContainer.style.display = 'none';
        
        // 初始化进度
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';
        progressText.textContent = '准备开始...';
        
        // 准备表单数据
        const formData = new FormData(form);
        
        // 如果全选，则不传递page_range参数或传递空值
        if (selectAllPagesCheckbox.checked) {
            formData.delete('page_range');
        }
        
        // 异步提交表单
        submitForm(formData);
    });
    
    // 异步提交表单函数
    function submitForm(formData) {
        const xhr = new XMLHttpRequest();
        
        // 设置请求
        xhr.open('POST', '/translate', true);
        
        // 处理响应
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        translationTaskId = response.task_id;
                        // 开始轮询进度
                        startProgressPolling();
                    } else {
                        updateProgress(0, 'error', response.message || '翻译请求失败');
                    }
                } catch (error) {
                    updateProgress(0, 'error', '解析响应失败: ' + error.message);
                }
            } else {
                updateProgress(0, 'error', '服务器错误: ' + xhr.status);
            }
        };
        
        // 处理网络错误
        xhr.onerror = function() {
            updateProgress(0, 'error', '网络连接错误');
        };
        
        // 发送请求
        xhr.send(formData);
    }
    
    // 开始进度轮询
    function startProgressPolling() {
        // 清除可能存在的旧轮询
        if (progressInterval) {
            clearInterval(progressInterval);
        }
        
        // 每1秒查询一次进度
        progressInterval = setInterval(function() {
            getTranslationProgress();
        }, 1000);
        
        // 立即查询一次
        getTranslationProgress();
    }
    
    // 查询翻译进度
    function getTranslationProgress() {
        if (!translationTaskId) return;
        
        const xhr = new XMLHttpRequest();
        xhr.open('GET', `/progress/${translationTaskId}`, true);
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const progressData = JSON.parse(xhr.responseText);
                    updateProgress(progressData.progress, progressData.status, progressData.message);
                    
                    // 如果翻译完成，停止轮询
                    if (progressData.status === 'completed') {
                        clearInterval(progressInterval);
                        // 显示下载链接
                        showDownloadLink(progressData.result_file, progressData.attachments || []);
                    } else if (progressData.status === 'error') {
                        clearInterval(progressInterval);
                    }
                } catch (error) {
                    console.error('解析进度响应失败:', error);
                }
            } else {
                console.error('获取进度失败:', xhr.status);
            }
        };
        
        xhr.onerror = function() {
            console.error('获取进度网络错误');
        };
        
        xhr.send();
    }
    
    // 更新进度显示
    function updateProgress(percentage, status, message) {
        // 确保百分比在0-100之间
        const safePercentage = Math.max(0, Math.min(100, percentage));
        
        progressBar.style.width = safePercentage + '%';
        progressBar.textContent = safePercentage + '%';
        
        // 根据状态更新文本
        let statusText = message;
        if (!statusText) {
            switch (status) {
                case 'processing':
                    statusText = '正在处理...';
                    break;
                case 'completed':
                    statusText = '翻译完成！';
                    break;
                case 'error':
                    statusText = '翻译失败！';
                    break;
                default:
                    statusText = '准备开始...';
            }
        }
        
        progressText.textContent = statusText;
        
        // 根据状态更新样式
        if (status === 'error') {
            progressBar.className = 'progress-bar error';
        } else if (status === 'completed') {
            progressBar.className = 'progress-bar completed';
        } else {
            progressBar.className = 'progress-bar processing';
        }
    }
    
    // 显示下载链接
    function showDownloadLink(fileName, attachments) {
        const downloadLinksContainer = document.getElementById('download-links');
        const resultMessage = document.getElementById('result-message');
        
        // 清空现有的下载链接
        downloadLinksContainer.innerHTML = '';
        
        // 添加主要文件下载链接
        const mainLink = document.createElement('a');
        mainLink.href = `/download_file/${fileName}`;
        mainLink.className = 'btn btn-success';
        mainLink.textContent = `下载翻译后的${fileName.endsWith('.pdf') ? 'PDF' : 'Word'}文件`;
        downloadLinksContainer.appendChild(mainLink);
        
        // 添加附件下载链接
        if (attachments && attachments.length > 0) {
            resultMessage.textContent = '您的文件已翻译完成，点击下方链接下载：';
            
            attachments.forEach((attachment, index) => {
                const attachmentLink = document.createElement('a');
                attachmentLink.href = `/download_file/${attachment}`;
                attachmentLink.className = 'btn btn-success';
                attachmentLink.style.marginLeft = '10px';
                attachmentLink.textContent = `下载翻译后的${attachment.endsWith('.docx') ? 'Word' : 'PDF'}文件`;
                downloadLinksContainer.appendChild(attachmentLink);
            });
        } else {
            resultMessage.textContent = '您的文件已翻译完成，点击下方链接下载：';
        }
        
        // 显示结果容器
        resultContainer.style.display = 'block';
    }
    
    // 取消翻译任务
    function cancelTranslation() {
        if (!translationTaskId) return;
        
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/cancel/${translationTaskId}`, true);
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        updateProgress(0, 'error', '翻译已取消');
                    } else {
                        updateProgress(0, 'error', '取消失败: ' + response.message);
                    }
                } catch (error) {
                    updateProgress(0, 'error', '取消失败: 解析响应错误');
                }
            } else {
                updateProgress(0, 'error', '取消失败: 服务器错误');
            }
            
            // 清理资源
            cleanupTask();
        };
        
        xhr.onerror = function() {
            updateProgress(0, 'error', '取消失败: 网络错误');
            cleanupTask();
        };
        
        xhr.send();
    }
    
    // 清理任务资源
    function cleanupTask() {
        // 清除进度轮询
        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        
        // 重置任务ID
        translationTaskId = null;
    }
    
    // 重置表单和进度
    function resetForm() {
        // 隐藏进度容器和结果容器
        progressContainer.style.display = 'none';
        resultContainer.style.display = 'none';
        
        // 重置表单
        form.reset();
        
        // 清理资源
        cleanupTask();
        
        // 重置页码相关UI
        resetPageRangeUI();
    }
    
    // 重置页码相关UI
    function resetPageRangeUI() {
        currentTotalPages = 0;
        totalPagesElement.innerHTML = '当前PDF共 <strong>0</strong> 页';
        selectAllPagesCheckbox.checked = true;
        pageRangeInput.value = '';
        pageRangeInput.disabled = true;
    }
    
    // 获取PDF页数
    function getPdfPageCount(file) {
        const formData = new FormData();
        formData.append('pdf_file', file);
        
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/get_pdf_pages', true);
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        currentTotalPages = response.total_pages;
                        totalPagesElement.innerHTML = `当前PDF共 <strong>${currentTotalPages}</strong> 页`;
                    } else {
                        console.error('获取PDF页数失败:', response.message);
                    }
                } catch (error) {
                    console.error('解析获取PDF页数响应失败:', error);
                }
            } else {
                console.error('获取PDF页数请求失败:', xhr.status);
            }
        };
        
        xhr.onerror = function() {
            console.error('获取PDF页数网络错误');
        };
        
        xhr.send(formData);
    }
    
    // 文件选择事件处理
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            console.log('Selected file:', file.name);
            // 重置页码UI
            resetPageRangeUI();
            // 获取PDF页数
            getPdfPageCount(file);
        } else {
            // 重置页码UI
            resetPageRangeUI();
        }
    });
    
    // 全选/取消全选事件处理
    selectAllPagesCheckbox.addEventListener('change', function(e) {
        const isChecked = e.target.checked;
        pageRangeInput.disabled = isChecked;
        if (isChecked) {
            pageRangeInput.value = '';
        }
    });
    
    // 翻译服务选择事件处理
    const translatorSelect = document.getElementById('translator');
    translatorSelect.addEventListener('change', function(e) {
        const selectedService = e.target.value;
        console.log('Selected translator:', selectedService);
    });
    
    // 语言选择事件处理
    const sourceLangSelect = document.getElementById('source_lang');
    const targetLangSelect = document.getElementById('target_lang');
    
    sourceLangSelect.addEventListener('change', function(e) {
        console.log('Source language:', e.target.value);
    });
    
    targetLangSelect.addEventListener('change', function(e) {
        console.log('Target language:', e.target.value);
    });
    
    // 取消按钮事件处理
    cancelBtn.addEventListener('click', function() {
        if (confirm('确定要取消翻译吗？')) {
            cancelTranslation();
        }
    });
});
