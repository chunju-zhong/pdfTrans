// 简单的测试脚本，用于验证按钮是否可以正常工作
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，开始测试按钮');
    
    // 测试加载术语文件按钮
    const loadGlossaryBtn = document.getElementById('load-glossary-btn');
    console.log('加载术语文件按钮:', loadGlossaryBtn);
    
    if (loadGlossaryBtn) {
        loadGlossaryBtn.addEventListener('click', function() {
            console.log('加载术语文件按钮被点击');
            alert('加载术语文件按钮被点击');
        });
    }
    
    // 测试保存术语到文件按钮
    const saveGlossaryBtn = document.getElementById('save-glossary-btn');
    console.log('保存术语到文件按钮:', saveGlossaryBtn);
    
    if (saveGlossaryBtn) {
        saveGlossaryBtn.addEventListener('click', function() {
            console.log('保存术语到文件按钮被点击');
            alert('保存术语到文件按钮被点击');
        });
    }
    
    // 测试提取术语按钮
    const extractGlossaryBtn = document.getElementById('extract-glossary-btn');
    console.log('提取术语按钮:', extractGlossaryBtn);
    
    if (extractGlossaryBtn) {
        extractGlossaryBtn.addEventListener('click', function() {
            console.log('提取术语按钮被点击');
            alert('提取术语按钮被点击');
        });
    }
    
    console.log('按钮测试脚本加载完成');
});