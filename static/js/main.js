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
    
    let progressInterval = null;
    let translationTaskId = null;
    
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
                        showDownloadLink(progressData.result_file);
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
    function showDownloadLink(fileName) {
        // 更新下载链接
        downloadLink.href = `/download_file/${fileName}`;
        
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
    }
    
    // 文件选择事件处理
    const fileInput = document.getElementById('pdf_file');
    fileInput.addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name;
        if (fileName) {
            console.log('Selected file:', fileName);
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
