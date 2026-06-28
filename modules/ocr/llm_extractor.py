# -*- coding: utf-8 -*-
from __future__ import annotations

"""LLM视觉模型OCR提取器

通过OpenAI兼容API调用视觉模型（DeepSeek-OCR、Qwen3-VL等），
将PDF页面图像发送给模型，获取文本输出，映射为TextBlock/PdfTable/PdfImage。

支持两种响应格式：
1. JSON格式（通用VLM模型）
2. Markdown/<|ref|>标签格式（DeepSeek-OCR原生格式）

响应解析逻辑委托给 LlmOcrResponseParser，
表格解析逻辑委托给 LlmTableParser。
"""

import os
import io
import logging
import base64
import fitz
import numpy as np
from PIL import Image
from openai import OpenAI, APITimeoutError

from models.extraction import PdfPage, PdfTable, PdfImage, PdfExtraction
from modules.ocr.base import OcrExtractor
from modules.ocr.llm_response_parser import LlmOcrResponseParser
from modules.ocr.llm_table_parser import LlmTableParser
from config import config
from modules.llm_error_handler import classify_llm_error

logger = logging.getLogger(__name__)


# DeepSeek-OCR 原生 prompt 格式
DEEPSEEK_OCR_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."

# 通用VLM模型的JSON prompt（兼容Qwen3-VL等）
VLM_JSON_SYSTEM_PROMPT = """你是一个专业的文档OCR引擎。分析提供的PDF页面图像，提取所有文字内容、表格和图表信息。

输出严格的JSON格式，结构如下：
{
  "text_blocks": [
    {
      "id": 0,
      "text": "提取的文字内容",
      "bbox": [x1, y1, x2, y2],
      "type": "text|title|section_title|header|footer|footnote",
      "is_body": true
    }
  ],
  "tables": [
    {
      "id": 0,
      "bbox": [x1, y1, x2, y2],
      "html": "<table><tr><td>单元格</td></tr></table>"
    }
  ],
  "images": [
    {
      "id": 0,
      "bbox": [x1, y1, x2, y2],
      "description": "图表简要描述"
    }
  ]
}

规则：
1. bbox坐标为图像像素坐标 [左上x, 左上y, 右下x, 右下y]
2. 按阅读顺序（从上到下、从左到右）排列text_blocks
3. 保持原文内容，不要翻译或修改
4. type为title/section_title时is_body为false
5. type为header/footer/footnote/page_number时is_body为false
6. 如果某类内容为空，对应数组为空列表
7. 仅输出JSON，不要输出其他内容"""



def _is_deepseek_ocr_model(model_name):
    """判断模型是否为DeepSeek-OCR"""
    model_lower = model_name.lower()
    return 'deepseek-ocr' in model_lower


class LlmOcrExtractor(OcrExtractor):
    """基于LLM视觉模型的OCR提取器

    通过OpenAI兼容API调用视觉模型，将PDF页面图像发送给模型，
    获取结构化JSON输出（文本块+坐标+表格+图表），
    映射为现有TextBlock/PdfTable/PdfImage模型。

    响应解析委托给 LlmOcrResponseParser，
    表格解析委托给 LlmTableParser。
    """

    def __init__(self, translator_type='aiping', lang='ch', source_lang=None, **kwargs):
        """初始化LLM OCR提取器

        Args:
            translator_type (str): 翻译引擎类型，可选 'aiping' 或 'silicon_flow'
            lang (str): OCR识别语言
            source_lang (str | None): 源语言
            **kwargs: 额外参数，支持 'model' 用于指定OCR模型名称
        """
        self.translator_type = translator_type
        self.lang = lang
        self.source_lang = source_lang
        self._model_override = kwargs.get('model')
        self._client = None
        self._model = None
        self._parser = None  # lazy init

    @property
    def parser(self):
        """延迟初始化响应解析器"""
        if self._parser is None:
            self._parser = LlmOcrResponseParser(
                self.translator_type, self.lang, source_lang=self.source_lang
            )
        return self._parser

    @property
    def client(self):
        """延迟初始化OpenAI客户端"""
        if self._client is None:
            if self.translator_type == 'aiping':
                self._client = OpenAI(
                    base_url=config.AIPING_API_URL,
                    api_key=config.AIPING_API_KEY,
                    timeout=config.OCR_LLM_TIMEOUT,
                    max_retries=0
                )
                self._model = self._model_override or config.AIPING_OCR_LLM_MODEL
            elif self.translator_type == 'silicon_flow':
                self._client = OpenAI(
                    base_url=config.SILICON_FLOW_API_URL,
                    api_key=config.SILICON_FLOW_API_KEY,
                    timeout=config.OCR_LLM_TIMEOUT,
                    max_retries=0
                )
                self._model = self._model_override or config.SILICON_FLOW_OCR_LLM_MODEL
            elif self.translator_type == 'qianfan':
                self._client = OpenAI(
                    base_url=config.QIANFAN_API_URL,
                    api_key=config.QIANFAN_API_KEY,
                    timeout=config.OCR_LLM_TIMEOUT,
                    max_retries=0
                )
                self._model = self._model_override or config.QIANFAN_OCR_LLM_MODEL
            else:
                raise ValueError(f"不支持的翻译引擎类型: {self.translator_type}")
        return self._client

    @property
    def model(self):
        """获取模型名称（触发客户端初始化）"""
        if self._model is None:
            _ = self.client  # 触发初始化
        return self._model

    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None, progress_callback=None):
        """从PDF中提取内容

        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 页码列表（从1开始），None表示全部
            temp_images_dir (str | None): 临时图像目录
            progress_callback (callable | None): 进度回调函数，签名 (msg_type, payload)

        Returns:
            PdfExtraction: 提取结果
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        if temp_images_dir is None:
            temp_images_dir = os.path.join(os.getcwd(), 'temp_images')
        os.makedirs(temp_images_dir, exist_ok=True)

        pdf_pages = []
        pdf_tables = []
        pdf_images = []

        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            target_pages = pages if pages else list(range(1, total_pages + 1))
            n_target = len(target_pages)

            # 发送步骤开始回调
            if progress_callback:
                progress_callback('step_start', {
                    'step': 1,
                    'step_name': 'LLM OCR提取',
                    'total_pages': n_target,
                    'pages_done': 0,
                })

            pages_done = 0
            for page_num in target_pages:
                page_idx = page_num - 1
                if page_idx >= total_pages:
                    continue
                page = doc[page_idx]

                # 渲染页面为图像
                pix = page.get_pixmap(dpi=config.OCR_LLM_DPI)
                img_path = os.path.join(temp_images_dir, f"llm_ocr_page_{page_num}.png")
                pix.save(img_path)

                # 获取页面尺寸信息（用于像素坐标转PDF点坐标）
                page_info = {
                    'page_width_pts': page.rect.width,
                    'page_height_pts': page.rect.height,
                    'img_width_px': pix.width,
                    'img_height_px': pix.height,
                }
                logger.info(f"LLM OCR第{page_num}页尺寸: 页面={page_info['page_width_pts']:.1f}x{page_info['page_height_pts']:.1f}pt, 图像={page_info['img_width_px']}x{page_info['img_height_px']}px")

                # 编码为base64
                with open(img_path, 'rb') as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')

                logger.info(f"LLM OCR提取第{page_num}/{total_pages}页")

                # 调用LLM视觉模型
                result_tuple = self._extract_page(img_base64, page_num, page_info, page=page, temp_images_dir=temp_images_dir)
                result, extract_error = result_tuple if result_tuple else (None, None)

                if result:
                    text_blocks, page_tables, page_images = result
                    pdf_pages.append(PdfPage(
                        page_num=page_num,
                        text_blocks=text_blocks
                    ))
                    pdf_tables.extend(page_tables)
                    pdf_images.extend(page_images)
                else:
                    # 提取失败，添加空页面
                    pdf_pages.append(PdfPage(
                        page_num=page_num,
                        text_blocks=[]
                    ))
                    if extract_error:
                        logger.error(f"第{page_num}页LLM OCR提取错误: {extract_error}")
                        # 通过回调传播具体错误
                        if progress_callback:
                            progress_callback('page_error', {
                                'page_num': page_num,
                                'error': extract_error,
                            })

                # 更新进度
                pages_done += 1
                if progress_callback:
                    progress_callback('step_progress', {
                        'step': 1,
                        'step_name': 'LLM OCR提取',
                        'total_pages': n_target,
                        'pages_done': pages_done,
                    })

            # 发送步骤完成回调
            if progress_callback:
                progress_callback('step_complete', {
                    'step': 1,
                    'step_name': 'LLM OCR提取',
                    'total_pages': n_target,
                    'pages_done': pages_done,
                })

        return PdfExtraction(
            total_pages=total_pages,
            pages=pdf_pages,
            tables=pdf_tables,
            images=pdf_images
        )

    @staticmethod
    def _is_blank_image(img_base64: str, threshold: float = 5.0) -> bool:
        """检测图像是否为空白页（纯色/接近纯色）

        通过计算灰度图像素标准差判断。纯白页标准差 ≈ 0，
        有文字页一般 > 20-30。阈值 5.0 只捕获真正空白页。

        Args:
            img_base64: base64 编码的图像数据
            threshold: 像素标准差阈值，低于此值判定为空白

        Returns:
            bool: 是否为空白页；检测失败时保守返回 False
        """
        try:
            img_data = base64.b64decode(img_base64)
            img = Image.open(io.BytesIO(img_data)).convert('L')
            arr = np.array(img, dtype=np.float32)
            std = arr.std()
            return bool(std < threshold)
        except Exception:
            return False

    def _build_lang_hint(self) -> str:
        """根据 source_lang 从规则注册表加载 OCR 语言专项提示

        Returns:
            str: 拼接好的语言专项提示文本，末尾带 "\n\n"；
                 无匹配规则或加载失败时返回空字符串
        """
        try:
            from prompts import rule_registry
            ocr_rules = rule_registry.get_rules("ocr", self.source_lang, "*")
            if ocr_rules:
                hint_parts = []
                for r in ocr_rules:
                    hint_parts.append(r.content.strip())
                return "\n".join(hint_parts) + "\n\n" if hint_parts else ''
        except ImportError:
            pass
        return ''

    def _extract_page(self, img_base64, page_num, page_info=None, page=None, temp_images_dir=None):
        """调用LLM视觉模型提取单页内容

        Args:
            img_base64 (str): 页面图像的base64编码
            page_num (int): 页码
            page_info (dict | None): 页面尺寸信息，用于坐标转换
            page (fitz.Page | None): fitz页面对象，用于图像裁剪
            temp_images_dir (str | None): 临时图像保存目录

        Returns:
            tuple | None: (text_blocks, tables, images) 或 None（失败时）
        """
        try:
            # 前置检测：跳过空白页，节省 API 调用
            if self._is_blank_image(img_base64):
                logger.info(f"第{page_num}页检测为空白页，跳过OCR")
                return (None, None)

            model_name = self.model
            use_deepseek_prompt = _is_deepseek_ocr_model(model_name)

            effective_max_tokens = config.OCR_LLM_MAX_TOKENS

            if use_deepseek_prompt:
                # DeepSeek-OCR 原生格式 prompt（不含藏文 Unicode 字符，
                # 避免服务端 tokenizer 解析失败返回 500）
                user_text = DEEPSEEK_OCR_PROMPT
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": user_text
                            }
                        ]
                    }
                ]
            else:
                # 通用VLM模型：system prompt + user消息
                lang_hint = self._build_lang_hint()
                lang_name_zh = config.SUPPORTED_LANGUAGES.get(self.source_lang or '', '')
                lang_prefix = f"该文档主要语言为{lang_name_zh}。" if lang_name_zh else ''
                user_text = f"{lang_hint}{lang_prefix}请提取第{page_num}页PDF中的所有文字、表格和图表信息。"
                messages = [
                    {"role": "system", "content": VLM_JSON_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_text
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ]

            # 超时重试：最多重试 1 次
            max_retries = 1
            timeout_error_msg = (
                f"LLM OCR API 请求超时（{config.OCR_LLM_TIMEOUT}秒），"
                f"请检查网络连接或 API 服务状态，建议稍后重试或使用非 LLM OCR 引擎"
            )

            for attempt in range(max_retries + 1):
                try:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=config.OCR_LLM_TEMPERATURE,
                        max_tokens=effective_max_tokens,
                        frequency_penalty=config.OCR_LLM_FREQUENCY_PENALTY,
                        presence_penalty=config.OCR_LLM_PRESENCE_PENALTY,
                    )

                    if not response.choices:
                        logger.warning(f"LLM OCR第{page_num}页返回空choices")
                        return (None, None)
                    result_text = response.choices[0].message.content
                    finish_reason = response.choices[0].finish_reason
                    usage = response.usage
                    logger.info(f"LLM OCR第{page_num}页原始响应(前1000字): {result_text[:1000]}")
                    if finish_reason == 'length':
                        logger.warning(
                            f"第{page_num}页LLM OCR响应被截断（finish_reason=length），"
                            f"当前输出={len(result_text)}字符，请检查输出是否含重复短语，或调高 OCR_LLM_FREQUENCY_PENALTY"
                        )
                    if usage:
                        logger.info(
                            f"第{page_num}页Token使用: prompt={usage.prompt_tokens}, "
                            f"completion={usage.completion_tokens}, total={usage.total_tokens}"
                        )

                    # 委托给解析器解析响应，传递必要的回调
                    parsed = self.parser._parse_response(
                        result_text, page_num, page_info, page=page,
                        temp_images_dir=temp_images_dir,
                        crop_callback=self._crop_and_save_image,
                        table_parse_callback=LlmTableParser._parse_html_table,
                    )
                    return (parsed, None)  # 成功

                except APITimeoutError:
                    if attempt < max_retries:
                        logger.warning(
                            f"第{page_num}页首次请求超时（模型={model_name}），正在进行第 1 次重试"
                        )
                    else:
                        logger.error(
                            f"第{page_num}页 OCR 请求重试后仍然超时（模型={model_name}），放弃该页"
                        )
                        logger.error(f"超时详情: {timeout_error_msg}")
                        return (None, timeout_error_msg)

        except Exception as e:
            logger.error(f"LLM OCR提取第{page_num}页失败: {e}", exc_info=True)
            error_info = classify_llm_error(e)
            error_msg = f"LLM OCR API 请求失败: {error_info['user_message']}"
            # max_tokens 超限时追加当前配置值
            if error_info['category'] == 'bad_request_max_tokens':
                error_msg += f"（当前 OCR_LLM_MAX_TOKENS={config.OCR_LLM_MAX_TOKENS}）"
            return (None, error_msg)

        # 不应到达此处，但为类型安全保留
        return (None, None)

    def _crop_and_save_image(self, page, pdf_bbox, page_num, image_idx, temp_images_dir):
        """从PDF页面裁剪图像区域并保存

        Args:
            page: fitz.Page 对象
            pdf_bbox: (x1, y1, x2, y2) PDF点坐标
            page_num: 页码
            image_idx: 图像索引
            temp_images_dir: 临时图像保存目录

        Returns:
            str: 保存的图像文件路径，失败返回空字符串
        """
        try:
            if not pdf_bbox or pdf_bbox == (0, 0, 0, 0):
                return ''

            rect = fitz.Rect(pdf_bbox)
            # 确保rect在页面范围内
            rect = rect & page.rect
            if rect.is_empty:
                logger.warning(f"图像裁剪区域为空: bbox={pdf_bbox}")
                return ''

            pix = page.get_pixmap(clip=rect, dpi=150)
            save_path = os.path.join(temp_images_dir, f"ocr_img_p{page_num}_{image_idx}.png")
            pix.save(save_path)
            logger.info(f"图像裁剪保存: {save_path}, bbox={pdf_bbox}")
            return save_path
        except Exception as e:
            logger.error(f"图像裁剪保存失败: {e}", exc_info=True)
            return ''


# ============================================================
    # Backward-compatible forwarding methods
    #
    # These private methods have been moved to LlmOcrResponseParser
    # or LlmTableParser.  The forwarding stubs below keep existing
    # tests / callers that reference them on LlmOcrExtractor working.
    # They are NOT part of the public API and will be removed in a
    # future cleanup pass.
    # ============================================================

    def _parse_response(self, result_text, page_num, page_info=None, page=None, temp_images_dir=None):
        """Backward-compatible wrapper: implements orchestration via instance methods
        so that patch.object(...) mocks on individual methods still work."""
        has_ref_tags = '<|ref|>' in result_text and '<|/ref|>' in result_text
        ocr_blocks = None

        if has_ref_tags:
            ocr_blocks = self._parse_ref_tags_to_blocks(result_text)

        json_parsed = False
        if not ocr_blocks:
            data = self._extract_json(result_text)
            if data is not None:
                ocr_blocks = self._parse_json_to_blocks(data)
                json_parsed = True

        if not json_parsed and not ocr_blocks:
            ocr_blocks = self._parse_markdown_to_blocks(result_text)

        if not ocr_blocks:
            return None

        return self._map_ocr_blocks_to_models(ocr_blocks, page_num, page_info, page=page, temp_images_dir=temp_images_dir)

    def _extract_json(self, text):
        return self.parser._extract_json(text)

    def _create_text_block(self, ocr_block, page_num, page_info=None):
        return self.parser._create_text_block(ocr_block, page_num, page_info)

    def _parse_ref_tags_to_blocks(self, result_text):
        return self.parser._parse_ref_tags_to_blocks(result_text)

    def _parse_json_to_blocks(self, data):
        return self.parser._parse_json_to_blocks(data)

    def _parse_markdown_to_blocks(self, result_text):
        return self.parser._parse_markdown_to_blocks(result_text)

    def _map_ocr_blocks_to_models(self, ocr_blocks, page_num, page_info=None, page=None, temp_images_dir=None):
        return self.parser._map_ocr_blocks_to_models(
            ocr_blocks, page_num, page_info, page=page,
            temp_images_dir=temp_images_dir,
            crop_callback=self._crop_and_save_image,
            table_parse_callback=LlmTableParser._parse_html_table,
        )

    def _parse_det_bboxes(self, det_content):
        return self.parser._parse_det_bboxes(det_content)

    def _pixel_to_pdf_coords(self, bbox, page_info, is_normalized=False):
        return self.parser._pixel_to_pdf_coords(bbox, page_info, is_normalized)

    def _detect_formula(self, text):
        return self.parser._detect_formula(text)

    @staticmethod
    def _estimate_font_size(pdf_bbox, text):
        return LlmOcrResponseParser._estimate_font_size(pdf_bbox, text)

    @staticmethod
    def _compute_table_layout(matrix, n_rows, n_cols, table_bbox):
        return LlmTableParser._compute_table_layout(matrix, n_rows, n_cols, table_bbox)

    @staticmethod
    def _parse_html_table(html, table_bbox=None):
        return LlmTableParser._parse_html_table(html, table_bbox)


# Backward compatibility: re-export moved symbols
from modules.ocr.llm_response_parser import OcrBlock, BLOCK_TYPE_MAP  # noqa: E402, F401
