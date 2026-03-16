# 进度系统重构规范

## 概述
- **Summary**: 将进度系统从硬编码数值重构为可配置的阶段系统，消除代码中的硬编码进度值（10, 20, 45, 50等）
- **Purpose**: 解决当前进度系统中进度值硬编码、维护困难、语义不清晰的问题
- **Target Users**: PDF翻译工具的开发者和维护者

## 背景与上下文

### 当前问题
1. **硬编码数值过多**: 代码中直接使用 `update_progress(30, ...)`, `update_progress(45, ...)` 等硬编码值
2. **进度阶段不明确**: 无法清晰看出有哪些进度阶段，每个阶段的范围是什么
3. **维护困难**: 调整某个阶段的进度范围需要修改多处代码
4. **语义不清晰**: 进度值30表示什么？不直观

### 当前进度值分布
```
翻译任务:
0-10:   初始化阶段 (0, 5, 10)
10-35:  文本提取阶段 (20, 30)
35-40:  语义合并阶段 (35, 45, 50)
40-80:  翻译阶段 (40, 45, 50)
75-80:  表格翻译阶段 (75, 80)
80-100: 输出生成阶段 (80, 90, 95, 100)

术语提取任务 (glossary_service.py):
0-5:   开始阶段 (5)
30:    PDF文本提取完成 (30)
30-100: 术语提取循环 (progress)
100:   术语提取完成 (100)
```

### 调用点统计
- translation_service.py: 27处进度更新调用
- app.py: 4处进度更新调用
- glossary_service.py: 4处进度更新调用

## 设计方案

### 核心概念

引入**进度阶段(Phase)**的概念：

- **Phase（阶段）**: 一个独立的工作步骤，如"初始化"、"提取文本"、"翻译"、"生成输出"等
- **PhaseRange（阶段范围）**: 每个阶段在整体进度中的百分比范围
- **PhaseProgress（阶段进度）**: 某阶段内部的相对进度（0-100%）

### 数据结构设计

```python
# 翻译任务的阶段配置
PHASE_CONFIG = {
    'init': {
        'name': '初始化',
        'start': 0,
        'end': 10,
    },
    'extraction': {
        'name': '文本提取',
        'start': 10,
        'end': 35,
    },
    'semantic_merge': {
        'name': '语义合并',
        'start': 35,
        'end': 40,
    },
    'translation': {
        'name': '翻译',
        'start': 40,
        'end': 80,
    },
    'table_translation': {
        'name': '表格翻译',
        'start': 80,
        'end': 90,
    },
    'generation': {
        'name': '生成输出',
        'start': 90,
        'end': 100,
    }
}

# 术语提取任务的阶段配置
GLOSSARY_PHASE_CONFIG = {
    'init': {
        'name': '开始提取',
        'start': 0,
        'end': 5,
    },
    'pdf_extraction': {
        'name': 'PDF文本提取',
        'start': 5,
        'end': 30,
    },
    'term_extraction': {
        'name': '术语提取',
        'start': 30,
        'end': 100,
    }
}
```

### Task类扩展

新增属性和方法，支持不同任务类型的阶段配置：

```python
class Task:
    # 新增：当前阶段
    current_phase: str = 'init'
    
    # 任务类型：'translation' 或 'glossary'
    task_type: str = 'translation'
    
    # 阶段配置（根据任务类型选择）
    phase_config = PHASE_CONFIG  # 默认翻译任务
    
    def set_task_type(self, task_type: str):
        """设置任务类型并切换对应的阶段配置
        
        Args:
            task_type: 'translation' 或 'glossary'
        """
        self.task_type = task_type
        if task_type == 'glossary':
            self.phase_config = GLOSSARY_PHASE_CONFIG
        else:
            self.phase_config = PHASE_CONFIG
    
    # 方法：更新阶段进度
    def update_phase_progress(self, phase: str, phase_percent: int, message: str = None):
        """根据阶段和阶段内百分比更新整体进度
        
        Args:
            phase: 阶段名称（如'translation'）
            phase_percent: 该阶段内的进度（0-100）
            message: 可选的状态消息
        """
        phase_range = self.phase_config.get(phase)
        if not phase_range:
            return False
            
        start = phase_range['start']
        end = phase_range['end']
        overall_progress = start + (end - start) * phase_percent // 100
        
        return self.update_progress(overall_progress, message)
```

### 阶段划分

#### 翻译任务阶段

| 阶段ID | 阶段名称 | 进度范围 | 说明 |
|--------|----------|----------|------|
| init | 初始化 | 0-10% | 任务创建、文件检查、翻译器创建 |
| extraction | 文本提取 | 10-35% | PDF文本提取 |
| semantic_merge | 语义合并 | 35-40% | 语义块合并（可选） |
| translation | 翻译 | 40-80% | 文本翻译（主要耗时阶段） |
| table_translation | 表格翻译 | 80-90% | 表格单元格翻译 |
| generation | 生成输出 | 90-100% | PDF/DOCX/MD生成、文件清理 |

#### 术语提取任务阶段

| 阶段ID | 阶段名称 | 进度范围 | 说明 |
|--------|----------|----------|------|
| init | 开始提取 | 0-5% | 开始提取操作 |
| pdf_extraction | PDF文本提取 | 5-30% | 从PDF中提取文本 |
| term_extraction | 术语提取 | 30-100% | 从文本中提取术语 |

## 功能需求

### FR-1: 阶段配置系统
系统应提供可配置的阶段进度配置。

- **Given**: 开发者需要调整某阶段的进度范围
- **When**: 修改 PHASE_CONFIG 配置
- **Then**: 所有使用该阶段的进度更新自动应用新范围
- **Verification**: 修改配置后，进度计算结果正确

### FR-2: 语义化进度更新方法
系统应提供语义化的进度更新方法。

- **Given**: 开发者需要在翻译阶段更新进度
- **When**: 调用 task.update_phase_progress('translation', 50, '翻译进行中...')
- **Then**: 整体进度被计算为 40 + (80-40) * 50 / 100 = 60
- **Verification**: 方法返回True，整体进度正确

### FR-3: 向后兼容
原有 update_progress() 方法应保持不变。

- **Given**: 现有代码使用硬编码进度值
- **When**: 继续使用 task.update_progress(30, 'message')
- **Then**: 功能正常，不受影响
- **Verification**: 原有测试通过

### FR-4: 术语提取任务支持（glossary_service.py）
系统应支持术语提取任务的阶段配置。

- **Given**: 术语提取任务使用进度更新
- **When**: 调用 task.set_task_type('glossary') 后使用 update_phase_progress()
- **Then**: 使用 GLOSSARY_PHASE_CONFIG 配置
- **Verification**: 术语提取进度正确计算

## 实施影响

### 受影响的文件
1. models/phase_config.py - 新建阶段配置模块
2. models/task.py - 添加阶段配置、task_type属性和方法
3. services/translation_service.py - 更新27处进度调用
4. services/glossary_service.py - 更新4处进度调用
5. app.py - 更新术语提取和翻译任务的进度调用
6. tests/test_phase_progress.py - 新增测试

### 非功能性需求
- **NFR-1**: 性能开销最小化，进度计算不应增加明显延迟
- **NFR-2**: 进度计算准确性，确保阶段百分比正确映射到整体进度
- **NFR-3**: 配置验证，阶段配置应进行有效性检查
- **NFR-4**: 多任务类型支持，支持翻译任务和术语提取任务使用不同的阶段配置

## 验收标准

### AC-1: 阶段配置加载
- **Given**: Task类实例化
- **When**: 访问 task.phase_config
- **Then**: 返回完整的 PHASE_CONFIG 配置，包含6个阶段

### AC-2: 进度计算正确性
- **Given**: 阶段配置 init: {start: 0, end: 10}
- **When**: 调用 update_phase_progress('init', 50, 'message')
- **Then**: progress 被设置为 5 (0 + (10-0) * 50 / 100)

### AC-3: 翻译阶段进度范围
- **Given**: 阶段配置 translation: {start: 40, end: 80}
- **When**: phase_percent = 0 到 100
- **Then**: overall_progress 范围为 40 到 80

### AC-4: 所有硬编码调用已更新
- **Given**: translation_service.py、app.py 和 glossary_service.py
- **When**: 搜索 update_progress(
- **Then**: 所有业务代码调用都使用 update_phase_progress() 方法

### AC-5: 术语提取任务阶段配置
- **Given**: Task类实例化并设置 task_type='glossary'
- **When**: 访问 task.phase_config
- **Then**: 返回 GLOSSARY_PHASE_CONFIG 配置，包含3个阶段

### AC-6: 向后兼容性
- **Given**: 原有测试用例
- **When**: 运行测试
- **Then**: 所有测试通过
