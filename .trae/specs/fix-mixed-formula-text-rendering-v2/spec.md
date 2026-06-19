# 修复公式渲染两个遗留问题 Spec

## Why
测试发现两个公式渲染问题：

**问题1：`$$...$$` display math 混合文本渲染失败**
文本 `$$\mathrm{k}_{\mathrm{T}} = 1,07(\mathrm{T}^{- 10})$$ (when $$\mathrm{T} = 5 - 10^{\circ}\mathrm{C}$$ )` 被检测为混合公式文本，但 `_render_mixed_text_formula_image` 渲染失败返回 None。原因是 matplotlib 的 mathtext 无法在单次 `ax.text()` 调用中处理多个 display math（`$$...$$`）块与英文文本的混合。日志显示"混合公式文本渲染失败 → 降级为纯文本"。

**问题2：混合公式文本中文显示为方块（□）**
图片中"高负荷率："等中文显示为 □□□□□，原因是 matplotlib 默认字体不支持 CJK 字符，需要配置中文字体。

## What Changes
- **将 `$$...$$` 转换为 `$...$`**：在 `_preprocess_latex_for_mathtext` 或 `_render_mixed_text_formula_image` 中，将 display math 定界符转换为 inline math，因为 mathtext 对 inline math 的支持更好
- **配置 CJK 字体**：在所有使用 matplotlib 渲染包含 CJK 文本的方法中，设置 `plt.rcParams['font.sans-serif']` 包含系统中文字体

## Impact
- Affected code: `modules/pdf_generator.py`
- Affected specs: fix-mixed-formula-text-rendering

## ADDED Requirements

### Requirement: 混合公式渲染时 $$...$$ 转为 $...$

`_render_mixed_text_formula_image` 在预处理后、传入 mathtext 前，将 `$$...$$` 转换为 `$...$`。

理由：matplotlib mathtext 的 display math（`$$`）模式不支持与普通文本混排，但 inline math（`$`）支持。

#### Scenario: 多个 display math 块 + 英文文本
- **WHEN** 文本为 `$$k_{T} = 1,07(T^{- 10})$$ (when $$T = 5 - 10°C$$ )`
- **THEN** 预处理后转为 `$k_{T} = 1,07(T^{- 10})$ (when $T = 5 - 10°C$ )`，mathtext 成功渲染

### Requirement: matplotlib 配置 CJK 字体

所有通过 matplotlib 渲染可能包含 CJK 文本的方法（`_render_mixed_text_formula_image`、`_try_mathtext_render`），在创建 figure 前设置：

```python
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'STHeiti', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

#### Scenario: 中文+公式混合文本渲染
- **WHEN** 文本为 "高负荷率：$15 - 30gBOD_5 / m^2 d$"
- **THEN** "高负荷率："显示为中文字符而非方块 □

## MODIFIED Requirements

### Requirement: _preprocess_latex_for_mathtext
增加 `$$...$$` → `$...$` 转换（在已有的 `\(...\)` → `$...$` 之后）。
