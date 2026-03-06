// 简化版的main.js文件，只包含术语表相关的功能
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成');
    
    // 术语提取相关元素
    const extractGlossaryBtn = document.getElementById('extract-glossary-btn');
    const glossaryProgressContainer = document.getElementById('glossary-progress-container');
    const glossaryProgressBar = document.getElementById('glossary-progress-bar');
    const glossaryProgressText = document.getElementById('glossary-progress-text');
    const glossaryCancelBtn = document.getElementById('glossary-cancel-btn');
    const glossaryTextarea = document.getElementById('glossary');
    
    console.log('术语提取按钮:', extractGlossaryBtn);
    console.log('术语表文本区域:', glossaryTextarea);
    
    let glossaryProgressInterval = null;
    let glossaryTaskId = null;
    
    // 提取术语按钮点击事件处理
    if (extractGlossaryBtn) {
        extractGlossaryBtn.addEventListener('click', function() {
            console.log('提取术语按钮被点击');
            alert('提取术语按钮被点击');
        });
    }
    
    // 加载术语文件按钮事件处理
    const loadGlossaryBtn = document.getElementById('load-glossary-btn');
    const glossaryFileInput = document.getElementById('glossary-file-input');
    
    console.log('加载术语文件按钮:', loadGlossaryBtn);
    console.log('术语文件输入:', glossaryFileInput);
    
    if (loadGlossaryBtn) {
        loadGlossaryBtn.addEventListener('click', function() {
            console.log('加载术语文件按钮被点击');
            glossaryFileInput.click();
        });
    }
    
    if (glossaryFileInput) {
        glossaryFileInput.addEventListener('change', function(e) {
            console.log('术语文件输入变化');
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
    }
    
    // 保存术语到文件按钮事件处理
    const saveGlossaryBtn = document.getElementById('save-glossary-btn');
    
    console.log('保存术语到文件按钮:', saveGlossaryBtn);
    
    if (saveGlossaryBtn) {
        saveGlossaryBtn.addEventListener('click', function() {
            console.log('保存术语到文件按钮被点击');
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
    }
    
    console.log('简化版脚本加载完成');
});