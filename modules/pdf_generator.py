"""PDF生成类

负责将翻译后的文本生成新的PDF文件，并尽量保留原始PDF的布局和格式。

核心功能：
1. 页面复制（从原始PDF复制页面到新文档）
2. 翻译文本渲染（委派给 PdfTextRenderer）
3. 翻译表格渲染（委派给 PdfTableRenderer）

注意：文本渲染和表格渲染的具体实现已分别迁移到 PdfTextRenderer 和 PdfTableRenderer。
"""

import fitz  # PyMuPDF
import os
import sys
import logging
import threading
from PIL import ImageFont

# 在模块级别设置 matplotlib 后端（仅调用一次）
import matplotlib
matplotlib.use('Agg')

from modules.pdf_text_renderer import PdfTextRenderer
from modules.pdf_table_renderer import PdfTableRenderer

logger = logging.getLogger(__name__)


class PdfGenerator:
    """PDF生成类

    负责将翻译后的文本生成新的PDF文件，并尽量保留原始PDF的布局和格式。
    """

    def __init__(self):
        """初始化PdfGenerator对象"""
        # 字体目录
        self.fonts_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'fonts'
        )

        # 字体缓存，避免重复加载
        self.font_cache = {}

        # 系统字体列表缓存（避免重复遍历文件系统）
        self._system_fonts_cache = None

        # 确保字体目录存在
        os.makedirs(self.fonts_dir, exist_ok=True)
        logger.info(f"PDF生成器初始化完成，字体目录: {self.fonts_dir}")

        # 创建渲染器子组件
        self.text_renderer = PdfTextRenderer(self)
        self.table_renderer = PdfTableRenderer(self)

    # ============= 核心PDF生成 =============

    def generate_pdf(
        self, original_pdf_path, translated_content,
        output_pdf_path, target_lang="zh", target_pages=None
    ):
        """生成翻译后的PDF文件

        Args:
            original_pdf_path (str): 原始PDF文件路径
            translated_content (dict): 翻译后的内容
                - blocks (list): 每页的完整文本块列表
                - tables (list): 翻译后的表格列表
            output_pdf_path (str): 输出PDF文件路径
            target_lang (str): 目标语言代码
            target_pages (list, optional): 指定输出的页码列表
        """
        logger.info(
            f"开始生成PDF，原始文件: {original_pdf_path}, "
            f"输出文件: {output_pdf_path}, 目标语言: {target_lang}"
        )

        logger.info(
            "PDF生成器接收到的translated_content包含blocks信息: "
            f"{('blocks' in translated_content)}"
        )
        if 'blocks' in translated_content:
            total_blocks = sum(
                len(page.text_blocks)
                for page in translated_content['blocks']
            )
            logger.info(
                f"PDF生成器接收到的blocks信息: "
                f"总页数={len(translated_content['blocks'])}, "
                f"总blocks数={total_blocks}"
            )
            for i, page_blocks in enumerate(translated_content['blocks']):
                blocks_list = page_blocks.text_blocks
                block_count = len(blocks_list)
                logger.debug(
                    f"PDF生成器 第 {i+1} 页有 {block_count} 个文本块"
                )
                for j, block in enumerate(blocks_list):
                    block_text = block.block_text
                    block_bbox = block.block_bbox
                    block_no = block.block_no
                    logger.debug(
                        f"PDF生成器 第 {i+1} 页 文本块 {j+1}: "
                        f"'{block_text}' 位置: {block_bbox} "
                        f"块编号: {block_no}"
                    )
        else:
            logger.warning(
                "PDF生成器未接收到blocks信息，无法绘制翻译文本"
            )

        if not os.path.exists(original_pdf_path):
            logger.error(
                f"原始PDF文件不存在: {original_pdf_path}"
            )
            raise FileNotFoundError(
                f"原始PDF文件不存在: {original_pdf_path}"
            )

        try:
            with fitz.open(original_pdf_path) as original_doc:
                logger.info(
                    f"成功打开原始PDF，总页数: {len(original_doc)}"
                )

                new_doc = fitz.open()
                try:
                    logger.info("创建新的PDF文档成功")

                    logger.info(
                        f"翻译内容: 完整文本块 "
                        f"{len(translated_content.get('blocks', []))}, "
                        f"表格 {len(translated_content.get('tables', []))}"
                    )

                    total_original_pages = len(original_doc)
                    logger.info(f"原始PDF总页数: {total_original_pages}")

                    if target_pages:
                        pages_to_output = [
                            p for p in target_pages
                            if 1 <= p <= total_original_pages
                        ]
                        logger.info(f"指定输出页码: {pages_to_output}")
                    else:
                        pages_to_output = list(
                            range(1, total_original_pages + 1)
                        )

                    blocks_by_page = {}
                    for blocks_content in translated_content.get(
                        'blocks', []
                    ):
                        blocks_by_page[blocks_content.page_num] = (
                            blocks_content
                        )

                    tables_by_page = {}
                    for table in translated_content.get('tables', []):
                        tables_by_page.setdefault(
                            table.page_num, []
                        ).append(table)

                    self.font_cache = {}

                    for page_num in pages_to_output:
                        original_page_idx = page_num - 1

                        new_doc.insert_pdf(
                            original_doc,
                            from_page=original_page_idx,
                            to_page=original_page_idx
                        )
                        new_page = new_doc[-1]

                        page_translated_blocks = blocks_by_page.get(
                            page_num
                        )

                        if (
                            page_translated_blocks
                            and page_translated_blocks.text_blocks
                        ):
                            blocks_count = len(
                                page_translated_blocks.text_blocks
                            )
                            logger.info(
                                f"第 {page_num} 页有 {blocks_count} "
                                f"个完整文本块"
                            )
                            self._draw_translated_text(
                                new_page, page_translated_blocks,
                                target_lang
                            )
                            logger.info(
                                f"第 {page_num} 页绘制完成"
                            )
                        else:
                            logger.info(
                                f"第 {page_num} 页无翻译文本块，"
                                f"保留原始页面"
                            )

                        page_tables = tables_by_page.get(page_num, [])
                        if page_tables:
                            logger.info(
                                f"第 {page_num} 页有 "
                                f"{len(page_tables)} 个表格需要处理"
                            )
                            for i, table in enumerate(page_tables):
                                self._draw_translated_table(
                                    new_page, table, target_lang
                                )
                                logger.info(
                                    f"第 {page_num} 页表格 {i+1} "
                                    f"绘制完成"
                                )

                    logger.info(
                        f"开始保存新PDF: {output_pdf_path}"
                    )
                    total_pages = len(new_doc)
                    new_doc.save(
                        output_pdf_path,
                        deflate=True, garbage=4, clean=True
                    )
                finally:
                    new_doc.close()

                logger.info(
                    f"PDF生成完成，输出文件: {output_pdf_path}, "
                    f"总页数: {total_pages}"
                )

        except Exception as e:
            logger.error(
                f"生成PDF时出错: {str(e)}", exc_info=True
            )
            raise Exception(f"生成PDF时出错: {str(e)}")

    # ============= LaTeX 检测与渲染 =============

    # 类级别缓存：LaTeX 可用性检测结果
    _latex_available = None
    _latex_lock = threading.Lock()

    @classmethod
    def _check_latex_available(cls):
        """检测系统是否安装了 LaTeX 引擎（用于 usetex 渲染）"""
        with cls._latex_lock:
            if cls._latex_available is not None:
                return cls._latex_available
            import subprocess
            import glob as glob_module

            try:
                result = subprocess.run(
                    ['latex', '--version'],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    cls._latex_available = True
                    logger.info("LaTeX 可用性检测: 可用 (PATH)")
                    return cls._latex_available
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            common_paths = []

            if sys.platform == 'darwin':
                common_paths = [
                    '/Library/TeX/texbin/latex',
                    '/opt/homebrew/bin/latex',
                ]
                common_paths.extend(
                    sorted(
                        glob_module.glob(
                            '/usr/local/texlive/*/bin/universal-darwin/latex'
                        ),
                        reverse=True
                    )
                )
            elif sys.platform == 'linux':
                common_paths = [
                    '/usr/bin/latex',
                    '/usr/local/bin/latex',
                ]
                common_paths.extend(
                    sorted(
                        glob_module.glob(
                            '/usr/local/texlive/*/bin/x86_64-linux/latex'
                        ),
                        reverse=True
                    )
                )
                common_paths.extend(
                    sorted(
                        glob_module.glob(
                            '/usr/local/texlive/*/bin/aarch64-linux/latex'
                        ),
                        reverse=True
                    )
                )
            elif sys.platform == 'win32':
                common_paths = [
                    r'C:\Program Files\MiKTeX\miktex\bin\x64\latex.exe',
                ]
                common_paths.extend(
                    sorted(
                        glob_module.glob(
                            'C:/texlive/*/bin/windows/latex.exe'
                        ),
                        reverse=True
                    )
                )

            found_path = None
            for candidate in common_paths:
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    found_path = candidate
                    break

            if found_path:
                latex_dir = os.path.dirname(found_path)
                current_path = os.environ.get('PATH', '')
                if latex_dir not in current_path.split(os.pathsep):
                    os.environ['PATH'] = latex_dir + os.pathsep + current_path
                    logger.info(
                        f"LaTeX 可用性检测: 可用 ({found_path})，"
                        f"已将 {latex_dir} 添加到 PATH"
                    )
                else:
                    logger.info(
                        f"LaTeX 可用性检测: 可用 ({found_path})，"
                        f"PATH 已包含 {latex_dir}"
                    )
                cls._latex_available = True
            else:
                cls._latex_available = False
                logger.info("LaTeX 可用性检测: 不可用")

            return cls._latex_available

    @staticmethod
    def _setup_matplotlib_cjk():
        """配置 matplotlib 的 CJK 字体支持"""
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = [
            'PingFang SC', 'Heiti SC', 'STHeiti',
            'SimHei', 'Arial Unicode MS', 'DejaVu Sans'
        ]
        plt.rcParams['axes.unicode_minus'] = False

    @staticmethod
    def _preprocess_latex_for_mathtext(latex):
        """预处理 LaTeX，去除 mathtext 不支持的命令，用于降级渲染"""
        import re
        latex = re.sub(r'\\\(', '$', latex)
        latex = re.sub(r'\\\)', '$', latex)
        latex = re.sub(r'\\\[', '$$', latex)
        latex = re.sub(r'\\\]', '$$', latex)
        latex = re.sub(r'\$\$', '$', latex)

        prev = None
        while prev != latex:
            prev = latex
            latex = re.sub(
                r'\\(?:text|mathrm|mathbf|mathit|mathsf|mathtt|'
                r'textbf|textrm)\{([^}]*)\}',
                r'\1', latex
            )

        prev = None
        while prev != latex:
            prev = latex
            latex = re.sub(
                r'\\begin\{(aligned|gathered|cases|equation\*?|'
                r'align\*?|gather\*?)\}(.*?)\\end\{\1\}',
                lambda m: re.sub(
                    r'\\\\', ' ', m.group(2)
                ).replace('&', ''),
                latex,
                flags=re.DOTALL,
            )

        latex = re.sub(r'\\\\(?=\s*&|\\\\|$)', ' ', latex)
        latex = re.sub(r'(?<=\S)\s*&\s*(?=\S)', ' ', latex)

        greek_letters = {
            r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ',
            r'\delta': 'δ', r'\epsilon': 'ε', r'\zeta': 'ζ',
            r'\eta': 'η', r'\theta': 'θ', r'\iota': 'ι',
            r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
            r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
            r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ',
            r'\phi': 'φ', r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
            r'\Alpha': 'Α', r'\Beta': 'Β', r'\Gamma': 'Γ',
            r'\Delta': 'Δ', r'\Epsilon': 'Ε', r'\Zeta': 'Ζ',
            r'\Eta': 'Η', r'\Theta': 'Θ', r'\Iota': 'Ι',
            r'\Kappa': 'Κ', r'\Lambda': 'Λ', r'\Mu': 'Μ',
            r'\Nu': 'Ν', r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Rho': 'Ρ',
            r'\Sigma': 'Σ', r'\Tau': 'Τ', r'\Upsilon': 'Υ',
            r'\Phi': 'Φ', r'\Chi': 'Χ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
        }
        for cmd, char in greek_letters.items():
            latex = latex.replace(cmd, char)

        math_symbols = {
            r'\circ': '°', r'\cdot': '·', r'\times': '×',
            r'\div': '÷', r'\pm': '±', r'\leq': '≤', r'\geq': '≥',
            r'\neq': '≠', r'\approx': '≈', r'\infty': '∞',
            r'\partial': '∂', r'\nabla': '∇', r'\forall': '∀',
            r'\exists': '∃', r'\in': '∈', r'\notin': '∉',
            r'\subset': '⊂', r'\supset': '⊃', r'\cup': '∪',
            r'\cap': '∩', r'\emptyset': '∅',
            r'\%': '%', r'\&': '&', r'\#': '#', r'\$': '$',
        }
        for cmd, char in math_symbols.items():
            latex = latex.replace(cmd, char)

        latex = re.sub(r'\\left\b', '', latex)
        latex = re.sub(r'\\right\b', '', latex)
        return latex

    def _try_mathtext_render(self, latex, fontsize=12, is_mixed=False):
        """尝试用 mathtext 渲染公式

        Args:
            latex: LaTeX 文本
            fontsize: 字体大小
            is_mixed: 是否为混合文本，混合文本不额外包裹 $...$

        Returns:
            BytesIO|None: 成功返回 BytesIO，失败返回 None
        """
        import matplotlib.pyplot as plt
        import io

        self._setup_matplotlib_cjk()

        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        ax.axis('off')
        try:
            if is_mixed:
                display_text = latex
            else:
                display_text = f'${latex}$'
            text = ax.text(
                0, 0, display_text,
                fontsize=fontsize, ha='left', va='bottom'
            )
            fig.canvas.draw()
            bbox = text.get_window_extent()
            if bbox.width < 1 or bbox.height < 1:
                plt.close(fig)
                return None
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
        except Exception:
            plt.close(fig)
            return None

    @staticmethod
    def _compute_visible_segments(full_start, full_end, blocked_ranges):
        """计算 [full_start, full_end] 中未被 blocked_ranges 遮挡的连续段

        Args:
            full_start: 完整范围起点（含）
            full_end: 完整范围终点（含）
            blocked_ranges: list of (start, end) 被遮挡的范围

        Returns:
            list of (seg_start, seg_end) 可见段
        """
        if not blocked_ranges:
            return [(full_start, full_end)]

        sorted_blocks = sorted(blocked_ranges, key=lambda x: x[0])
        merged = [sorted_blocks[0]]
        for start, end in sorted_blocks[1:]:
            if start <= merged[-1][1] + 1:
                merged[-1] = (
                    merged[-1][0], max(merged[-1][1], end)
                )
            else:
                merged.append((start, end))

        segments = []
        current = full_start
        for block_start, block_end in merged:
            if current < block_start:
                segments.append((current, block_start - 1))
            current = max(current, block_end + 1)
        if current <= full_end:
            segments.append((current, full_end))

        return segments

    # ============= 委派方法（保持向后兼容） =============

    def _draw_translated_text(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._draw_translated_text(*args, **kwargs)

    def _draw_translated_table(self, *args, **kwargs):
        """委派给 PdfTableRenderer"""
        return self.table_renderer._draw_translated_table(*args, **kwargs)

    def _get_suitable_font(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._get_suitable_font(*args, **kwargs)

    def _get_system_fonts(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._get_system_fonts(*args, **kwargs)

    def _check_embedded_font_support(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._check_embedded_font_support(
            *args, **kwargs
        )

    def _check_font_support(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._check_font_support(*args, **kwargs)

    def _find_font_file(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._find_font_file(*args, **kwargs)

    def _contains_latex_formula(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._contains_latex_formula(*args, **kwargs)

    def _render_formula_image(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._render_formula_image(*args, **kwargs)

    def _render_mixed_text_formula_image(self, *args, **kwargs):
        """委派给 PdfTextRenderer"""
        return self.text_renderer._render_mixed_text_formula_image(
            *args, **kwargs
        )
