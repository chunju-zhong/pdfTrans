# 修复 PDF 上传 413 错误 Spec

## Why
用户上传较大 PDF 文件时，Flask 返回 HTTP 413 (Request Entity Too Large) 错误，且前端没有友好的错误提示。当前 `MAX_CONTENT_LENGTH` 限制为 50MB，且缺少 413 错误处理器和前端文件大小校验。

## What Changes
- 增大 `MAX_CONTENT_LENGTH` 上传限制至 500MB
- 在 Flask 中注册 413 错误处理器，返回 JSON 格式的友好错误信息
- 在前端添加文件大小校验，上传前提示用户文件过大
- 前端对 413 状态码做专门处理，显示友好提示

## Impact
- Affected code: `config.py`、`app.py`、`static/js/main.js`

## ADDED Requirements

### Requirement: 413 错误处理器
系统 SHALL 在 Flask 中注册 413 (RequestEntityTooLarge) 错误处理器，返回 JSON 格式响应 `{ "success": false, "message": "文件大小超过限制..." }`。

#### Scenario: 上传文件超过大小限制
- **WHEN** 用户上传的文件超过 `MAX_CONTENT_LENGTH` 限制
- **THEN** Flask 返回 HTTP 413 状态码，响应体为 JSON 格式 `{ "success": false, "message": "..." }`

### Requirement: 前端文件大小校验
系统 SHALL 在前端上传文件前校验文件大小，若超过限制则显示友好提示且不发送请求。

#### Scenario: 用户选择超大文件
- **WHEN** 用户在文件选择器中选择了一个超过 500MB 的 PDF 文件
- **THEN** 前端显示"文件大小超过限制"提示，不发送上传请求

### Requirement: 前端 413 状态码处理
系统 SHALL 在前端 XHR 请求中对 HTTP 413 状态码做专门处理，显示友好的错误提示。

#### Scenario: 服务端返回 413
- **WHEN** 前端收到 HTTP 413 响应
- **THEN** 显示"文件大小超过限制，请上传小于 500MB 的文件"提示

## MODIFIED Requirements

### Requirement: 上传文件大小限制
将 `MAX_CONTENT_LENGTH` 从 50MB 增大至 500MB，以支持更大的 PDF 文件上传。
