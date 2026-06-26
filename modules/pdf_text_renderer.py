"""PDF文本渲染器

负责在PDF页面上绘制翻译后的文本内容，包括：
- 普通文本渲染（含字体选择、颜色、对齐等）
- LaTeX公式渲染（含usetex和mathtext两种后端）
- 混合文本（中文+公式）渲染
- 文本溢出处理（字体缩小、截断等）
"""

import fitz  # PyMuPDF
import os
import sys
import logging
from PIL import ImageFont

logger = logging.getLogger(__name__)


class PdfTextRenderer:
    """PDF文本渲染器，封装文本渲染相关的所有方法"""

    def __init__(self, pdf_generator):
        """初始化PdfTextRenderer对象

        Args:
            pdf_generator: PdfGenerator父实例，用于访问字体缓存和辅助方法
        """
        self._pg = pdf_generator

    # ============= 主入口方法 =============

    def _draw_translated_text(self, page, translated_blocks, target_lang="zh"):
        """在页面上绘制翻译后的文本，使用块级关联实现样式保留

        核心逻辑：
        1. 第一遍遍历：收集所有需要 redact 的区域，添加 redaction 标注
        2. 执行 apply_redactions 一次性删除原文
        3. 第二遍遍历：按原文样式（字体、大小、颜色、位置）渲染翻译文本

        Args:
            page (fitz.Page): PDF页面对象
            translated_blocks (PdfPage): 当前页的翻译文本块
            target_lang (str): 目标语言代码
        """
        full_text_blocks = translated_blocks.text_blocks
        total_blocks = len(full_text_blocks)

        logger.info(f"开始绘制翻译文本V2，共 {total_blocks} 个完整文本块")

        # ========== 第一遍：添加 redaction 标注 ==========
        for block_idx, full_block in enumerate(full_text_blocks):
            block_bbox = full_block.block_bbox
            original_font_size = full_block.font_size
            rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])

            h_padding = max(5, min(original_font_size * 0.5, 12))
            v_padding = max(3, min(original_font_size * 0.3, 6))
            bg_rect = fitz.Rect(
                max(rect.x0 - h_padding, 0),
                max(rect.y0 - v_padding, 0),
                min(rect.x1 + h_padding, page.rect.width),
                min(rect.y1 + v_padding, page.rect.height)
            )
            page.add_redact_annot(bg_rect, fill=(1, 1, 1))
            logger.debug(
                f"添加 redaction 标注，区域: {bg_rect} "
                f"(h_padding={h_padding:.1f}, v_padding={v_padding:.1f})"
            )

        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        logger.info(f"已执行 redaction 删除原文，共处理 {total_blocks} 个文本块区域")

        # ========== 第二遍：插入翻译文本 ==========
        for block_idx, full_block in enumerate(full_text_blocks):
            logger.info(f"处理完整文本块 {block_idx+1}/{total_blocks}")

            translated_text = full_block.block_text
            block_bbox = full_block.block_bbox

            logger.info(
                f"翻译文本: '{translated_text}' (共 {len(translated_text)} 字符)"
            )
            logger.info(f"文本块位置: {block_bbox}")

            original_font = full_block.font
            original_font_size = full_block.font_size
            color = full_block.color
            bold = full_block.bold
            italic = full_block.italic

            # 计算文本度量（字体大小、行高等）
            bbox_height = block_bbox[3] - block_bbox[1]
            metrics = self._calculate_text_metrics(full_block, bbox_height)
            font_size = metrics['font_size']
            lineheight = metrics['lineheight']

            logger.info(
                f"使用文本块自带样式: 字体='{original_font}', "
                f"大小={font_size}, 粗体={bold}, 斜体={italic}"
            )

            # 颜色转换
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            rgb_color = (r / 255.0, g / 255.0, b / 255.0)

            grayscale = 0.299 * r + 0.587 * g + 0.114 * b
            if grayscale > 200:
                rgb_color = (0, 0, 0)
                logger.info("颜色接近白色，自动改为黑色")

            # 获取适合目标语言的字体
            suitable_font = self._get_suitable_font(page, original_font, target_lang)
            logger.info(
                f"适合的字体: 原字体='{original_font}', "
                f"目标语言='{target_lang}', 选择='{suitable_font}'"
            )

            rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])
            logger.debug(f"文本框尺寸: {rect.width}x{rect.height}")

            # LaTeX公式渲染（整块为公式）
            if (
                getattr(full_block, 'is_formula', False)
                and full_block.block_text
                and self._handle_formula_rendering(page, full_block, rect, font_size)
            ):
                continue

            # 混合文本（中文+公式片段）渲染
            if (
                not getattr(full_block, 'is_formula', False)
                and self._contains_latex_formula(translated_text)
                and self._handle_mixed_formula_rendering(
                    page, translated_text, rect, font_size
                )
            ):
                continue

            # 文本对齐方式
            alignment = getattr(full_block, 'alignment', 0)
            logger.info(
                f"使用对齐方式: {alignment} "
                f"(0=左对齐, 1=居中, 2=右对齐)"
            )

            # ---- 文本渲染尝试 ----
            success = self._attempt_text_rendering(
                page, rect, translated_text, suitable_font,
                font_size, rgb_color, alignment, lineheight
            )

            if not success:
                logger.warning(
                    f"所有尝试（含截断）均失败，跳过文本块绘制: "
                    f"'{translated_text[:50]}...'"
                )

        logger.info("所有翻译文本绘制完成")

    def _attempt_text_rendering(
        self, page, rect, text, fontname, font_size,
        color, alignment, lineheight
    ):
        """尝试所有文本渲染策略，包括字体缩小、行高调整、截断等

        Returns:
            bool: 是否成功渲染
        """
        max_attempts = 5
        success = False

        # 策略1: 逐步缩小字体尝试渲染
        for attempt in range(1, max_attempts + 1):
            if attempt == 1:
                adjusted_font_size = font_size
            else:
                adjusted_font_size = font_size * (1 - (attempt - 1) * 0.1)
                adjusted_font_size = max(adjusted_font_size, font_size * 0.7)

            logger.info(
                f"[文本渲染] 第 {attempt} 次尝试: "
                f"字体大小={adjusted_font_size:.1f} (原始={font_size:.1f})"
            )

            if self._try_render_with_font_scale(
                page, rect, text, fontname, adjusted_font_size,
                color, alignment, lineheight
            ):
                success = True
                break

        # 策略2: 更激进的字体缩小（60%, 50%）
        if not success:
            success = self._try_font_reduction_fallback(
                page, rect, text, fontname, font_size,
                color, alignment, lineheight
            )

        # 策略3: 调整行高倍率
        if not success:
            success = self._try_lineheight_adjustment(
                page, rect, text, fontname, font_size * 0.5,
                color, alignment
            )

        # 策略4: 按单词边界截断
        if not success:
            success = self._try_word_truncation(
                page, rect, text, fontname, font_size * 0.5,
                color, alignment, lineheight
            )

        # 策略5: CJK字符截断（仅在单词截断未尝试时）
        if not success:
            words = text.split()
            if len(words) <= 1:
                success = self._try_cjk_truncation(
                    page, rect, text, fontname, font_size * 0.5,
                    color, alignment, lineheight
                )

        # 策略6: 机械截断
        if not success:
            success = self._try_mechanical_truncation(
                page, rect, text, fontname, font_size * 0.5,
                color, alignment, lineheight
            )

        return success

    # ============= 文本度量计算 =============

    def _calculate_text_metrics(self, full_block, bbox_height):
        """计算文本块的字体大小和行高倍率

        Args:
            full_block: TextBlock对象
            bbox_height: 文本边界框高度

        Returns:
            dict: 包含 font_size 和 lineheight 的字典
        """
        original_font_size = full_block.font_size

        # 字体大小为0时，根据bbox高度估算
        if original_font_size == 0:
            if bbox_height > 0:
                original_font_size = min(bbox_height * 0.75, 36)
                logger.info(
                    f"字体大小为0，根据bbox高度估算: {original_font_size:.1f}pt "
                    f"(bbox_height={bbox_height:.1f})"
                )
            else:
                original_font_size = 12
                logger.info(f"字体大小为0且bbox高度为0，使用默认字体大小: 12pt")

        # 计算原文行高倍率
        if original_font_size > 0 and bbox_height > 0:
            estimated_lines = max(
                1, round(bbox_height / (original_font_size * 1.2))
            )
            original_lineheight = bbox_height / (
                original_font_size * estimated_lines
            )
            original_lineheight = max(1.0, min(original_lineheight, 2.0))
            logger.info(
                f"原文行高倍率: {original_lineheight:.3f} "
                f"(bbox高度={bbox_height:.1f}, 字体大小={original_font_size:.1f}, "
                f"估算行数={estimated_lines})"
            )
        else:
            original_lineheight = 1.2

        return {
            'font_size': original_font_size,
            'lineheight': original_lineheight,
        }

    # ============= 公式渲染 =============

    def _handle_formula_rendering(self, page, full_block, rect, font_size):
        """处理整块LaTeX公式渲染

        Returns:
            bool: 是否成功渲染为图片并插入
        """
        try:
            img_buf = self._render_formula_image(
                full_block.block_text, fontsize=font_size
            )
            if img_buf is not None:
                page.insert_image(rect, stream=img_buf.getvalue())
                return True
            else:
                logger.warning('公式渲染返回 None，降级为文本')
        except Exception as e:
            logger.warning(f'公式渲染异常，降级为文本: {e}')
        return False

    def _handle_mixed_formula_rendering(
        self, page, text, rect, font_size
    ):
        """处理混合文本（中文+LaTeX公式片段）渲染

        Returns:
            bool: 是否成功渲染为图片并插入
        """
        try:
            img_buf = self._render_mixed_text_formula_image(
                text, fontsize=font_size
            )
            if img_buf is not None:
                page.insert_image(rect, stream=img_buf.getvalue())
                logger.info(f'混合公式文本渲染成功: {text[:50]}...')
                return True
            else:
                logger.warning('混合公式文本渲染返回 None，降级为纯文本')
        except Exception as e:
            logger.warning(f'混合公式文本渲染异常，降级为文本: {e}')
        return False

    def _render_formula_image(self, latex, fontsize=12):
        """将LaTeX公式渲染为图片

        优先使用usetex（完整LaTeX支持），降级使用mathtext。

        Returns:
            BytesIO|None: 图片字节流，失败返回None
        """
        import matplotlib.pyplot as plt
        import io

        self._pg._setup_matplotlib_cjk()

        # 优先使用 usetex
        if self._pg._check_latex_available():
            try:
                plt.rcParams['text.usetex'] = True
                plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
                fig, ax = plt.subplots(figsize=(0.01, 0.01))
                ax.axis('off')
                text = ax.text(
                    0, 0, f'${latex}$',
                    fontsize=fontsize, ha='left', va='bottom'
                )
                fig.canvas.draw()
                bbox = text.get_window_extent()
                fig.set_size_inches(
                    bbox.width / fig.dpi + 0.1,
                    bbox.height / fig.dpi + 0.05
                )
                buf = io.BytesIO()
                fig.savefig(
                    buf, format='png', dpi=150,
                    bbox_inches='tight', pad_inches=0.02,
                    transparent=True
                )
                plt.close(fig)
                buf.seek(0)
                return buf
            except Exception as e:
                logger.warning(f'usetex 渲染失败: {e}，降级为 mathtext')
                plt.rcParams['text.usetex'] = False

        # 降级1：用原始 LaTeX 尝试 mathtext 渲染
        try:
            buf = self._pg._try_mathtext_render(latex, fontsize)
            if buf:
                return buf
        except Exception:
            pass

        # 降级2：预处理 LaTeX 后用 mathtext 渲染
        processed = self._pg._preprocess_latex_for_mathtext(latex)
        try:
            buf = self._pg._try_mathtext_render(processed, fontsize)
            if buf:
                return buf
        except Exception:
            pass

        logger.warning(f'公式渲染完全失败: {latex[:50]}...')
        return None

    def _render_mixed_text_formula_image(self, text, fontsize=12):
        """将混合文本（中文+LaTeX公式）渲染为图片

        使用matplotlib的mathtext功能，在文本中嵌入 $...$ 公式。

        Returns:
            BytesIO|None: 图片字节流，失败返回None
        """
        import matplotlib.pyplot as plt
        import io

        self._pg._setup_matplotlib_cjk()

        processed = self._pg._preprocess_latex_for_mathtext(text)

        if self._pg._check_latex_available():
            try:
                plt.rcParams['text.usetex'] = True
                plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
                fig, ax = plt.subplots(figsize=(0.01, 0.01))
                ax.axis('off')
                text_obj = ax.text(
                    0, 0, processed,
                    fontsize=fontsize, ha='left', va='bottom'
                )
                fig.canvas.draw()
                bbox = text_obj.get_window_extent()
                if bbox.width < 1 or bbox.height < 1:
                    plt.close(fig)
                    plt.rcParams['text.usetex'] = False
                    raise ValueError("rendered size too small")
                fig.set_size_inches(
                    bbox.width / fig.dpi + 0.1,
                    bbox.height / fig.dpi + 0.05
                )
                buf = io.BytesIO()
                fig.savefig(
                    buf, format='png', dpi=150,
                    bbox_inches='tight', pad_inches=0.02,
                    transparent=True
                )
                plt.close(fig)
                buf.seek(0)
                return buf
            except Exception as e:
                logger.warning(
                    f'混合文本 usetex 渲染失败: {e}，降级为 mathtext'
                )
                plt.rcParams['text.usetex'] = False

        try:
            buf = self._pg._try_mathtext_render(
                processed, fontsize, is_mixed=True
            )
            if buf:
                return buf
        except Exception:
            pass

        logger.warning(f'混合公式文本渲染失败: {text[:50]}...')
        return None

    @staticmethod
    def _contains_latex_formula(text):
        """检测文本是否包含 LaTeX 公式片段"""
        import re
        if re.search(r'(?<!\$)\$(?!\$).+?\$(?!\$)', text):
            return True
        if re.search(r'\$\$.+?\$\$', text):
            return True
        if re.search(r'\\\(.*?\\\)', text):
            return True
        if re.search(r'\\\[.*?\\\]', text):
            return True
        return False

    # ============= 分步渲染尝试 =============

    def _try_render_with_font_scale(
        self, page, rect, text, fontname, font_size,
        color, alignment, lineheight
    ):
        """使用给定参数的单次文本渲染尝试

        Returns:
            bool: 渲染是否成功
        """
        try:
            result = page.insert_textbox(
                rect, text,
                fontname=fontname, fontsize=font_size,
                color=color, align=alignment, lineheight=lineheight
            )
            logger.info(
                f"[文本渲染] 字体大小={font_size:.1f}: "
                f"返回值={result}, 成功={result >= 0}"
            )
            if result >= 0:
                logger.info(
                    f"[OK] 文本渲染成功，插入了 {result} 个字符，"
                    f"使用字体大小: {font_size}，文本框大小: {rect}"
                )
                return True
            logger.warning(
                f"[WARN] 文本溢出，返回值: {result}，"
                f"当前字体大小: {font_size}，文本框: {rect}"
            )
            logger.warning(
                f"溢出文本: '{text[:100]}...' (完整长度={len(text)})"
            )
        except Exception as e:
            logger.warning(f"[FAIL] 绘制失败: {e}")
        return False

    def _try_font_reduction_fallback(
        self, page, rect, text, fontname, font_size,
        color, alignment, lineheight
    ):
        """尝试更激进的字体缩小（60%, 50%）

        Returns:
            bool: 渲染是否成功
        """
        logger.info(f"[字体缩小] 尝试缩小字体以适配文本框")
        for font_ratio in [0.6, 0.5]:
            adjusted_font_size = font_size * font_ratio
            try:
                result = page.insert_textbox(
                    rect, text,
                    fontname=fontname, fontsize=adjusted_font_size,
                    color=color, align=alignment, lineheight=lineheight
                )
                if result >= 0:
                    logger.info(
                        f"[OK] 缩小字体到{font_ratio*100:.0f}%后渲染成功，"
                        f"字体大小: {adjusted_font_size}"
                    )
                    return True
                logger.warning(
                    f"缩小字体到{font_ratio*100:.0f}%仍溢出，继续尝试"
                )
            except Exception as e:
                logger.warning(
                    f"缩小字体到{font_ratio*100:.0f}%绘制失败: {e}"
                )
                break
        return False

    def _try_lineheight_adjustment(
        self, page, rect, text, fontname, font_size, color, alignment
    ):
        """尝试调整行高倍率以避免截断

        Returns:
            bool: 渲染是否成功
        """
        logger.info(f"[行高调整] 尝试调整行高倍率以避免截断")
        for lineheight_attempt in [1.5, 1.8, 2.0]:
            logger.info(f"[行高调整] 尝试行高倍率={lineheight_attempt}")
            try:
                result = page.insert_textbox(
                    rect, text,
                    fontname=fontname, fontsize=font_size,
                    color=color, align=alignment,
                    lineheight=lineheight_attempt
                )
                if result >= 0:
                    logger.info(
                        f"[OK] 调整行高倍率到{lineheight_attempt}后渲染成功"
                    )
                    return True
                logger.debug(f"行高倍率{lineheight_attempt}仍溢出，继续尝试")
            except Exception as e:
                logger.warning(f"行高调整尝试失败: {e}")
                break
        return False

    def _try_word_truncation(
        self, page, rect, text, fontname, font_size,
        color, alignment, lineheight
    ):
        """按单词边界截断文本（适用于有空格分隔的文本）

        Returns:
            bool: 渲染是否成功
        """
        words = text.split()
        if len(words) <= 1:
            return False

        logger.warning(
            f"[智能截断] 开始单词截断，文本框尺寸: "
            f"宽度={rect.width:.1f}, 高度={rect.height:.1f}"
        )
        logger.warning(
            f"[智能截断] 使用最小字体大小: {font_size:.1f}, "
            f"行高倍率: {lineheight:.3f}"
        )

        for word_count in range(len(words) - 1, max(1, len(words) // 10), -1):
            truncated_text = ' '.join(words[:word_count]) + '...'
            logger.info(
                f"[智能截断] 尝试保留{word_count}个单词: "
                f"'{truncated_text[:50]}...'"
            )
            try:
                result = page.insert_textbox(
                    rect, truncated_text,
                    fontname=fontname, fontsize=font_size,
                    color=color, align=alignment, lineheight=lineheight
                )
                if result >= 0:
                    logger.warning(
                        f"[智能截断成功] 截断文本后渲染成功: "
                        f"原始单词数={len(words)}, "
                        f"截断后单词数={word_count}, "
                        f"截断比例={word_count/len(words):.0%}, "
                        f"字体大小={font_size:.1f}, "
                        f"文本框尺寸=宽度={rect.width:.1f}, "
                        f"高度={rect.height:.1f}"
                    )
                    return True
            except Exception as e:
                logger.warning(f"智能截断绘制失败: {e}")
                break
        return False

    def _try_cjk_truncation(
        self, page, rect, text, fontname, font_size,
        color, alignment, lineheight
    ):
        """按CJK字符数截断文本（中文/日文/韩文无空格分隔）

        Returns:
            bool: 渲染是否成功
        """
        total_chars = len(text)
        if total_chars == 0:
            return False

        logger.warning(
            f"[CJK截断] 开始CJK字符截断，原始字符数={total_chars}"
        )

        for char_ratio in [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]:
            keep_chars = max(1, int(total_chars * char_ratio))
            truncated_text = text[:keep_chars] + '...'
            logger.info(
                f"[CJK截断] 尝试保留{keep_chars}/{total_chars}字符"
                f"({char_ratio:.0%}): '{truncated_text[:50]}...'"
            )
            try:
                result = page.insert_textbox(
                    rect, truncated_text,
                    fontname=fontname, fontsize=font_size,
                    color=color, align=alignment, lineheight=lineheight
                )
                if result >= 0:
                    logger.warning(
                        f"[CJK截断成功] 截断后渲染成功: "
                        f"原始字符数={total_chars}, "
                        f"截断后字符数={keep_chars}, "
                        f"截断比例={char_ratio:.0%}"
                    )
                    return True
            except Exception as e:
                logger.warning(f"CJK截断绘制失败: {e}")
                break
        return False

    def _try_mechanical_truncation(
        self, page, rect, text, fontname, font_size,
        color, alignment, lineheight
    ):
        """机械截断：按比例逐步截断文本（最后手段）

        Returns:
            bool: 渲染是否成功
        """
        logger.warning(
            f"[机械截断] 智能截断失败，回退到机械截断"
        )

        ellipsis = "..."
        max_truncation_attempts = 10

        for trunc_attempt in range(1, max_truncation_attempts + 1):
            ratio = 1.0 - trunc_attempt * 0.1
            if ratio < 0.3:
                logger.warning(
                    f"[机械截断] 达到最小比例限制(30%)，停止截断"
                )
                break

            truncated_text = text[:max(1, int(len(text) * ratio))]
            if not truncated_text.endswith(ellipsis):
                truncated_text = truncated_text.rstrip() + ellipsis

            logger.info(
                f"[机械截断] 第 {trunc_attempt} 次截断尝试: "
                f"截断比例={ratio:.0%}"
            )
            logger.info(
                f"[机械截断] 截断后文本预览: "
                f"'{truncated_text[:50]}...' (长度={len(truncated_text)})"
            )
            logger.info(
                f"[机械截断] 文本框尺寸: "
                f"宽度={rect.width:.1f}, 高度={rect.height:.1f}, "
                f"字体大小={font_size:.1f}"
            )

            try:
                result = page.insert_textbox(
                    rect, truncated_text,
                    fontname=fontname, fontsize=font_size,
                    color=color, align=alignment, lineheight=lineheight
                )
                if result >= 0:
                    logger.warning(
                        f"[机械截断成功] 截断文本后渲染成功: "
                        f"原始长度={len(text)}, "
                        f"截断后长度={len(truncated_text)}, "
                        f"截断比例={ratio:.0%}, "
                        f"字体大小={font_size:.1f}, "
                        f"文本框尺寸=宽度={rect.width:.1f}, "
                        f"高度={rect.height:.1f}, "
                        f"行高倍率={lineheight:.3f}, "
                        f"截断后文本预览='{truncated_text[:50]}...'"
                    )
                    return True
                logger.debug(f"截断到{ratio:.0%}仍溢出，继续截断")
            except Exception as e:
                logger.warning(f"截断文本绘制失败: {e}")
                break
        return False

    # ============= 字体管理 =============

    def _get_suitable_font(self, page, original_font, target_lang):
        """获取适合目标语言的字体

        使用 font_cache 缓存字体查找结果，避免重复的文件系统查找和兼容性检测。

        Args:
            page (fitz.Page): PDF页面对象
            original_font (str): 原始字体名称
            target_lang (str): 目标语言代码

        Returns:
            str: 适合的字体名称

        Raises:
            ValueError: 当找不到适合目标语言的字体时抛出
        """
        logger.info(
            f"获取适合字体: 原字体='{original_font}', "
            f"目标语言='{target_lang}'"
        )

        # 检查缓存
        cache_key = (original_font, target_lang)
        if cache_key in self._pg.font_cache:
            cached_fontname, cached_fontfile = self._pg.font_cache[cache_key]
            logger.info(
                f"字体缓存命中: fontname='{cached_fontname}', "
                f"fontfile='{cached_fontfile}'"
            )
            try:
                if cached_fontfile:
                    page.insert_font(
                        fontname=cached_fontname, fontfile=cached_fontfile
                    )
                else:
                    page.insert_font(
                        fontname=cached_fontname, fontfile=None
                    )
            except Exception as e:
                logger.warning(
                    f"缓存字体插入当前页面失败，将重新查找: {e}"
                )
                del self._pg.font_cache[cache_key]
            else:
                return cached_fontname

        # 1. 检查原始字体
        if original_font:
            try:
                logger.info(f"尝试使用原始字体 '{original_font}'")
                page.insert_font(fontname=original_font, fontfile=None)
                if self._check_embedded_font_support(page, original_font, target_lang):
                    logger.info(
                        f"原始字体 '{original_font}' 支持目标语言 "
                        f"'{target_lang}'，直接使用"
                    )
                    self._pg.font_cache[cache_key] = (original_font, None)
                    return original_font
                else:
                    logger.info(
                        f"原始字体 '{original_font}' 不支持目标语言 "
                        f"'{target_lang}'，跳过"
                    )
            except Exception as e:
                logger.warning(
                    f"原始字体 '{original_font}' 插入失败: {e}"
                )

        # 2. 从系统获取可用字体列表
        system_font_paths = self._get_system_fonts()
        logger.info(
            f"系统字体列表获取完成，共 {len(system_font_paths)} 种字体"
        )

        # 3. 从系统字体中选择支持目标语言的字体
        if system_font_paths:
            logger.info(
                f"开始从系统字体中选择支持 '{target_lang}' 的字体"
            )

            # 特殊处理Arial Unicode.ttf
            arial_unicode_found = False
            for font_path in system_font_paths:
                if 'Arial Unicode.ttf' in font_path:
                    arial_unicode_found = True
                    try:
                        logger.info(
                            f"找到Arial Unicode字体: {font_path}"
                        )
                        fontname = "arialuni"
                        page.insert_font(
                            fontname=fontname, fontfile=font_path
                        )
                        logger.info(
                            f"成功使用Arial Unicode字体作为 '{fontname}'"
                        )
                        self._pg.font_cache[cache_key] = (fontname, font_path)
                        return fontname
                    except Exception as e:
                        logger.error(
                            f"Arial Unicode字体插入失败: {e}"
                        )
                        continue

            if not arial_unicode_found:
                logger.info("未找到Arial Unicode字体，继续搜索其他字体")

            # 遍历所有系统字体
            compatible_fonts = []
            for font_path in system_font_paths:
                try:
                    if self._check_font_support(font_path, target_lang):
                        compatible_fonts.append(font_path)
                        logger.debug(
                            f"字体 '{os.path.basename(font_path)}' "
                            f"支持目标语言 '{target_lang}'"
                        )
                except Exception as e:
                    logger.debug(
                        f"检查字体 '{os.path.basename(font_path)}' "
                        f"时出错: {e}"
                    )

            logger.info(
                f"找到 {len(compatible_fonts)} 种支持 "
                f"'{target_lang}' 的字体"
            )

            for font_path in compatible_fonts:
                try:
                    logger.info(f"尝试使用兼容字体: {font_path}")
                    font_filename = os.path.basename(font_path)
                    fontname = os.path.splitext(font_filename)[0].replace(' ', '_')
                    fontname = ''.join(
                        c for c in fontname if c.isalnum() or c == '_'
                    )
                    page.insert_font(fontname=fontname, fontfile=font_path)
                    logger.info(
                        f"成功使用系统字体 '{font_filename}' 作为 '{fontname}'"
                    )
                    self._pg.font_cache[cache_key] = (fontname, font_path)
                    return fontname
                except Exception as e:
                    logger.warning(
                        f"系统字体 '{os.path.basename(font_path)}' "
                        f"插入失败: {e}"
                    )
                    continue

        # 4. 无法找到任何适合的字体
        error_msg = (
            f"无法找到适合目标语言 '{target_lang}' 的字体。"
            f"请安装支持该语言的字体，例如Arial Unicode或其他支持"
            f"{target_lang}语言的字体。"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    def _check_embedded_font_support(self, page, fontname, target_lang):
        """检查PDF内嵌字体是否支持目标语言字符

        Returns:
            bool: 字体是否支持目标语言字符
        """
        test_chars = {
            'zh': '你好',
            'en': 'Hello',
            'de': 'äöüß',
            'fr': 'éèêàç',
            'es': 'ñ¿¡',
            'pt': 'ãç',
            'it': 'àèì',
            'nl': 'ëï',
            'ja': 'こんにちは',
            'ko': '안녕',
            'th': 'สวัสดี',
            'vi': 'chào',
            'ru': 'Привет',
            'ar': 'مرحبا',
            'hi': 'नमस्ते',
            'he': 'שלום',
            'bo': 'བཀྲ་ཤིས་བདེ་ལེགས',
        }
        test_char = test_chars.get(target_lang, test_chars['en'])

        latin_langs = {'en', 'fr', 'de', 'es', 'pt', 'it', 'nl'}
        if target_lang in latin_langs:
            system_font_paths = self._get_system_fonts()
            matched_path = self._find_font_file(fontname, system_font_paths)
            if matched_path:
                return self._check_font_support(matched_path, target_lang)
            logger.debug(
                f"拉丁语言 '{target_lang}'，内嵌字体 "
                f"'{fontname}' 默认支持"
            )
            return True

        system_font_paths = self._get_system_fonts()
        matched_path = self._find_font_file(fontname, system_font_paths)
        if matched_path:
            result = self._check_font_support(matched_path, target_lang)
            logger.debug(
                f"内嵌字体 '{fontname}' 系统文件检测: {result}"
            )
            return result

        logger.debug(
            f"内嵌字体 '{fontname}' 未找到系统文件，非拉丁语言 "
            f"'{target_lang}' 默认不支持"
        )
        return False

    def _check_font_support(self, font_path, target_lang):
        """检查字体是否真正支持目标语言

        Returns:
            bool: 字体是否真正支持目标语言
        """
        try:
            font_filename = os.path.basename(font_path)
            font = ImageFont.truetype(font_path, 12)

            test_chars = {
                'zh': '你好世界',
                'en': 'Hello World',
                'de': 'äöüßÄÖÜ',
                'fr': 'éèêàçîôù',
                'es': 'ñ¿¡áéíóú',
                'pt': 'ãçáéíóú',
                'it': 'àèìòù',
                'nl': 'ëï',
                'ja': 'こんにちは世界',
                'ko': '안녕하세요 세계',
                'th': 'สวัสดี',
                'vi': 'Xin chào',
                'ru': 'Привет',
                'ar': 'مرحبا',
                'hi': 'नमस्ते',
                'he': 'שלום',
                'bo': 'བཀྲ་ཤིས་བདེ་ལེགས',
            }
            test_char = test_chars.get(target_lang, test_chars['en'])

            for char in test_char:
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                if char_width < 1:
                    logger.debug(
                        f"字体 '{font_filename}' 不包含字符 '{char}' 的字形"
                    )
                    return False

            logger.debug(
                f"字体 '{font_filename}' 支持目标语言 '{target_lang}'"
            )
            return True
        except Exception as e:
            logger.debug(
                f"字体 '{os.path.basename(font_path)}' 加载失败或不支持 "
                f"目标语言 '{target_lang}': {e}"
            )
            return False

    def _get_system_fonts(self):
        """从系统中获取可用字体列表（带缓存）

        Returns:
            list: 系统可用字体完整路径列表
        """
        if self._pg._system_fonts_cache is not None:
            return self._pg._system_fonts_cache

        system_fonts = []
        try:
            if sys.platform == 'win32':
                font_dirs = [r'C:\Windows\Fonts']
            elif sys.platform == 'darwin':
                font_dirs = [
                    '/System/Library/Fonts',
                    '/Library/Fonts',
                    os.path.expanduser('~/Library/Fonts'),
                ]
            else:
                font_dirs = [
                    '/usr/share/fonts',
                    '/usr/local/share/fonts',
                    os.path.expanduser('~/.fonts'),
                ]

            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    for root, _, files in os.walk(font_dir):
                        for file in files:
                            if file.endswith(('.ttf', '.otf', '.ttc')):
                                font_path = os.path.join(root, file)
                                system_fonts.append(font_path)

            system_fonts = list(set(system_fonts))
            system_fonts.sort()
            logger.info(
                f"从系统获取到 {len(system_fonts)} 种可用字体"
            )
        except Exception as e:
            logger.warning(f"获取系统字体列表失败: {e}")
            system_fonts = []

        self._pg._system_fonts_cache = system_fonts
        return system_fonts

    @staticmethod
    def _find_font_file(fontname, system_font_paths):
        """在系统字体列表中查找匹配的字体文件

        Returns:
            str|None: 匹配的字体文件路径，未找到返回 None
        """
        if not fontname or not system_font_paths:
            return None

        norm_target = fontname.lower().replace('-', '').replace(' ', '')

        for font_path in system_font_paths:
            filename = os.path.basename(font_path)
            name_without_ext = os.path.splitext(filename)[0]
            norm_filename = name_without_ext.lower().replace('-', '').replace(' ', '')

            if norm_target == norm_filename:
                return font_path

            if (
                norm_filename.startswith(norm_target + '-')
                or norm_filename.startswith(norm_target + '_')
                or norm_filename.startswith(norm_target + 'bold')
                or norm_filename.startswith(norm_target + 'italic')
            ):
                return font_path

        for font_path in system_font_paths:
            filename = os.path.basename(font_path)
            name_without_ext = os.path.splitext(filename)[0]
            norm_filename = name_without_ext.lower().replace('-', '').replace(' ', '')
            if norm_target in norm_filename:
                return font_path

        return None
