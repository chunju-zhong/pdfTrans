// 文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 获取表单元素
    const form = document.getElementById('translate-form');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const progressTime = document.getElementById('progress-time');
    const resultContainer = document.getElementById('result-container');
    const resultTime = document.getElementById('result-time');
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
    
    // 开始翻译按钮
    const startTranslationBtn = document.getElementById('start-translation-btn');
    
    // 表单提交事件处理
    form.addEventListener('submit', function(e) {
        // 阻止表单默认提交行为
        e.preventDefault();
        
        // 禁用开始翻译按钮
        startTranslationBtn.disabled = true;
        
        // 显示进度容器，隐藏结果容器
        progressContainer.style.display = 'block';
        resultContainer.style.display = 'none';
        
        // 显示取消翻译按钮
        cancelBtn.style.display = 'inline-block';
        
        // 初始化进度
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';
        progressText.textContent = '准备开始...';
        progressTime.textContent = '耗时: 00:00';
        
        // 准备表单数据
        const formData = new FormData(form);
        
        // 如果全选，则不传递page_range参数或传递空值
        if (selectAllPagesCheckbox.checked) {
            formData.delete('page_range');
        }
        
        // 如果按章节拆分选项被隐藏，则不传递chapter_split参数
        if (chapterSplitOption.style.display === 'none') {
            formData.delete('chapter_split');
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
                    updateProgress(progressData.progress, progressData.status, progressData.message, progressData.total_time);
                    
                    // 检查并显示警告
                    if (progressData.warnings && progressData.warnings.length > 0) {
                        showProgressWarnings(progressData.warnings);
                    } else {
                        hideProgressWarnings();
                    }
                    
                    // 如果翻译完成，停止轮询
                    if (progressData.status === 'completed') {
                        clearInterval(progressInterval);
                        // 隐藏进度区域的警告，因为会在结果区域显示
                        hideProgressWarnings();
                        // 显示下载链接
                        showDownloadLink(progressData.result_file, progressData.attachments || [], progressData.warnings || [], progressData.total_time);
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
    
    // 显示进度过程中的警告
    function showProgressWarnings(warnings) {
        const progressWarningsContainer = document.getElementById('progress-warnings-container');
        const progressWarningsList = document.getElementById('progress-warnings-list');
        
        if (warnings && warnings.length > 0) {
            progressWarningsContainer.style.display = 'block';
            progressWarningsList.innerHTML = '';
            
            warnings.forEach((warning, index) => {
                const warningItem = document.createElement('div');
                warningItem.className = 'warning-item';
                
                const warningMessage = document.createElement('div');
                warningMessage.className = 'warning-message';
                warningMessage.textContent = warning.message;
                warningItem.appendChild(warningMessage);
                
                if (warning.context) {
                    const warningContext = document.createElement('div');
                    warningContext.className = 'warning-context';
                    
                    if (warning.context.process) {
                        const processInfo = document.createElement('div');
                        processInfo.textContent = `处理过程: ${warning.context.process}`;
                        warningContext.appendChild(processInfo);
                    }
                    
                    if (warning.context.token_usage) {
                        const tokenInfo = document.createElement('div');
                        tokenInfo.textContent = `Token使用: ${warning.context.token_usage.total_tokens} (输入: ${warning.context.token_usage.prompt_tokens}, 输出: ${warning.context.token_usage.completion_tokens})`;
                        warningContext.appendChild(tokenInfo);
                    }
                    
                    if (warning.context.finish_reason) {
                        const reasonInfo = document.createElement('div');
                        reasonInfo.textContent = `结束原因: ${warning.context.finish_reason}`;
                        warningContext.appendChild(reasonInfo);
                    }
                    
                    warningItem.appendChild(warningContext);
                }
                
                progressWarningsList.appendChild(warningItem);
            });
        } else {
            progressWarningsContainer.style.display = 'none';
        }
    }
    
    // 隐藏进度过程中的警告
    function hideProgressWarnings() {
        const progressWarningsContainer = document.getElementById('progress-warnings-container');
        progressWarningsContainer.style.display = 'none';
    }
    
    // 更新进度显示
    function updateProgress(percentage, status, message, totalTime) {
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
        
        // 更新耗时显示
        if (totalTime !== undefined) {
            progressTime.textContent = `耗时: ${formatTime(totalTime)}`;
        }
        
        // 根据状态更新样式
        if (status === 'error') {
            progressBar.className = 'progress-bar error';
            // 重新启用开始翻译按钮
            startTranslationBtn.disabled = false;
            // 隐藏取消翻译按钮
            cancelBtn.style.display = 'none';
        } else if (status === 'completed') {
            progressBar.className = 'progress-bar completed';
        } else {
            progressBar.className = 'progress-bar processing';
        }
    }
    
    // 显示下载链接
    function showDownloadLink(fileName, attachments, warnings, totalTime) {
        const downloadLinksContainer = document.getElementById('download-links');
        const resultMessage = document.getElementById('result-message');
        const resultTime = document.getElementById('result-time');
        const warningsContainer = document.getElementById('warnings-container');
        const warningsList = document.getElementById('warnings-list');
        
        // 清空现有的下载链接
        downloadLinksContainer.innerHTML = '';
        
        // 显示警告
        if (warnings && warnings.length > 0) {
            warningsContainer.style.display = 'block';
            warningsList.innerHTML = '';
            
            warnings.forEach((warning, index) => {
                const warningItem = document.createElement('div');
                warningItem.className = 'warning-item';
                
                const warningMessage = document.createElement('div');
                warningMessage.className = 'warning-message';
                warningMessage.textContent = warning.message;
                warningItem.appendChild(warningMessage);
                
                if (warning.context) {
                    const warningContext = document.createElement('div');
                    warningContext.className = 'warning-context';
                    
                    if (warning.context.process) {
                        const processInfo = document.createElement('div');
                        processInfo.textContent = `处理过程: ${warning.context.process}`;
                        warningContext.appendChild(processInfo);
                    }
                    
                    if (warning.context.token_usage) {
                        const tokenInfo = document.createElement('div');
                        tokenInfo.textContent = `Token使用: ${warning.context.token_usage.total_tokens} (输入: ${warning.context.token_usage.prompt_tokens}, 输出: ${warning.context.token_usage.completion_tokens})`;
                        warningContext.appendChild(tokenInfo);
                    }
                    
                    if (warning.context.finish_reason) {
                        const reasonInfo = document.createElement('div');
                        reasonInfo.textContent = `结束原因: ${warning.context.finish_reason}`;
                        warningContext.appendChild(reasonInfo);
                    }
                    
                    warningItem.appendChild(warningContext);
                }
                
                warningsList.appendChild(warningItem);
            });
        } else {
            warningsContainer.style.display = 'none';
        }
        
        // 更新耗时显示
        if (totalTime !== undefined) {
            resultTime.textContent = `翻译总耗时：${formatTime(totalTime)}`;
        }
        
        // 添加主要文件下载链接
        const mainLink = document.createElement('a');
        mainLink.href = `/download_file/${fileName}`;
        mainLink.className = 'btn btn-success';
        let fileTypeText = '文件';
        if (fileName.endsWith('.pdf')) {
            fileTypeText = 'PDF';
        } else if (fileName.endsWith('.docx')) {
            fileTypeText = 'Word';
        } else if (fileName.endsWith('.md')) {
            fileTypeText = 'Markdown';
        } else if (fileName.endsWith('.zip')) {
            fileTypeText = 'Markdown(含图片)';
        }
        mainLink.textContent = `下载翻译后的${fileTypeText}文件`;
        downloadLinksContainer.appendChild(mainLink);
        
        // 添加附件下载链接
        if (attachments && attachments.length > 0) {
            resultMessage.textContent = '您的文件已翻译完成，点击下方链接下载：';
            
            attachments.forEach((attachment, index) => {
                const attachmentLink = document.createElement('a');
                attachmentLink.href = `/download_file/${attachment}`;
                attachmentLink.className = 'btn btn-success';
                attachmentLink.style.marginLeft = '10px';
                let attachmentTypeText = '文件';
                if (attachment.endsWith('.pdf')) {
                    attachmentTypeText = 'PDF';
                } else if (attachment.endsWith('.docx')) {
                    attachmentTypeText = 'Word';
                } else if (attachment.endsWith('.md')) {
                    attachmentTypeText = 'Markdown';
                } else if (attachment.endsWith('.zip')) {
                    attachmentTypeText = 'Markdown(含图片)';
                }
                attachmentLink.textContent = `下载翻译后的${attachmentTypeText}文件`;
                downloadLinksContainer.appendChild(attachmentLink);
            });
        } else {
            resultMessage.textContent = '您的文件已翻译完成，点击下方链接下载：';
        }
        
        // 重新启用开始翻译按钮
        startTranslationBtn.disabled = false;
        
        // 隐藏取消翻译按钮
        cancelBtn.style.display = 'none';
        
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
    
    // 格式化时间（秒）为分:秒格式
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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
        
        // 重新启用开始翻译按钮
        startTranslationBtn.disabled = false;
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
    
    // 语义块合并相关事件处理
    const semanticMergeCheckbox = document.getElementById('semantic_merge');
    const llmMergingOption = document.getElementById('llm-merging-option');
    
    // 初始状态检查
    function updateLlmMergingOptionVisibility() {
        if (semanticMergeCheckbox.checked) {
            llmMergingOption.style.display = 'block';
        } else {
            llmMergingOption.style.display = 'none';
        }
    }
    
    // 初始调用，设置正确的显示状态
    updateLlmMergingOptionVisibility();
    
    // 语义块合并开关变化事件处理
    semanticMergeCheckbox.addEventListener('change', function(e) {
        updateLlmMergingOptionVisibility();
    });
    
    // 输出格式相关元素
    const outputFormatSelect = document.getElementById('output_format');
    const chapterSplitOption = document.getElementById('chapter-split-option'); // 按章节翻译Markdown选项的父容器
    
    // 更新按章节翻译选项的可见性
    function updateChapterSplitOptionVisibility() {
        const selectedFormat = outputFormatSelect.value;
        // 检查输出格式是否包含Markdown
        const includesMarkdown = selectedFormat === 'md' || selectedFormat === 'all';
        
        if (includesMarkdown) {
            chapterSplitOption.style.display = 'block';
        } else {
            chapterSplitOption.style.display = 'none';
            // 当选项被隐藏时，取消勾选复选框
            document.getElementById('chapter_split').checked = false;
        }
    }
    
    // 初始调用，设置正确的显示状态
    updateChapterSplitOptionVisibility();
    
    // 输出格式变化事件处理
    outputFormatSelect.addEventListener('change', function(e) {
        updateChapterSplitOptionVisibility();
    });
    
    // 取消按钮事件处理
    cancelBtn.addEventListener('click', function() {
        if (confirm('确定要取消翻译吗？')) {
            cancelTranslation();
        }
    });
    
    // 术语提取相关元素
    const extractGlossaryBtn = document.getElementById('extract-glossary-btn');
    const glossaryProgressContainer = document.getElementById('glossary-progress-container');
    const glossaryProgressBar = document.getElementById('glossary-progress-bar');
    const glossaryProgressText = document.getElementById('glossary-progress-text');
    const glossaryCancelBtn = document.getElementById('glossary-cancel-btn');
    const glossaryTextarea = document.getElementById('glossary');
    
    let glossaryProgressInterval = null;
    let glossaryTaskId = null;
    
    // 提取术语按钮点击事件处理
    extractGlossaryBtn.addEventListener('click', function() {
        const file = fileInput.files[0];
        if (!file) {
            alert('请先选择PDF文件');
            return;
        }
        
        // 显示进度容器
        glossaryProgressContainer.style.display = 'block';
        
        // 初始化进度
        glossaryProgressBar.style.width = '0%';
        glossaryProgressBar.textContent = '0%';
        glossaryProgressText.textContent = '正在提取术语...';
        
        // 准备表单数据
        const formData = new FormData();
        formData.append('pdf_file', file);
        formData.append('source_lang', sourceLangSelect.value);
        formData.append('target_lang', targetLangSelect.value);
        formData.append('translator', translatorSelect.value);
        formData.append('doc_type', document.getElementById('doc_type').value);
        
        // 添加页码范围
        if (!selectAllPagesCheckbox.checked && pageRangeInput.value) {
            formData.append('page_range', pageRangeInput.value);
        }
        
        // 异步提取术语
        extractGlossary(formData);
    });
    
    // 异步提取术语函数
    function extractGlossary(formData) {
        const xhr = new XMLHttpRequest();
        
        // 设置请求
        xhr.open('POST', '/extract_glossary', true);
        
        // 处理响应
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        glossaryTaskId = response.task_id;
                        // 开始轮询进度
                        startGlossaryProgressPolling();
                    } else {
                        updateGlossaryProgress(0, 'error', response.message || '提取术语请求失败');
                    }
                } catch (error) {
                    updateGlossaryProgress(0, 'error', '解析响应失败: ' + error.message);
                }
            } else {
                updateGlossaryProgress(0, 'error', '服务器错误: ' + xhr.status);
            }
        };
        
        // 处理网络错误
        xhr.onerror = function() {
            updateGlossaryProgress(0, 'error', '网络连接错误');
        };
        
        // 发送请求
        xhr.send(formData);
    }
    
    // 开始术语提取进度轮询
    function startGlossaryProgressPolling() {
        // 清除可能存在的旧轮询
        if (glossaryProgressInterval) {
            clearInterval(glossaryProgressInterval);
        }
        
        // 每1秒查询一次进度
        glossaryProgressInterval = setInterval(function() {
            getGlossaryProgress();
        }, 1000);
        
        // 立即查询一次
        getGlossaryProgress();
    }
    
    // 查询术语提取进度
    function getGlossaryProgress() {
        if (!glossaryTaskId) return;
        
        const xhr = new XMLHttpRequest();
        xhr.open('GET', `/glossary_progress/${glossaryTaskId}`, true);
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const progressData = JSON.parse(xhr.responseText);
                    updateGlossaryProgress(progressData.progress, progressData.status, progressData.message);
                    
                    // 如果提取完成，停止轮询
                    if (progressData.status === 'completed') {
                        clearInterval(glossaryProgressInterval);
                        // 回填术语表
                        if (progressData.glossary) {
                            glossaryTextarea.value = progressData.glossary;
                        }
                        // 进度条不自动消失，让用户看到结果
                    } else if (progressData.status === 'error') {
                        clearInterval(glossaryProgressInterval);
                        // 进度条不自动消失，让用户看到错误信息
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
    
    // 更新术语提取进度显示
    function updateGlossaryProgress(percentage, status, message) {
        // 确保百分比在0-100之间
        const safePercentage = Math.max(0, Math.min(100, percentage));
        
        glossaryProgressBar.style.width = safePercentage + '%';
        glossaryProgressBar.textContent = safePercentage + '%';
        
        // 根据状态更新文本
        let statusText = message;
        if (!statusText) {
            switch (status) {
                case 'processing':
                    statusText = '正在提取术语...';
                    break;
                case 'completed':
                    statusText = '术语提取完成！';
                    break;
                case 'error':
                    statusText = '提取失败！';
                    break;
                default:
                    statusText = '准备开始...';
            }
        }
        
        glossaryProgressText.textContent = statusText;
        
        // 根据状态更新样式
        if (status === 'error') {
            glossaryProgressBar.className = 'progress-bar error';
        } else if (status === 'completed') {
            glossaryProgressBar.className = 'progress-bar completed';
        } else {
            glossaryProgressBar.className = 'progress-bar processing';
        }
        
        // 根据状态显示或隐藏取消按钮
        if (status === 'completed' || status === 'error') {
            glossaryCancelBtn.style.display = 'none';
        } else {
            glossaryCancelBtn.style.display = 'inline-block';
        }
    }
    
    // 取消术语提取任务
    function cancelGlossaryExtraction() {
        if (!glossaryTaskId) return;
        
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/glossary_cancel/${glossaryTaskId}`, true);
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        updateGlossaryProgress(0, 'error', '术语提取已取消');
                    } else {
                        updateGlossaryProgress(0, 'error', '取消失败: ' + response.message);
                    }
                } catch (error) {
                    updateGlossaryProgress(0, 'error', '取消失败: 解析响应错误');
                }
            } else {
                updateGlossaryProgress(0, 'error', '取消失败: 服务器错误');
            }
            
            // 清理资源
            cleanupGlossaryTask();
        };
        
        xhr.onerror = function() {
            updateGlossaryProgress(0, 'error', '取消失败: 网络错误');
            cleanupGlossaryTask();
        };
        
        xhr.send();
    }
    
    // 清理术语提取任务资源
    function cleanupGlossaryTask() {
        // 清除进度轮询
        if (glossaryProgressInterval) {
            clearInterval(glossaryProgressInterval);
            glossaryProgressInterval = null;
        }
        
        // 重置任务ID
        glossaryTaskId = null;
        
        // 隐藏进度容器
        glossaryProgressContainer.style.display = 'none';
    }
    
    // 术语提取取消按钮事件处理
    glossaryCancelBtn.addEventListener('click', function() {
        if (confirm('确定要取消术语提取吗？')) {
            cancelGlossaryExtraction();
        }
    });
    
    // 加载术语文件按钮事件处理
    const loadGlossaryBtn = document.getElementById('load-glossary-btn');
    const glossaryFileInput = document.getElementById('glossary-file-input');
    
    loadGlossaryBtn.addEventListener('click', function() {
        glossaryFileInput.click();
    });
    
    glossaryFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const content = e.target.result;
                    glossaryTextarea.value = content;
                    alert('术语表加载成功！');
                } catch (error) {
                    alert('加载文件失败：' + error.message);
                }
            };
            reader.onerror = function() {
                alert('读取文件失败，请重试');
            };
            reader.readAsText(file);
        }
        // 重置文件输入，以便可以重复选择同一个文件
        e.target.value = '';
    });
    
    // 保存术语到文件按钮事件处理
    const saveGlossaryBtn = document.getElementById('save-glossary-btn');
    
    saveGlossaryBtn.addEventListener('click', function() {
        const content = glossaryTextarea.value;
        if (!content.trim()) {
            alert('术语表为空，没有内容可保存');
            return;
        }
        
        // 创建Blob对象
        const blob = new Blob([content], { type: 'text/plain' });
        
        // 创建下载链接
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'glossary.txt';
        a.click();
        
        // 释放URL对象
        setTimeout(function() {
            URL.revokeObjectURL(url);
        }, 100);
        
        alert('术语表保存成功！');
    });
});