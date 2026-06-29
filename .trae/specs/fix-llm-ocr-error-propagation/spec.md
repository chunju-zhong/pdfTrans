# LLM OCR API 错误信息向用户透传 Spec

## Why

当前 `modules/ocr/llm_extractor.py` 的 `_extract_page` 方法中，通用的 `except Exception` 只做日志记录（`logger.error`）就返回 `(None, None)`，具体的错误信息（如 401 认证失败、模型不可用等）被丢弃，导致：
1. 上层 `page_error` 回调收不到具体错误原因
2. UI 无法向用户展示正确的错误提示（如"API密钥无效"）
3. 用户看到的是模糊的"处理失败"而非具体的操作指引

## What Changes

- `modules/ocr/llm_extractor.py` **`_extract_page` 方法**: 通用 `except Exception` 中返回具体的错误信息字符串，替代 `None`
- `modules/ocr/llm_extractor.py` **调用侧 (211行附近)**: 确保 `extract_error` 不为空时通过 `page_error` 回调传播给 UI
- **不涉及** 配置、CLI、前端界面的修改

## Impact

- Affected specs: LLM OCR 错误处理
- Affected code:
  - `modules/ocr/llm_extractor.py` — `_extract_page()` 返回具体错误信息

## ADDED Requirements

### Requirement: LLM OCR API 错误信息向上传透

系统 SHALL 将 LLM OCR 调用中的 API 错误信息（如认证失败、模型不可用等）通过错误回调向上层传递，以便 UI 展示给用户。

#### Scenario: API 认证失败（401）
- **WHEN** LLM OCR 调用百度千帆/Aiping/硅基流动 API 时返回 401 认证错误
- **THEN** `_extract_page` SHALL 返回具体的错误信息字符串
- **AND** 上层 error 回调 SHALL 收到包含"API认证失败"或具体错误描述的字符串
- **AND** 用户 SHALL 在 UI 上看到包含错误原因的提示

#### Scenario: 其他 API 异常
- **WHEN** LLM OCR 调用 API 时发生其他非超时异常（如 429 限流、500 服务端错误等）
- **THEN** `_extract_page` SHALL 返回包含错误类型或错误描述的字符串
- **AND** 错误信息 SHALL 通过回调传到 UI

#### Scenario: 超时错误（已有逻辑，不受影响）
- **WHEN** LLM OCR 调用超时
- **THEN** 保持现有的超时特定错误提示不变

## MODIFIED Requirements

### Requirement: `_extract_page` 异常处理

**原行为**: 通用 `except Exception` 仅记录日志，返回 `(None, None)`。

**新行为**:
```python
except Exception as e:
    logger.error(f"LLM OCR提取第{page_num}页失败: {e}", exc_info=True)
    error_msg = f"LLM OCR API 请求失败: {str(e)}"
    return (None, error_msg)
```
