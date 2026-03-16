# 添加 clean 阶段配置计划

## 目标
在 PHASE_CONFIG 中增加一个 `clean` 阶段，用于处理临时文件清理工作。

## 当前状态
- generation 阶段范围: 90-100%

## 修改方案
将 generation 阶段拆分为两个阶段：
- generation (90-95%): 生成输出文件
- clean (95-100%): 清理临时文件

## 实施步骤

### 1. 修改 models/phase_config.py
- 将 generation 阶段的 end 从 100 改为 95
- 添加 clean 阶段: start=95, end=100

### 2. 更新 services/translation_service.py
- 将清理临时文件的进度调用从 `generation` 阶段改为 `clean` 阶段

### 3. 验证测试
- 运行测试确保功能正常
