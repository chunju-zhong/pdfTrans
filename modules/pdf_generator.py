import fitz  # PyMuPDF
import os
import sys
import logging
import threading
from PIL import ImageFont

# 在模块级别设置 matplotlib 后端（仅调用一次）
import matplotlib
matplotlib.use('Agg')

# 配置日志
logger = logging.getLogger(__name__)

class PdfGenerator:
    """PDF生成类
    
    负责将翻译后的文本生成新的PDF文件，并尽量保留原始PDF的布局和格式。
    """
    
    def __init__(self):
        """初始化PdfGenerator对象"""
        # 字体目录
        self.fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
        
        # 字体缓存，避免重复加载
        self.font_cache = {}

        # 系统字体列表缓存（避免重复遍历文件系统）
        self._system_fonts_cache = None
        
        # 确保字体目录存在
        os.makedirs(self.fonts_dir, exist_ok=True)
        logger.info(f"PDF生成器初始化完成，字体目录: {self.fonts_dir}")
    
    def generate_pdf(self, original_pdf_path, translated_content, output_pdf_path, target_lang="zh", target_pages=None):
        """生成翻译后的PDF文件
        
        Args:
            original_pdf_path (str): 原始PDF文件路径
            translated_content (dict): 翻译后的内容
                - blocks (list): 每页的完整文本块列表 (翻译后的文本块)
                    - page_num (int): 页码
                    - text_blocks (list): TextBlock对象列表
                        - block_text (str): 完整文本块内容 (已翻译)
                        - block_bbox (tuple): 文本块位置 (x0, y0, x1, y1)
                        - block_no (int): 块编号
                        - block_type (int): 块类型
                        - font (str): 字体名称
                        - font_size (float): 字体大小
                        - color (int): 颜色值
                        - flags (int): 样式标记
                - tables (list): 翻译后的表格列表
            output_pdf_path (str): 输出PDF文件路径
            target_lang (str): 目标语言代码
        """
        logger.info(f"开始生成PDF，原始文件: {original_pdf_path}, 输出文件: {output_pdf_path}, 目标语言: {target_lang}")
        
        # 添加接收translated_content的日志，记录blocks信息
        logger.info(f"PDF生成器接收到的translated_content包含blocks信息: {('blocks' in translated_content)}")
        if 'blocks' in translated_content:
            total_blocks = sum(len(page.text_blocks) for page in translated_content['blocks'])
            logger.info(f"PDF生成器接收到的blocks信息: 总页数={len(translated_content['blocks'])}, 总blocks数={total_blocks}")
            # 显示所有页面的所有完整块内容
            for i, page_blocks in enumerate(translated_content['blocks']):
                # 直接使用PdfPage对象的text_blocks属性
                blocks_list = page_blocks.text_blocks
                block_count = len(blocks_list)
                logger.debug(f"PDF生成器 第 {i+1} 页有 {block_count} 个文本块")
                for j, block in enumerate(blocks_list):
                    # 直接使用TextBlock对象的属性
                    block_text = block.block_text
                    block_bbox = block.block_bbox
                    block_no = block.block_no
                    logger.debug(f"PDF生成器 第 {i+1} 页 文本块 {j+1}: '{block_text}' 位置: {block_bbox} 块编号: {block_no}")
        else:
            logger.warning("PDF生成器未接收到blocks信息，无法绘制翻译文本")
        
        if not os.path.exists(original_pdf_path):
            logger.error(f"原始PDF文件不存在: {original_pdf_path}")
            raise FileNotFoundError(f"原始PDF文件不存在: {original_pdf_path}")
        
        try:
            # 打开原始PDF
            with fitz.open(original_pdf_path) as original_doc:
                logger.info(f"成功打开原始PDF，总页数: {len(original_doc)}")
                
                # 创建新的PDF文档
                new_doc = fitz.open()
                try:
                    logger.info("创建新的PDF文档成功")

                    # 记录翻译内容概览
                    logger.info(f"翻译内容: 完整文本块 {len(translated_content.get('blocks', []))}, 表格 {len(translated_content.get('tables', []))}")

                    # 处理原始PDF的所有页面（包括无翻译内容的页面）
                    total_original_pages = len(original_doc)
                    logger.info(f"原始PDF总页数: {total_original_pages}")
                    
                    # 确定要输出的页面范围
                    if target_pages:
                        pages_to_output = [p for p in target_pages if 1 <= p <= total_original_pages]
                        logger.info(f"指定输出页码: {pages_to_output}")
                    else:
                        pages_to_output = list(range(1, total_original_pages + 1))
                    
                    # 构建页码到翻译内容的映射，方便查找
                    blocks_by_page = {}
                    for blocks_content in translated_content.get('blocks', []):
                        blocks_by_page[blocks_content.page_num] = blocks_content

                    tables_by_page = {}
                    for table in translated_content.get('tables', []):
                        tables_by_page.setdefault(table.page_num, []).append(table)

                    # 清空字体缓存，确保每次生成使用干净状态
                    self.font_cache = {}

                    for page_num in pages_to_output:
                        original_page_idx = page_num - 1

                        # 使用 insert_pdf 复制原始页面到新文档（比 show_pdf_page 更高效，资源引用更合理）
                        new_doc.insert_pdf(original_doc, from_page=original_page_idx, to_page=original_page_idx)
                        new_page = new_doc[-1]  # 获取刚插入的页面

                        # 获取当前页的翻译内容
                        page_translated_blocks = blocks_by_page.get(page_num)

                        if page_translated_blocks and page_translated_blocks.text_blocks:
                            blocks_count = len(page_translated_blocks.text_blocks)
                            logger.info(f"第 {page_num} 页有 {blocks_count} 个完整文本块")
                            self._draw_translated_text(new_page, page_translated_blocks, target_lang)
                            logger.info(f"第 {page_num} 页绘制完成")
                        else:
                            logger.info(f"第 {page_num} 页无翻译文本块，保留原始页面")

                        # 处理表格（如果有）
                        page_tables = tables_by_page.get(page_num, [])
                        if page_tables:
                            logger.info(f"第 {page_num} 页有 {len(page_tables)} 个表格需要处理")
                            for i, table in enumerate(page_tables):
                                self._draw_translated_table(new_page, table, target_lang)
                                logger.info(f"第 {page_num} 页表格 {i+1} 绘制完成")

                    # 保存新PDF
                    logger.info(f"开始保存新PDF: {output_pdf_path}")

                    # 在保存文档之前获取总页数
                    total_pages = len(new_doc)

                    # 保存文档（启用压缩优化：deflate压缩流、garbage清理未引用对象、clean清理冗余内容）
                    new_doc.save(output_pdf_path, deflate=True, garbage=4, clean=True)
                finally:
                    new_doc.close()
                
                # 使用预存的总页数记录日志，避免在文档关闭后访问
                logger.info(f"PDF生成完成，输出文件: {output_pdf_path}, 总页数: {total_pages}")
                
        except Exception as e:
            logger.error(f"生成PDF时出错: {str(e)}", exc_info=True)
            raise Exception(f"生成PDF时出错: {str(e)}")
    
    # 类级别缓存：LaTeX 可用性检测结果
    _latex_available = None
    _latex_lock = threading.Lock()

    @classmethod
    def _check_latex_available(cls):
        """检测系统是否安装了 LaTeX 引擎（用于 usetex 渲染，线程安全）"""
        with cls._latex_lock:
            # double-check locking
            if cls._latex_available is not None:
                return cls._latex_available
            import subprocess
            import glob as glob_module

            # Step 1: Try PATH detection
            try:
                result = subprocess.run(['latex', '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    cls._latex_available = True
                    logger.info("LaTeX 可用性检测: 可用 (PATH)")
                    return cls._latex_available
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            # Step 2: Probe common LaTeX installation paths by platform
            common_paths = []

            if sys.platform == 'darwin':
                common_paths = [
                    '/Library/TeX/texbin/latex',                      # MacTeX default
                    '/opt/homebrew/bin/latex',                        # Homebrew
                ]
                common_paths.extend(
                    sorted(glob_module.glob('/usr/local/texlive/*/bin/universal-darwin/latex'), reverse=True)
                )
            elif sys.platform == 'linux':
                common_paths = [
                    '/usr/bin/latex',
                    '/usr/local/bin/latex',
                ]
                common_paths.extend(
                    sorted(glob_module.glob('/usr/local/texlive/*/bin/x86_64-linux/latex'), reverse=True)
                )
                common_paths.extend(
                    sorted(glob_module.glob('/usr/local/texlive/*/bin/aarch64-linux/latex'), reverse=True)
                )
            elif sys.platform == 'win32':
                common_paths = [
                    r'C:\Program Files\MiKTeX\miktex\bin\x64\latex.exe',
                ]
                common_paths.extend(
                    sorted(glob_module.glob('C:/texlive/*/bin/windows/latex.exe'), reverse=True)
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
                    logger.info(f"LaTeX 可用性检测: 可用 ({found_path})，已将 {latex_dir} 添加到 PATH")
                else:
                    logger.info(f"LaTeX 可用性检测: 可用 ({found_path})，PATH 已包含 {latex_dir}")
                cls._latex_available = True
            else:
                cls._latex_available = False
                logger.info("LaTeX 可用性检测: 不可用")

            return cls._latex_available

    @staticmethod
    def _setup_matplotlib_cjk():
        """配置 matplotlib 的 CJK 字体支持（统一入口，避免重复配置）"""
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'STHeiti', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

    @staticmethod
    def _preprocess_latex_for_mathtext(latex):
        """预处理 LaTeX，去除 mathtext 不支持的命令，用于降级渲染

        处理步骤：
        1. 将 \\(...\\) → $...$，\\[...\\] → $$...$$（mathtext 不识别 \\(\\) \\[\\] 定界符）
        2. 将 \\text{content} → content, \\mathrm{content} → content 等
        3. 去除 \\begin{env}...\\end{env} 环境包装（aligned, gathered, cases 等）
        4. 希腊字母替换（mathtext 不支持 \\alpha 等）
        5. 数学符号替换
        6. 去除 \\left 和 \\right 命令
        """
        import re
        # 转换 LaTeX 定界符为 mathtext 支持的格式
        latex = re.sub(r'\\\(', '$', latex)
        latex = re.sub(r'\\\)', '$', latex)
        latex = re.sub(r'\\\[', '$$', latex)
        latex = re.sub(r'\\\]', '$$', latex)
        # 将 $$...$$ 转换为 $...$（mathtext display math 不支持与文本混排）
        latex = re.sub(r'\$\$', '$', latex)
        # 去除数学字体命令
        prev = None
        while prev != latex:
            prev = latex
            latex = re.sub(
                r'\\(?:text|mathrm|mathbf|mathit|mathsf|mathtt|textbf|textrm)\{([^}]*)\}',
                r'\1', latex
            )
        # 去除 \begin{env}...\end{env} 环境（aligned, gathered, cases 等）
        # 必须在数学符号替换（含 \& → &）之前，否则 \\& 中的 \& 被替换导致 \\ 变成 \
        # 使用反向引用确保 \begin 和 \end 的环境名一致
        prev = None
        while prev != latex:
            prev = latex
            latex = re.sub(
                r'\\begin\{(aligned|gathered|cases|equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}',
                lambda m: re.sub(r'\\\\', ' ', m.group(2)).replace('&', ''),
                latex,
                flags=re.DOTALL,
            )
        # 兜底：仅处理残留的行分隔符 \\ 和对齐标记 &
        # （当 _detect_formula 已去除 \begin/\end 时，上面的正则不匹配）
        # 只替换作为行分隔符的 \\（后跟 & 或另一个 \\ 或字符串末尾）
        latex = re.sub(r'\\\\(?=\s*&|\\\\|$)', ' ', latex)
        # 只替换作为对齐标记的 &（两侧有非空白内容）
        latex = re.sub(r'(?<=\S)\s*&\s*(?=\S)', ' ', latex)
        # 希腊字母替换
        greek_letters = {
            r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
            r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
            r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
            r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
            r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
            r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
            r'\Alpha': 'Α', r'\Beta': 'Β', r'\Gamma': 'Γ', r'\Delta': 'Δ',
            r'\Epsilon': 'Ε', r'\Zeta': 'Ζ', r'\Eta': 'Η', r'\Theta': 'Θ',
            r'\Iota': 'Ι', r'\Kappa': 'Κ', r'\Lambda': 'Λ', r'\Mu': 'Μ',
            r'\Nu': 'Ν', r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Rho': 'Ρ',
            r'\Sigma': 'Σ', r'\Tau': 'Τ', r'\Upsilon': 'Υ', r'\Phi': 'Φ',
            r'\Chi': 'Χ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
        }
        for cmd, char in greek_letters.items():
            latex = latex.replace(cmd, char)
        # 数学符号替换
        math_symbols = {
            r'\circ': '°', r'\cdot': '·', r'\times': '×', r'\div': '÷',
            r'\pm': '±', r'\leq': '≤', r'\geq': '≥', r'\neq': '≠',
            r'\approx': '≈', r'\infty': '∞', r'\partial': '∂',
            r'\nabla': '∇', r'\forall': '∀', r'\exists': '∃',
            r'\in': '∈', r'\notin': '∉', r'\subset': '⊂', r'\supset': '⊃',
            r'\cup': '∪', r'\cap': '∩', r'\emptyset': '∅',
            r'\%': '%', r'\&': '&', r'\#': '#', r'\$': '$',
        }
        for cmd, char in math_symbols.items():
            latex = latex.replace(cmd, char)
        # 去除 \left 和 \right 命令
        latex = re.sub(r'\\left\b', '', latex)
        latex = re.sub(r'\\right\b', '', latex)
        return latex

    def _render_formula_image(self, latex, fontsize=12):
        import matplotlib.pyplot as plt
        import io

        # 配置 CJK 字体
        self._setup_matplotlib_cjk()

        # 优先使用 usetex（支持完整 LaTeX 命令如 \text{}）
        if self._check_latex_available():
            try:
                plt.rcParams['text.usetex'] = True
                # 加载 amsmath 宏包以支持 \begin{aligned} 等环境
                plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
                fig, ax = plt.subplots(figsize=(0.01, 0.01))
                ax.axis('off')
                text = ax.text(0, 0, f'${latex}$', fontsize=fontsize, ha='left', va='bottom')
                fig.canvas.draw()
                bbox = text.get_window_extent()
                fig.set_size_inches(bbox.width / fig.dpi + 0.1, bbox.height / fig.dpi + 0.05)
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.02, transparent=True)
                plt.close(fig)
                buf.seek(0)
                return buf
            except Exception as e:
                logger.warning(f'usetex 渲染失败: {e}，降级为 mathtext')
                plt.rcParams['text.usetex'] = False

        # 降级1：用原始 LaTeX 尝试 mathtext 渲染
        try:
            buf = self._try_mathtext_render(latex, fontsize)
            if buf:
                return buf
        except Exception:
            pass

        # 降级2：预处理 LaTeX 后用 mathtext 渲染
        processed = self._preprocess_latex_for_mathtext(latex)
        try:
            buf = self._try_mathtext_render(processed, fontsize)
            if buf:
                return buf
        except Exception:
            pass

        # 降级3：返回 None 表示渲染失败
        logger.warning(f'公式渲染完全失败: {latex[:50]}...')
        return None

    def _try_mathtext_render(self, latex, fontsize=12, is_mixed=False):
        """尝试用 mathtext 渲染公式，成功返回 BytesIO，失败返回 None

        Args:
            latex: LaTeX 文本
            fontsize: 字体大小
            is_mixed: 是否为混合文本（中文+公式），混合文本不包裹 $...$
        """
        import matplotlib.pyplot as plt
        import io

        # 配置 CJK 字体
        self._setup_matplotlib_cjk()

        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        ax.axis('off')
        try:
            if is_mixed:
                # 混合文本：文本本身包含 $...$，不需要额外包裹
                display_text = latex
            else:
                display_text = f'${latex}$'
            text = ax.text(0, 0, display_text, fontsize=fontsize, ha='left', va='bottom')
            fig.canvas.draw()
            bbox = text.get_window_extent()
            if bbox.width < 1 or bbox.height < 1:
                plt.close(fig)
                return None
            fig.set_size_inches(bbox.width / fig.dpi + 0.1, bbox.height / fig.dpi + 0.05)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.02, transparent=True)
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception:
            plt.close(fig)
            return None

    @staticmethod
    def _contains_latex_formula(text):
        """检测文本是否包含 LaTeX 公式片段（$...$、$$...$$、\\(...\\)、\\[...\\]）"""
        import re
        # 检测 $...$ （非 $$...$$）
        if re.search(r'(?<!\$)\$(?!\$).+?\$(?!\$)', text):
            return True
        # 检测 $$...$$
        if re.search(r'\$\$.+?\$\$', text):
            return True
        # 检测 \(...\)
        if re.search(r'\\\(.*?\\\)', text):
            return True
        # 检测 \[...\]
        if re.search(r'\\\[.*?\\\]', text):
            return True
        return False

    def _render_mixed_text_formula_image(self, text, fontsize=12):
        """将混合文本（中文+LaTeX公式）渲染为图片

        使用 matplotlib 的 mathtext 功能，在文本中嵌入 $...$ 公式。
        先预处理 LaTeX 命令，然后整体渲染。
        """
        import matplotlib.pyplot as plt
        import io

        # 配置 CJK 字体
        self._setup_matplotlib_cjk()

        # 预处理 LaTeX 命令
        processed = self._preprocess_latex_for_mathtext(text)

        # 如果有 usetex，优先使用
        if self._check_latex_available():
            try:
                plt.rcParams['text.usetex'] = True
                plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
                fig, ax = plt.subplots(figsize=(0.01, 0.01))
                ax.axis('off')
                # usetex 模式下需要用 LaTeX 语法
                text_obj = ax.text(0, 0, processed, fontsize=fontsize, ha='left', va='bottom')
                fig.canvas.draw()
                bbox = text_obj.get_window_extent()
                if bbox.width < 1 or bbox.height < 1:
                    plt.close(fig)
                    plt.rcParams['text.usetex'] = False
                    raise ValueError("rendered size too small")
                fig.set_size_inches(bbox.width / fig.dpi + 0.1, bbox.height / fig.dpi + 0.05)
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', pad_inches=0.02, transparent=True)
                plt.close(fig)
                buf.seek(0)
                return buf
            except Exception as e:
                logger.warning(f'混合文本 usetex 渲染失败: {e}，降级为 mathtext')
                plt.rcParams['text.usetex'] = False

        # mathtext 渲染
        try:
            buf = self._try_mathtext_render(processed, fontsize, is_mixed=True)
            if buf:
                return buf
        except Exception:
            pass

        logger.warning(f'混合公式文本渲染失败: {text[:50]}...')
        return None

    def _draw_translated_text(self, page, translated_blocks, target_lang="zh"):
        """在页面上绘制翻译后的文本，使用块级关联实现样式保留
        
        核心逻辑：
        1. 第一遍遍历：收集所有需要 redact 的区域，添加 redaction 标注
        2. 执行 apply_redactions 一次性删除原文（比白色矩形遮盖更彻底，减少PDF体积）
        3. 第二遍遍历：按原文样式（字体、大小、颜色、位置）渲染翻译文本
        
        Args:
            page (fitz.Page): PDF页面对象
            translated_blocks (PdfPage): 当前页的翻译文本块
                - page_num (int): 页码
                - text_blocks (list): TextBlock对象列表 (已翻译的完整文本块)
            target_lang (str): 目标语言代码
        """
        # 直接使用PdfPage对象的text_blocks属性
        full_text_blocks = translated_blocks.text_blocks
        total_blocks = len(full_text_blocks)
        
        logger.info(f"开始绘制翻译文本V2，共 {total_blocks} 个完整文本块")
        
        # ========== 第一遍：添加 redaction 标注，标记需要删除的原文区域 ==========
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
            page.add_redact_annot(bg_rect, fill=None)
            logger.debug(f"添加 redaction 标注，区域: {bg_rect} (h_padding={h_padding:.1f}, v_padding={v_padding:.1f})")

        # 一次性执行 redaction，真正删除原文（不删除图片）
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        logger.info(f"已执行 redaction 删除原文，共处理 {total_blocks} 个文本块区域")

        # ========== 第二遍：插入翻译文本 ==========
        for block_idx, full_block in enumerate(full_text_blocks):
            logger.info(f"处理完整文本块 {block_idx+1}/{total_blocks}")
            
            # 直接使用TextBlock对象的属性
            translated_text = full_block.block_text
            block_bbox = full_block.block_bbox
            
            logger.info(f"翻译文本: '{translated_text}' (共 {len(translated_text)} 字符)")
            logger.info(f"文本块位置: {block_bbox}")
            
            # 直接使用TextBlock对象自带的样式信息
            original_font = full_block.font
            original_font_size = full_block.font_size
            color = full_block.color
            bold = full_block.bold
            italic = full_block.italic

            # 字体大小为0时（LLM OCR等无样式信息的TextBlock），根据bbox估算
            bbox_height = block_bbox[3] - block_bbox[1]
            if original_font_size == 0:
                if bbox_height > 0:
                    original_font_size = min(bbox_height * 0.75, 36)
                    logger.info(f"字体大小为0，根据bbox高度估算: {original_font_size:.1f}pt (bbox_height={bbox_height:.1f})")
                else:
                    original_font_size = 12
                    logger.info(f"字体大小为0且bbox高度为0，使用默认字体大小: {original_font_size:.1f}pt")

            logger.info(f"使用文本块自带样式: 字体='{original_font}', 大小={original_font_size}, 粗体={bold}, 斜体={italic}")

            # 计算原文行高倍率，确保翻译文本行高与原文一致
            if original_font_size > 0 and bbox_height > 0:
                # 保守估算：假设原文只有1行（适用于标题等短文本）
                # 对于长文本，bbox_height 通常足够容纳多行
                estimated_lines = max(1, round(bbox_height / (original_font_size * 1.2)))
                
                # 计算行高倍率
                original_lineheight = bbox_height / (original_font_size * estimated_lines)
                
                # 上下限保护：行高倍率在合理范围内
                original_lineheight = max(1.0, min(original_lineheight, 2.0))
                
                logger.info(f"原文行高倍率: {original_lineheight:.3f} (bbox高度={bbox_height:.1f}, 字体大小={original_font_size:.1f}, 估算行数={estimated_lines})")
            else:
                original_lineheight = 1.2  # 默认值
                estimated_lines = 0

            # 颜色转换：ARGB(0xAARRGGBB) 和 RGB(0xRRGGBB) 的 R/G/B 位位置相同
            # 统一取低 24 位后提取，避免冗余分支
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            logger.debug(f"颜色: {color:#x} -> R={r}, G={g}, B={b}")
            
            # 转换为0-1范围
            rgb_color = (r / 255.0, g / 255.0, b / 255.0)
            logger.debug(f"转换后RGB: {rgb_color}")
            
            # 确保文本颜色不是透明或白色（与背景冲突）
            grayscale = 0.299 * r + 0.587 * g + 0.114 * b
            logger.debug(f"灰度值: {grayscale}")
            
            if grayscale > 200:  # 接近白色，改为黑色
                rgb_color = (0, 0, 0)  # 确保文本可见
                logger.info("颜色接近白色，自动改为黑色")
            
            # 获取适合目标语言的字体
            suitable_font = self._get_suitable_font(page, original_font, target_lang)
            logger.info(f"适合的字体: 原字体='{original_font}', 目标语言='{target_lang}', 选择='{suitable_font}'")
            
            # 创建文本框
            rect = fitz.Rect(block_bbox[0], block_bbox[1], block_bbox[2], block_bbox[3])
            logger.debug(f"文本框尺寸: {rect.width}x{rect.height}")

            if getattr(full_block, 'is_formula', False) and full_block.block_text:
                try:
                    img_buf = self._render_formula_image(full_block.block_text, fontsize=original_font_size)
                    if img_buf is not None:
                        page.insert_image(rect, stream=img_buf.getvalue())
                        continue
                    else:
                        logger.warning('公式渲染返回 None，降级为文本')
                except Exception as e:
                    logger.warning(f'公式渲染异常，降级为文本: {e}')

            # 检测非公式文本块中是否包含 LaTeX 公式片段
            if not getattr(full_block, 'is_formula', False) and self._contains_latex_formula(translated_text):
                try:
                    img_buf = self._render_mixed_text_formula_image(translated_text, fontsize=original_font_size)
                    if img_buf is not None:
                        page.insert_image(rect, stream=img_buf.getvalue())
                        logger.info(f'混合公式文本渲染成功: {translated_text[:50]}...')
                        continue
                    else:
                        logger.warning('混合公式文本渲染返回 None，降级为纯文本')
                except Exception as e:
                    logger.warning(f'混合公式文本渲染异常，降级为文本: {e}')

            # 使用文本块的对齐方式
            alignment = getattr(full_block, 'alignment', 0)
            logger.info(f"使用对齐方式: {alignment} (0=左对齐, 1=居中, 2=右对齐)")
            
            # 不再使用字体回退列表，只使用适合的字体
            max_attempts = 5
            success = False
            current_rect = rect

            # 记录文本渲染尝试的初始参数
            logger.info(f"[文本渲染] 开始尝试渲染，文本框尺寸: 宽度={current_rect.width:.1f}, 高度={current_rect.height:.1f}")
            logger.info(f"[文本渲染] 原始字体大小: {original_font_size:.1f}, 行高倍率: {original_lineheight:.3f}")
            logger.info(f"[文本渲染] 文本内容长度: {len(translated_text)} 字符")

            for attempt in range(1, max_attempts + 1):
                try:
                    # 计算当前尝试的字体大小调整策略
                    # 从原始字体大小开始，逐步缩小以适应文本框
                    if attempt == 1:
                        adjusted_font_size = original_font_size
                    else:
                        reduction_factor = (attempt - 1) * 0.1
                        adjusted_font_size = original_font_size * (1 - reduction_factor)
                        adjusted_font_size = max(adjusted_font_size, original_font_size * 0.7)  # 不小于原大小的70%

                    logger.info(f"[文本渲染] 第 {attempt} 次尝试: 字体大小={adjusted_font_size:.1f} (原始={original_font_size:.1f}, 调整比例={(adjusted_font_size/original_font_size):.0%})")
                    logger.info(f"[文本渲染] 第 {attempt} 次尝试: 文本框尺寸=宽度={current_rect.width:.1f}, 高度={current_rect.height:.1f}, 行高倍率={original_lineheight:.3f}")

                    # 尝试绘制文本
                    result = page.insert_textbox(
                        current_rect,
                        translated_text,
                        fontname=suitable_font,
                        fontsize=adjusted_font_size,
                        color=rgb_color,
                        align=alignment,
                        lineheight=original_lineheight
                    )

                    logger.info(f"[文本渲染] 第 {attempt} 次尝试结果: 返回值={result}, 成功={result >= 0}")

                    if result >= 0:
                        logger.info(f"[OK] 文本渲染成功，插入了 {result} 个字符，使用字体大小: {adjusted_font_size}，文本框大小: {current_rect}")
                        logger.debug(f"渲染文本内容: '{translated_text[:100]}...' (完整长度={len(translated_text)})")
                        success = True
                        break
                    
                    # 文本溢出，需要调整
                    logger.warning(f"[WARN] 文本溢出，返回值: {result}，当前字体大小: {adjusted_font_size}，文本框: {current_rect}")
                    logger.warning(f"溢出文本: '{translated_text[:100]}...' (完整长度={len(translated_text)})")
                except Exception as e:
                    logger.warning(f"[FAIL] 绘制失败: {e}")
                    break
            
            if not success:
                min_font_size = original_font_size * 0.5
                for font_ratio in [0.6, 0.5]:
                    adjusted_font_size = original_font_size * font_ratio
                    try:
                        result = page.insert_textbox(
                            current_rect,
                            translated_text,
                            fontname=suitable_font,
                            fontsize=adjusted_font_size,
                            color=rgb_color,
                            align=alignment,
                            lineheight=original_lineheight
                        )
                        if result >= 0:
                            logger.info(f"[OK] 缩小字体到{font_ratio*100:.0f}%后渲染成功，字体大小: {adjusted_font_size}")
                            success = True
                            break
                        logger.warning(f"缩小字体到{font_ratio*100:.0f}%仍溢出，继续尝试")
                    except Exception as e:
                        logger.warning(f"缩小字体到{font_ratio*100:.0f}%绘制失败: {e}")
                        break

            if not success:
                # 在截断之前，先尝试调整行高倍率
                logger.info(f"[行高调整] 尝试调整行高倍率以避免截断")
                for lineheight_attempt in [1.5, 1.8, 2.0]:
                    logger.info(f"[行高调整] 尝试行高倍率={lineheight_attempt}")
                    try:
                        result = page.insert_textbox(
                            current_rect,
                            translated_text,
                            fontname=suitable_font,
                            fontsize=min_font_size,
                            color=rgb_color,
                            align=alignment,
                            lineheight=lineheight_attempt
                        )
                        if result >= 0:
                            logger.info(f"[OK] 调整行高倍率到{lineheight_attempt}后渲染成功")
                            success = True
                            break
                        logger.debug(f"行高倍率{lineheight_attempt}仍溢出，继续尝试")
                    except Exception as e:
                        logger.warning(f"行高调整尝试失败: {e}")
                        break

            if not success:
                logger.warning(f"[智能截断] 所有尝试失败，开始智能截断")
                logger.warning(f"[智能截断] 文本框尺寸: 宽度={current_rect.width:.1f}, 高度={current_rect.height:.1f}")
                logger.warning(f"[智能截断] 使用最小字体大小: {min_font_size:.1f}, 行高倍率: {original_lineheight:.3f}")

                # 按单词边界截断（适用于有空格分隔的文本）
                words = translated_text.split()
                word_truncation_tried = False
                if len(words) > 1:
                    word_truncation_tried = True
                    for word_count in range(len(words) - 1, max(1, len(words) // 10), -1):
                        truncated_text = ' '.join(words[:word_count]) + '...'
                        logger.info(f"[智能截断] 尝试保留{word_count}个单词: '{truncated_text[:50]}...'")
                        try:
                            result = page.insert_textbox(
                                current_rect,
                                truncated_text,
                                fontname=suitable_font,
                                fontsize=min_font_size,
                                color=rgb_color,
                                align=alignment,
                                lineheight=original_lineheight
                            )
                            if result >= 0:
                                logger.warning(
                                    f"[智能截断成功] 截断文本后渲染成功: 原始单词数={len(words)}, "
                                    f"截断后单词数={word_count}, 截断比例={word_count/len(words):.0%}, "
                                    f"字体大小={min_font_size:.1f}, 文本框尺寸=宽度={current_rect.width:.1f}, 高度={current_rect.height:.1f}"
                                )
                                success = True
                                break
                        except Exception as e:
                            logger.warning(f"智能截断绘制失败: {e}")
                            break

                # CJK 文本按字符数截断降级（中文/日文/韩文无空格分隔，split()返回单元素）
                if not success and not word_truncation_tried:
                    total_chars = len(translated_text)
                    # 保留至少30%字符，逐步减少尝试
                    for char_ratio in [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]:
                        keep_chars = max(1, int(total_chars * char_ratio))
                        truncated_text = translated_text[:keep_chars] + '...'
                        logger.info(f"[CJK截断] 尝试保留{keep_chars}/{total_chars}字符({char_ratio:.0%}): '{truncated_text[:50]}...'")
                        try:
                            result = page.insert_textbox(
                                current_rect,
                                truncated_text,
                                fontname=suitable_font,
                                fontsize=min_font_size,
                                color=rgb_color,
                                align=alignment,
                                lineheight=original_lineheight
                            )
                            if result >= 0:
                                logger.warning(
                                    f"[CJK截断成功] 截断后渲染成功: 原始字符数={total_chars}, "
                                    f"截断后字符数={keep_chars}, 截断比例={char_ratio:.0%}"
                                )
                                success = True
                                break
                        except Exception as e:
                            logger.warning(f"CJK截断绘制失败: {e}")
                            break
                
                # 如果智能截断也失败，回退到机械截断（但限制最小比例）
                if not success:
                    logger.warning(f"[机械截断] 智能截断失败，回退到机械截断")
                    truncated_text = translated_text
                    ellipsis = "..."
                    max_truncation_attempts = 10
                    for trunc_attempt in range(1, max_truncation_attempts + 1):
                        ratio = 1.0 - trunc_attempt * 0.1
                        if ratio < 0.3:  # 至少保留30%
                            logger.warning(f"[机械截断] 达到最小比例限制(30%)，停止截断")
                            break
                        truncated_text = translated_text[:max(1, int(len(translated_text) * ratio))]
                        if not truncated_text.endswith(ellipsis):
                            truncated_text = truncated_text.rstrip() + ellipsis
                        
                        # 记录截断尝试的详细信息
                        logger.info(f"[机械截断] 第 {trunc_attempt} 次截断尝试: 截断比例={ratio:.0%}")
                        logger.info(f"[机械截断] 截断后文本预览: '{truncated_text[:50]}...' (长度={len(truncated_text)})")
                        logger.info(f"[机械截断] 文本框尺寸: 宽度={current_rect.width:.1f}, 高度={current_rect.height:.1f}, 字体大小={min_font_size:.1f}")
                        
                        try:
                            result = page.insert_textbox(
                                current_rect,
                                truncated_text,
                                fontname=suitable_font,
                                fontsize=min_font_size,
                                color=rgb_color,
                                align=alignment,
                                lineheight=original_lineheight
                            )
                            if result >= 0:
                                logger.warning(
                                    f"[机械截断成功] 截断文本后渲染成功: 原始长度={len(translated_text)}, "
                                    f"截断后长度={len(truncated_text)}, 截断比例={ratio:.0%}, "
                                    f"字体大小={min_font_size:.1f}, 文本框尺寸=宽度={current_rect.width:.1f}, 高度={current_rect.height:.1f}, "
                                    f"行高倍率={original_lineheight:.3f}, 截断后文本预览='{truncated_text[:50]}...'"
                                )
                                success = True
                                break
                            logger.debug(f"截断到{ratio:.0%}仍溢出，继续截断")
                        except Exception as e:
                            logger.warning(f"截断文本绘制失败: {e}")
                            break

            if not success:
                logger.warning(f"所有尝试（含截断）均失败，跳过文本块绘制: '{translated_text[:50]}...'")
        
        logger.info("所有翻译文本绘制完成")
    
    def _get_suitable_font(self, page, original_font, target_lang):
        """获取适合目标语言的字体

        使用 font_cache 缓存字体查找结果，避免重复的文件系统查找和兼容性检测。
        缓存 key 为 (original_font, target_lang)，value 为 (fontname, fontfile)。

        Args:
            page (fitz.Page): PDF页面对象
            original_font (str): 原始字体名称
            target_lang (str): 目标语言代码
            
        Returns:
            str: 适合的字体名称
        
        Raises:
            ValueError: 当找不到适合目标语言的字体时抛出
        """
        logger.info(f"获取适合字体: 原字体='{original_font}', 目标语言='{target_lang}'")

        # 检查缓存
        cache_key = (original_font, target_lang)
        if cache_key in self.font_cache:
            cached_fontname, cached_fontfile = self.font_cache[cache_key]
            logger.info(f"字体缓存命中: fontname='{cached_fontname}', fontfile='{cached_fontfile}'")
            # 缓存命中时仍需调用 insert_font 确保当前页面引用了该字体
            try:
                if cached_fontfile:
                    page.insert_font(fontname=cached_fontname, fontfile=cached_fontfile)
                else:
                    page.insert_font(fontname=cached_fontname, fontfile=None)
            except Exception as e:
                logger.warning(f"缓存字体插入当前页面失败，将重新查找: {e}")
                # 插入失败则从缓存移除，继续正常查找
                del self.font_cache[cache_key]
            else:
                return cached_fontname
        
        # 1. 检查是否有预先加载的字体
        if original_font:
            try:
                logger.info(f"尝试使用原始字体 '{original_font}'")
                page.insert_font(fontname=original_font, fontfile=None)
                # 检查原始字体是否支持目标语言字符
                if self._check_embedded_font_support(page, original_font, target_lang):
                    logger.info(f"原始字体 '{original_font}' 支持目标语言 '{target_lang}'，直接使用")
                    self.font_cache[cache_key] = (original_font, None)
                    return original_font
                else:
                    logger.info(f"原始字体 '{original_font}' 不支持目标语言 '{target_lang}'，跳过")
            except Exception as e:
                logger.warning(f"原始字体 '{original_font}' 插入失败: {e}")
        
        # 2. 从系统获取可用字体列表
        system_font_paths = self._get_system_fonts()
        logger.info(f"系统字体列表获取完成，共 {len(system_font_paths)} 种字体")
        
        # 3. 从系统字体中选择支持目标语言的字体
        if system_font_paths:
            logger.info(f"开始从系统字体中选择支持 '{target_lang}' 的字体")
            
            # 特殊处理Arial Unicode.ttf，它支持多种语言
            arial_unicode_found = False
            for font_path in system_font_paths:
                if 'Arial Unicode.ttf' in font_path:
                    arial_unicode_found = True
                    try:
                        logger.info(f"找到Arial Unicode字体: {font_path}")
                        # 使用自定义短名称插入字体
                        fontname = "arialuni"
                        page.insert_font(fontname=fontname, fontfile=font_path)
                        logger.info(f"成功使用Arial Unicode字体作为 '{fontname}'")
                        self.font_cache[cache_key] = (fontname, font_path)
                        return fontname
                    except Exception as e:
                        logger.error(f"Arial Unicode字体插入失败: {e}")
                        continue
            
            if not arial_unicode_found:
                logger.info("未找到Arial Unicode字体，继续搜索其他字体")
            
            # 遍历所有系统字体路径
            compatible_fonts = []
            for font_path in system_font_paths:
                try:
                    # 检查字体是否支持目标语言
                    if self._check_font_support(font_path, target_lang):
                        compatible_fonts.append(font_path)
                        logger.debug(f"字体 '{os.path.basename(font_path)}' 支持目标语言 '{target_lang}'")
                except Exception as e:
                    logger.debug(f"检查字体 '{os.path.basename(font_path)}' 时出错: {e}")
            
            logger.info(f"找到 {len(compatible_fonts)} 种支持 '{target_lang}' 的字体")
            
            # 尝试使用找到的兼容字体
            for font_path in compatible_fonts:
                try:
                    logger.info(f"尝试使用兼容字体: {font_path}")
                    # 创建自定义短名称，去除空格和特殊字符
                    font_filename = os.path.basename(font_path)
                    fontname = os.path.splitext(font_filename)[0].replace(' ', '_')
                    fontname = ''.join(c for c in fontname if c.isalnum() or c == '_')
                    
                    # 尝试插入字体
                    page.insert_font(fontname=fontname, fontfile=font_path)
                    logger.info(f"成功使用系统字体 '{font_filename}' 作为 '{fontname}'")
                    self.font_cache[cache_key] = (fontname, font_path)
                    return fontname
                except Exception as e:
                    logger.warning(f"系统字体 '{os.path.basename(font_path)}' 插入失败: {e}")
                    continue
        
        # 4. 无法找到任何适合的字体，抛出异常
        error_msg = f"无法找到适合目标语言 '{target_lang}' 的字体。请安装支持该语言的字体，例如Arial Unicode或其他支持{target_lang}语言的字体。"
        logger.error(error_msg)
        raise ValueError(error_msg)
    

    
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

        # 合并重叠的遮挡范围
        sorted_blocks = sorted(blocked_ranges, key=lambda x: x[0])
        merged = [sorted_blocks[0]]
        for start, end in sorted_blocks[1:]:
            if start <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        # 计算可见段
        segments = []
        current = full_start
        for block_start, block_end in merged:
            if current < block_start:
                segments.append((current, block_start - 1))
            current = max(current, block_end + 1)
        if current <= full_end:
            segments.append((current, full_end))

        return segments

    def _draw_translated_table(self, page, table, target_lang="zh"):
        """在页面上绘制翻译后的表格

        Args:
            page (fitz.Page): PDF页面对象
            table: PdfTable对象
            target_lang (str): 目标语言代码
        """
        # 使用cells属性
        table_cells = table.cells
        logger.info(f"[表格绘制] 接收到表格数据: 页码={table.page_num}, 表格索引={table.table_idx}, cells行数={len(table_cells) if table_cells else 0}")

        if not table_cells:
            logger.warning("[表格绘制] 表格数据为空，跳过绘制")
            return

        # 记录表格所有单元格的内容，用于诊断
        logger.info("[表格绘制] 表格所有单元格内容预览:")
        for row_idx, row in enumerate(table_cells):
            for col_idx, cell in enumerate(row):
                if cell and hasattr(cell, 'text') and cell.text:
                    text_preview = cell.text[:30] + '...' if len(cell.text) > 30 else cell.text
                    logger.info(f"[表格绘制] 单元格 ({row_idx},{col_idx}): '{text_preview}'")

        n_rows = len(table_cells)
        n_cols = max(len(row) for row in table_cells) if table_cells else 0
        logger.info(f"[表格绘制] 开始绘制表格，共 {n_rows} 行 {n_cols} 列")

        # 获取表格边界框信息
        table_bbox = table.bbox
        logger.info(f"[TABLE_DIAG] 表格边界框: {table_bbox}")

        # 获取行高和列宽信息
        row_heights = table.row_heights
        col_widths = table.col_widths
        logger.info(f"行高: {row_heights}")
        logger.info(f"列宽: {col_widths}")

        if table_bbox:
            table_x0, table_y0, table_x1, table_y1 = table_bbox
        else:
            # 无有效 bbox 时使用页面区域作为 fallback
            table_x0, table_y0 = 50, 50
            table_x1, table_y1 = page.rect.width - 50, page.rect.height - 50
            logger.warning(f"[表格绘制] 表格无有效 bbox，使用页面区域 fallback: ({table_x0},{table_y0},{table_x1},{table_y1})")

        # 获取适合目标语言的字体
        suitable_font = self._get_suitable_font(page, 'GoogleSansText-Regular', target_lang)
        logger.info(f"适合的字体: 目标语言='{target_lang}', 选择='{suitable_font}'")

        # ========== 第一遍：添加 redaction 标注，标记需要删除的单元格原文区域 ==========
        for i, row in enumerate(table_cells):
            for j, cell in enumerate(row):
                if cell is None:
                    continue

                # 获取单元格 bbox
                if isinstance(cell, dict):
                    cell_bbox = cell.get('bbox')
                elif hasattr(cell, 'bbox'):
                    cell_bbox = cell.bbox
                else:
                    cell_bbox = None

                # 计算单元格矩形区域
                if cell_bbox and not (cell_bbox[0] == 0 and cell_bbox[1] == 0 and cell_bbox[2] == 0 and cell_bbox[3] == 0):
                    x0, y0, x1, y1 = cell_bbox
                    if x1 - x0 <= 0 or y1 - y0 <= 0:
                        cell_bbox = None

                if cell_bbox is None:
                    if table_bbox and row_heights and col_widths:
                        x0 = table_x0 + sum(col_widths[:j])
                        y0 = table_y0 + sum(row_heights[:i])
                        row_span = getattr(cell, 'row_span', 1) if hasattr(cell, 'row_span') else 1
                        col_span = getattr(cell, 'col_span', 1) if hasattr(cell, 'col_span') else 1
                        cell_width = sum(col_widths[j:j + col_span]) if j + col_span <= len(col_widths) else col_widths[j] if j < len(col_widths) else 100
                        cell_height = sum(row_heights[i:i + row_span]) if i + row_span <= len(row_heights) else row_heights[i] if i < len(row_heights) else 30
                        x1 = x0 + cell_width
                        y1 = y0 + cell_height
                    else:
                        cell_width = (table_x1 - table_x0) / n_cols if n_cols > 0 else 100
                        cell_height = (table_y1 - table_y0) / n_rows if n_rows > 0 else 30
                        x0 = table_x0 + j * cell_width
                        y0 = table_y0 + i * cell_height
                        x1 = x0 + cell_width
                        y1 = y0 + cell_height

                cell_bg_rect = fitz.Rect(
                    max(x0 - 2, 0),
                    y0,
                    min(x1 + 2, page.rect.width),
                    y1
                )
                page.add_redact_annot(cell_bg_rect, fill=None)

        # 一次性执行 redaction，真正删除单元格原文（不删除图片）
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        logger.info(f"[表格绘制] 已执行 redaction 删除单元格原文")

        # ========== 第二遍：插入翻译文本 ==========
        # 绘制单元格文本
        for i, row in enumerate(table_cells):
            for j, cell in enumerate(row):
                # 跳过被合并覆盖的位置
                if cell is None:
                    logger.debug(f"[表格绘制] 单元格 ({i},{j}) 为 None（合并覆盖位置），跳过")
                    continue

                # 获取单元格文本和 bbox
                if isinstance(cell, dict):
                    cell_text = cell.get('text', '')
                    cell_bbox = cell.get('bbox')
                elif hasattr(cell, 'text') and hasattr(cell, 'bbox'):
                    cell_text = cell.text
                    cell_bbox = cell.bbox
                else:
                    cell_text = str(cell)
                    cell_bbox = None

                # 计算单元格矩形区域
                if cell_bbox and not (cell_bbox[0] == 0 and cell_bbox[1] == 0 and cell_bbox[2] == 0 and cell_bbox[3] == 0):
                    x0, y0, x1, y1 = cell_bbox
                    cell_width = x1 - x0
                    cell_height = y1 - y0
                    if cell_width <= 0 or cell_height <= 0:
                        cell_bbox = None

                if cell_bbox is None:
                    # 没有有效 bbox，使用行列信息计算
                    if table_bbox and row_heights and col_widths:
                        x0 = table_x0 + sum(col_widths[:j])
                        y0 = table_y0 + sum(row_heights[:i])
                        row_span = getattr(cell, 'row_span', 1) if hasattr(cell, 'row_span') else 1
                        col_span = getattr(cell, 'col_span', 1) if hasattr(cell, 'col_span') else 1
                        cell_width = sum(col_widths[j:j + col_span]) if j + col_span <= len(col_widths) else col_widths[j] if j < len(col_widths) else 100
                        cell_height = sum(row_heights[i:i + row_span]) if i + row_span <= len(row_heights) else row_heights[i] if i < len(row_heights) else 30
                        x1 = x0 + cell_width
                        y1 = y0 + cell_height
                    else:
                        cell_width = (table_x1 - table_x0) / n_cols if n_cols > 0 else 100
                        cell_height = (table_y1 - table_y0) / n_rows if n_rows > 0 else 30
                        x0 = table_x0 + j * cell_width
                        y0 = table_y0 + i * cell_height
                        x1 = x0 + cell_width
                        y1 = y0 + cell_height

                rect = fitz.Rect(x0, y0, x1, y1)
                cell_height = y1 - y0
                cell_width = x1 - x0

                # 绘制单元格文本
                if cell_text:
                    # 动态计算字体大小（基于完整单元格高度，合并单元格高度更大）
                    base_font_size = min(cell_height * 0.8, 12)
                    logger.debug(f"单元格 ({i},{j}) 字体大小: {base_font_size:.2f}, 单元格高度: {cell_height:.2f}")

                    # 根据 estimated_lines 预判单元格容量
                    cell_estimated_lines = getattr(cell, 'estimated_lines', 0)
                    if cell_estimated_lines > 0 and cell_height > 0:
                        # 计算能容纳 estimated_lines 行的最大字体大小
                        max_font_for_lines = cell_height / (cell_estimated_lines * 1.2)  # 1.2 is lineheight
                        if max_font_for_lines < base_font_size:
                            # 文本可能溢出 - 直接使用较小的字体
                            base_font_size = max(max_font_for_lines, base_font_size * 0.5)

                    max_attempts = 5
                    success = False

                    for attempt in range(1, max_attempts + 1):
                        if attempt == 1:
                            current_font_size = base_font_size
                        else:
                            current_font_size = base_font_size * (1 - (attempt - 1) * 0.1)
                            current_font_size = max(current_font_size, base_font_size * 0.5)

                        try:
                            result = page.insert_textbox(
                                rect,
                                cell_text,
                                fontname=suitable_font,
                                fontsize=current_font_size,
                                color=(0, 0, 0),
                                align=getattr(cell, 'alignment', 1),
                                lineheight=1.2
                            )

                            if result >= 0:
                                success = True
                                break
                        except Exception as e:
                            logger.error(f"单元格 ({i+1},{j+1}) 文本绘制异常: {str(e)}")

                    if not success:
                        # 尝试截断文本以适应单元格（二分搜索）
                        is_cjk = any('\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef' for ch in cell_text)
                        truncation_success = False

                        if is_cjk:
                            # CJK文本：二分搜索最大可容纳字符数
                            lo, hi = 1, len(cell_text) - 1
                            best_n = 0
                            while lo <= hi:
                                mid = (lo + hi) // 2
                                truncated = cell_text[:mid] + "…"
                                try:
                                    result = page.insert_textbox(
                                        rect,
                                        truncated,
                                        fontname=suitable_font,
                                        fontsize=base_font_size * 0.5,
                                        color=(0, 0, 0),
                                        align=1,
                                        lineheight=1.2
                                    )
                                    if result >= 0:
                                        best_n = mid
                                        lo = mid + 1
                                    else:
                                        hi = mid - 1
                                except Exception:
                                    hi = mid - 1
                            if best_n > 0:
                                truncation_success = True
                                final_truncated = cell_text[:best_n] + "…"
                                try:
                                    page.insert_textbox(
                                        rect,
                                        final_truncated,
                                        fontname=suitable_font,
                                        fontsize=base_font_size * 0.5,
                                        color=(0, 0, 0),
                                        align=1,
                                        lineheight=1.2
                                    )
                                except Exception:
                                    truncation_success = False
                        else:
                            # 英文文本：二分搜索最大可容纳词数
                            words = cell_text.split()
                            lo, hi = 1, len(words) - 1
                            best_n = 0
                            while lo <= hi:
                                mid = (lo + hi) // 2
                                truncated = " ".join(words[:mid]) + "…"
                                try:
                                    result = page.insert_textbox(
                                        rect,
                                        truncated,
                                        fontname=suitable_font,
                                        fontsize=base_font_size * 0.5,
                                        color=(0, 0, 0),
                                        align=1,
                                        lineheight=1.2
                                    )
                                    if result >= 0:
                                        best_n = mid
                                        lo = mid + 1
                                    else:
                                        hi = mid - 1
                                except Exception:
                                    hi = mid - 1
                            if best_n > 0:
                                truncation_success = True
                                final_truncated = " ".join(words[:best_n]) + "…"
                                try:
                                    page.insert_textbox(
                                        rect,
                                        final_truncated,
                                        fontname=suitable_font,
                                        fontsize=base_font_size * 0.5,
                                        color=(0, 0, 0),
                                        align=1,
                                        lineheight=1.2
                                    )
                                except Exception:
                                    truncation_success = False

                        if truncation_success:
                            logger.warning(f"[表格溢出] 单元格 ({i},{j}): 文本='{cell_text[:50]}...', 单元格尺寸={cell_width:.1f}x{cell_height:.1f}, 处理方式=截断")
                        else:
                            # 截断也失败，强制写入作为最后手段
                            try:
                                page.insert_textbox(
                                    rect,
                                    cell_text,
                                    fontname=suitable_font,
                                    fontsize=base_font_size * 0.5,
                                    color=(0, 0, 0),
                                    align=1,
                                    lineheight=1.2
                                )
                            except Exception as e:
                                logger.error(f"单元格 ({i+1},{j+1}) 最后尝试绘制异常: {str(e)}")
                            logger.warning(f"[表格溢出] 单元格 ({i},{j}): 文本='{cell_text[:50]}...', 单元格尺寸={cell_width:.1f}x{cell_height:.1f}, 处理方式=强制写入")

        # 统一绘制表格网格线（外框 + 内部线条，跳过合并单元格内部）
        try:
            if table_bbox:
                table_rect = fitz.Rect(table_x0, table_y0, table_x1, table_y1)
                # 外框
                page.draw_rect(table_rect, color=(0, 0, 0), width=1)

                # 构建遮挡信息：合并单元格内部的线段不绘制
                h_line_blocked = {}  # {row_boundary_idx: [(col_start, col_end), ...]}
                v_line_blocked = {}  # {col_boundary_idx: [(row_start, row_end), ...]}

                # 收集所有合并单元格信息
                merged_cells = []
                for row_idx, row in enumerate(table_cells):
                    for col_idx, cell in enumerate(row):
                        if cell is None:
                            continue
                        row_span = getattr(cell, 'row_span', 1)
                        col_span = getattr(cell, 'col_span', 1)
                        if row_span > 1 or col_span > 1:
                            merged_cells.append((row_idx, col_idx, row_span, col_span))
                            logger.debug(f"[网格线遮挡] 合并单元格 ({row_idx},{col_idx}): row_span={row_span}, col_span={col_span}")
                        if row_span > 1:
                            # 遮挡 row_idx 到 row_idx+row_span-1 之间的水平线
                            for r in range(row_idx, row_idx + row_span - 1):
                                if r not in h_line_blocked:
                                    h_line_blocked[r] = []
                                h_line_blocked[r].append((col_idx, col_idx + col_span - 1))
                        if col_span > 1:
                            # 遮挡 col_idx 到 col_idx+col_span-1 之间的垂直线
                            for c in range(col_idx, col_idx + col_span - 1):
                                if c not in v_line_blocked:
                                    v_line_blocked[c] = []
                                v_line_blocked[c].append((row_idx, row_idx + row_span - 1))

                # 排除其他合并单元格的边界线：如果一条线段是某个合并单元格的边界，
                # 则不应该被遮挡（画线优先于不画线）
                # 收集合并单元格的边界位置，但区分水平/垂直方向：
                # - 水平边界（用于 h_blocked 排除）：只有 col_span > 1 的单元格才添加其上/下边框，
                #   因为 col_span 跨多列，上/下边框应完整绘制；row_span > 1 的上/下边框是合并内部，应被遮挡
                # - 垂直边界（用于 v_blocked 排除）：只有 row_span > 1 的单元格才添加其左/右边框，
                #   因为 row_span 跨多行，左/右边框应完整绘制；col_span > 1 的左/右边框是合并内部，应被遮挡
                h_boundaries = {}  # {row_boundary_idx: set of col indices that are boundaries}
                v_boundaries = {}  # {col_boundary_idx: set of row indices that are boundaries}
                for row_idx, col_idx, row_span, col_span in merged_cells:
                    # 水平边界：只有 col_span > 1 的单元格，其上/下边框才排除遮挡
                    if col_span > 1:
                        # 上边框：row_boundary = row_idx - 1（如果存在）
                        if row_idx > 0:
                            if row_idx - 1 not in h_boundaries:
                                h_boundaries[row_idx - 1] = set()
                            for c in range(col_idx, col_idx + col_span):
                                h_boundaries[row_idx - 1].add(c)
                        # 下边框：row_boundary = row_idx + row_span - 1
                        bottom_boundary = row_idx + row_span - 1
                        if bottom_boundary not in h_boundaries:
                            h_boundaries[bottom_boundary] = set()
                        for c in range(col_idx, col_idx + col_span):
                            h_boundaries[bottom_boundary].add(c)

                    # 垂直边界：只有 row_span > 1 的单元格，其左/右边框才排除遮挡
                    if row_span > 1:
                        # 左边框：col_boundary = col_idx - 1（如果存在）
                        if col_idx > 0:
                            if col_idx - 1 not in v_boundaries:
                                v_boundaries[col_idx - 1] = set()
                            for r in range(row_idx, row_idx + row_span):
                                v_boundaries[col_idx - 1].add(r)
                        # 右边框：col_boundary = col_idx + col_span - 1
                        right_boundary = col_idx + col_span - 1
                        if right_boundary not in v_boundaries:
                            v_boundaries[right_boundary] = set()
                        for r in range(row_idx, row_idx + row_span):
                            v_boundaries[right_boundary].add(r)

                # 从遮挡信息中排除边界位置
                # 将遮挡范围拆分为更小的段，排除边界列/行
                def subtract_boundary_from_blocked(blocked_ranges, boundary_set):
                    """从遮挡范围中排除边界位置"""
                    if not boundary_set:
                        return blocked_ranges
                    result = []
                    for start, end in blocked_ranges:
                        # 将 (start, end) 拆分为不包含 boundary_set 中位置的段
                        current = start
                        for pos in sorted(boundary_set):
                            if pos < current:
                                continue
                            if pos > end:
                                break
                            if pos > current:
                                result.append((current, pos - 1))
                            current = pos + 1
                        if current <= end:
                            result.append((current, end))
                    return result

                for r in list(h_line_blocked.keys()):
                    h_line_blocked[r] = subtract_boundary_from_blocked(
                        h_line_blocked[r], h_boundaries.get(r, set())
                    )
                    # 清理空的遮挡范围
                    h_line_blocked[r] = [(s, e) for s, e in h_line_blocked[r] if s <= e]
                    if not h_line_blocked[r]:
                        del h_line_blocked[r]

                for c in list(v_line_blocked.keys()):
                    v_line_blocked[c] = subtract_boundary_from_blocked(
                        v_line_blocked[c], v_boundaries.get(c, set())
                    )
                    v_line_blocked[c] = [(s, e) for s, e in v_line_blocked[c] if s <= e]
                    if not v_line_blocked[c]:
                        del v_line_blocked[c]

                logger.debug(f"[网格线遮挡] h_line_blocked={h_line_blocked}")
                logger.debug(f"[网格线遮挡] v_line_blocked={v_line_blocked}")

                # 绘制水平线（跳过被遮挡的段）
                for row_i in range(len(row_heights) - 1):
                    line_y = table_y0 + sum(row_heights[:row_i + 1])
                    blocked_ranges = h_line_blocked.get(row_i, [])
                    segments = self._compute_visible_segments(0, len(col_widths) - 1, blocked_ranges)
                    for seg_start, seg_end in segments:
                        x_start = table_x0 + sum(col_widths[:seg_start])
                        x_end = table_x0 + sum(col_widths[:seg_end + 1])
                        page.draw_line(
                            fitz.Point(x_start, line_y),
                            fitz.Point(x_end, line_y),
                            color=(0, 0, 0), width=0.5
                        )

                # 绘制垂直线（跳过被遮挡的段）
                for col_j in range(len(col_widths) - 1):
                    line_x = table_x0 + sum(col_widths[:col_j + 1])
                    blocked_ranges = v_line_blocked.get(col_j, [])
                    segments = self._compute_visible_segments(0, len(row_heights) - 1, blocked_ranges)
                    for seg_start, seg_end in segments:
                        y_start = table_y0 + sum(row_heights[:seg_start])
                        y_end = table_y0 + sum(row_heights[:seg_end + 1])
                        page.draw_line(
                            fitz.Point(line_x, y_start),
                            fitz.Point(line_x, y_end),
                            color=(0, 0, 0), width=0.5
                        )

                logger.info("表格网格线绘制完成（已跳过合并单元格内部）")
        except Exception as e:
            logger.error(f"绘制表格网格线异常: {e}")

        logger.info("表格绘制完成")
    
    def _get_system_fonts(self):
        """从系统中获取可用字体列表（带缓存，避免重复遍历文件系统）

        Returns:
            list: 系统可用字体完整路径列表
        """
        if self._system_fonts_cache is not None:
            return self._system_fonts_cache

        system_fonts = []
        try:
            # 获取系统字体目录
            if sys.platform == 'win32':
                # Windows系统字体目录
                font_dirs = [r'C:\Windows\Fonts']
            elif sys.platform == 'darwin':
                # macOS系统字体目录
                font_dirs = [
                    '/System/Library/Fonts',
                    '/Library/Fonts',
                    os.path.expanduser('~/Library/Fonts')
                ]
            else:
                # Linux系统字体目录
                font_dirs = [
                    '/usr/share/fonts',
                    '/usr/local/share/fonts',
                    os.path.expanduser('~/.fonts')
                ]
            
            # 遍历字体目录，获取字体文件
            for font_dir in font_dirs:
                if os.path.exists(font_dir):
                    for root, _, files in os.walk(font_dir):
                        for file in files:
                            if file.endswith(('.ttf', '.otf', '.ttc')):  # 考虑TrueType、OpenType和TrueType集合字体
                                # 获取字体完整路径
                                font_path = os.path.join(root, file)
                                system_fonts.append(font_path)
            
            # 去重并排序
            system_fonts = list(set(system_fonts))
            system_fonts.sort()  # 按字母顺序排序，提高可预测性
            logger.info(f"从系统获取到 {len(system_fonts)} 种可用字体")
        except Exception as e:
            logger.warning(f"获取系统字体列表失败: {e}")
            system_fonts = []

        self._system_fonts_cache = system_fonts
        return system_fonts

    @staticmethod
    def _find_font_file(fontname, system_font_paths):
        """在系统字体列表中查找匹配的字体文件

        匹配策略（按优先级）：
        1. 精确匹配（去除扩展名后）
        2. 前缀匹配（字体家族名 + 变体后缀，如 Arial-Bold → ArialBold.ttf）
        3. 子串匹配（兜底）

        Args:
            fontname (str): 目标字体名称
            system_font_paths (list): 系统字体路径列表

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

            # 1. 精确匹配
            if norm_target == norm_filename:
                return font_path

            # 2. 前缀匹配：目标字体是文件名的前缀（如 "Arial" 匹配 "ArialBold"，不匹配 "ArialUnicodeMS"）
            if norm_filename.startswith(norm_target + '-') or norm_filename.startswith(norm_target + '_') or \
               norm_filename.startswith(norm_target + 'bold') or norm_filename.startswith(norm_target + 'italic'):
                return font_path

        # 3. 兜底子串匹配（原逻辑，优先返回第一个匹配）
        for font_path in system_font_paths:
            filename = os.path.basename(font_path)
            name_without_ext = os.path.splitext(filename)[0]
            norm_filename = name_without_ext.lower().replace('-', '').replace(' ', '')
            if norm_target in norm_filename:
                return font_path

        return None

    def _check_embedded_font_support(self, page, fontname, target_lang):
        """检查PDF内嵌字体是否支持目标语言字符

        通过在临时页面上用该字体插入测试文本来检测。
        如果字体不支持目标语言字符，PyMuPDF会使用替换字形，
        导致插入的文本长度与预期不符。

        Args:
            page (fitz.Page): PDF页面对象
            fontname (str): 字体名称
            target_lang (str): 目标语言代码

        Returns:
            bool: 字体是否支持目标语言字符
        """
        # 获取目标语言的测试字符
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
        }
        test_char = test_chars.get(target_lang, test_chars['en'])

        # 拉丁语言（en/fr/de/es/pt/it/nl）的内嵌字体通常支持拉丁字符
        latin_langs = {'en', 'fr', 'de', 'es', 'pt', 'it', 'nl'}
        if target_lang in latin_langs:
            # 尝试从系统字体中查找该字体文件进行精确检测
            system_font_paths = self._get_system_fonts()
            matched_path = self._find_font_file(fontname, system_font_paths)
            if matched_path:
                return self._check_font_support(matched_path, target_lang)
            # 找不到字体文件，拉丁语言默认支持
            logger.debug(f"拉丁语言 '{target_lang}'，内嵌字体 '{fontname}' 默认支持")
            return True

        # 非拉丁语言：尝试从系统字体中查找该字体文件进行检测
        system_font_paths = self._get_system_fonts()
        matched_path = self._find_font_file(fontname, system_font_paths)
        if matched_path:
            result = self._check_font_support(matched_path, target_lang)
            logger.debug(f"内嵌字体 '{fontname}' 系统文件检测: {result}")
            return result

        # 无法找到字体文件，非拉丁语言默认不支持
        logger.debug(f"内嵌字体 '{fontname}' 未找到系统文件，非拉丁语言 '{target_lang}' 默认不支持")
        return False

    def _check_font_support(self, font_path, target_lang):
        """检查字体是否真正支持目标语言

        Args:
            font_path (str): 字体文件路径
            target_lang (str): 目标语言代码
            
        Returns:
            bool: 字体是否真正支持目标语言
        """
        try:
            # 获取字体文件名
            font_filename = os.path.basename(font_path)
            
            # 尝试加载字体
            font = ImageFont.truetype(font_path, 12)
            
            # 获取目标语言的测试字符
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
            }
            test_char = test_chars.get(target_lang, test_chars['en'])
            
            # 检查字体是否包含测试字符的字形
            # 使用getbbox检查每个字符的宽度，替换字符宽度通常为0或固定值
            for char in test_char:
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                # 如果字符宽度为0或非常小，说明字体不支持该字符
                if char_width < 1:
                    logger.debug(f"字体 '{font_filename}' 不包含字符 '{char}' 的字形")
                    return False
            
            logger.debug(f"字体 '{font_filename}' 支持目标语言 '{target_lang}'")
            return True
        except Exception as e:
            logger.debug(f"字体 '{os.path.basename(font_path)}' 加载失败或不支持目标语言 '{target_lang}': {e}")
            return False
