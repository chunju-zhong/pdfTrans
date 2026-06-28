# -*- coding: utf-8 -*-
"""LLM API 错误分类工具

将 OpenAI 兼容 API 调用抛出的异常分类为用户友好的中文消息，
便于上层调用者将错误信息上报到 UI。
"""

from __future__ import annotations

from typing import Dict

from openai import (
    BadRequestError,
    AuthenticationError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)


def classify_llm_error(e: Exception) -> Dict[str, object]:
    """将 LLM API 异常分类为用户友好的中文消息。

    Args:
        e: 任意 Exception 实例，通常是 OpenAI 兼容 API 调用抛出的异常。

    Returns:
        包含以下字段的字典：
            - category (str): 错误类别，取值为 'auth'、'rate_limit'、
              'bad_request_max_tokens'、'bad_request'、'timeout'、'connection'、
              'server_error' 或 'unknown'。
            - user_message (str): 中文用户友好消息，含可操作建议。
            - is_retryable (bool): 是否建议重试。
            - original_message (str): 原始 str(e)，不截断。
    """
    original_message = str(e)

    if isinstance(e, AuthenticationError):
        return {
            'category': 'auth',
            'user_message': 'API 密钥无效或已过期，请检查 API Key 配置',
            'is_retryable': False,
            'original_message': original_message,
        }

    if isinstance(e, RateLimitError):
        return {
            'category': 'rate_limit',
            'user_message': '请求过于频繁或配额已用尽，请稍后重试或更换 API Key',
            'is_retryable': True,
            'original_message': original_message,
        }

    # BadRequestError 含 max_tokens 的检测必须在通用 BadRequestError 之前
    if isinstance(e, BadRequestError):
        if 'max_tokens' in original_message.lower():
            return {
                'category': 'bad_request_max_tokens',
                'user_message': (
                    'max_tokens 参数超限，请降低对应的环境变量配置'
                    '（如 OCR_LLM_MAX_TOKENS、GLOSSARY_MAX_TOKENS、LAYOUT_MAX_TOKENS）后重试'
                ),
                'is_retryable': False,
                'original_message': original_message,
            }
        return {
            'category': 'bad_request',
            'user_message': f'请求参数错误：{original_message[:200]}',
            'is_retryable': False,
            'original_message': original_message,
        }

    if isinstance(e, APITimeoutError):
        return {
            'category': 'timeout',
            'user_message': 'API 请求超时，请检查网络连接或重试',
            'is_retryable': True,
            'original_message': original_message,
        }

    if isinstance(e, APIConnectionError):
        return {
            'category': 'connection',
            'user_message': '无法连接到 API 服务，请检查网络或代理设置',
            'is_retryable': True,
            'original_message': original_message,
        }

    if isinstance(e, InternalServerError):
        return {
            'category': 'server_error',
            'user_message': 'API 服务端暂时不可用，请稍后重试',
            'is_retryable': True,
            'original_message': original_message,
        }

    return {
        'category': 'unknown',
        'user_message': f'API 调用失败：{original_message[:200]}',
        'is_retryable': False,
        'original_message': original_message,
    }
