from __future__ import annotations

import glob
import os
import shutil

from modules.docx_generator import DocxGenerator
from modules.markdown_generator import create_markdown_generator
from modules.pdf_generator import PdfGenerator
from config import config
from utils.file_utils import remove_file, create_zip
from utils.logging_config import get_logger

logger = get_logger(__name__)


class TranslationOutputGenerator:
    """输出生成：负责各种格式输出文件的生成"""

    def generate_output_files(self, task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type='aiping', chapters=None, chapter_split=True, output_path=None, output_filename=None, tmp_dir=None, target_pages=None):
        """生成输出文件

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            unique_id: 唯一ID
            filename: 原始文件名
            output_format: 输出格式
            translated_content: 翻译后的内容
            extracted_images: 提取的图像
            target_lang: 目标语言
            translator_type: 翻译器类型（aiping/silicon_flow）
            chapter_split: 是否按章节翻译Markdown (默认: True)
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件

        Returns:
            list: 输出文件名列表
        """
        logger.info(f"任务 {task.task_id} 开始生成输出文件")

        # 添加调用前的日志，记录translated_content中的blocks信息
        logger.info(f"任务 {task.task_id} translated_content包含blocks信息: {('blocks' in translated_content)}")
        if 'blocks' in translated_content:
            total_blocks = sum(len(page.text_blocks) for page in translated_content['blocks'])
            logger.info(f"任务 {task.task_id} 传递给生成器的blocks信息: 总页数={len(translated_content['blocks'])}, 总blocks数={total_blocks}")

        output_files = []

        # 计算需要生成的格式数量，用于细粒度进度
        format_steps = []
        if output_format in ['pdf', 'pdf_docx', 'all']:
            format_steps.append(('PDF', 'pdf'))
        if output_format in ['docx', 'pdf_docx', 'all']:
            format_steps.append(('DOCX', 'docx'))
        if output_format in ['md', 'markdown', 'all']:
            format_steps.append(('Markdown', 'md'))
        total_steps = len(format_steps)
        completed_steps = 0

        # 处理PDF生成
        if output_format in ['pdf', 'pdf_docx', 'all']:
            task.update_phase_progress('generation', int(completed_steps / total_steps * 100), '正在生成输出文件: PDF...')
            pdf_filename = self.generate_pdf_output(task, input_filepath, unique_id, filename, translated_content, target_lang, output_path, output_filename, target_pages=target_pages)
            output_files.append(pdf_filename)
            completed_steps += 1

        # 处理Word生成
        if output_format in ['docx', 'pdf_docx', 'all']:
            task.update_phase_progress('generation', int(completed_steps / total_steps * 100), '正在生成输出文件: DOCX...')
            docx_filename = self.generate_docx_output(task, unique_id, filename, translated_content, extracted_images, target_lang, output_path, output_filename)
            output_files.append(docx_filename)
            completed_steps += 1

        # 处理Markdown生成
        if output_format in ['md', 'markdown', 'all']:
            task.update_phase_progress('generation', int(completed_steps / total_steps * 100), '正在生成输出文件: Markdown...')
            logger.info(f"任务 {task.task_id} 开始生成Markdown输出")
            try:
                md_filename = self.generate_markdown_output(task, unique_id, filename, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path, output_filename, tmp_dir)
                output_files.append(md_filename)
                completed_steps += 1
            except Exception as e:
                logger.error(f"任务 {task.task_id} Markdown文档生成失败: {str(e)}")
                # 抛出异常，让上层处理
                raise Exception(f"Markdown文档生成失败: {str(e)}")

        return output_files

    def generate_pdf_output(self, task, input_filepath, unique_id, filename, translated_content, target_lang, output_path=None, output_filename=None, target_pages=None):
        """生成PDF输出文件

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            unique_id: 唯一ID
            filename: 原始文件名
            translated_content: 翻译后的内容
            target_lang: 目标语言
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名

        Returns:
            str: 输出文件名
        """
        # 使用lazy import确保测试@patch能生效
        from services.translation_service import PdfGenerator, os as _os
        # 如果用户指定了输出文件名，则使用用户指定的文件名
        if output_filename:
            final_output_filename = output_filename
        else:
            final_output_filename = f"translated_{unique_id}_{filename}"
        output_filepath = _os.path.join(output_path if output_path else config.OUTPUT_FOLDER, final_output_filename)

        # 创建PDF生成器实例
        pdf_generator = PdfGenerator()
        # 生成翻译后的PDF，传递目标语言参数和页码范围
        pdf_generator.generate_pdf(input_filepath, translated_content, output_filepath, target_lang, target_pages=target_pages)
        logger.info(f"任务 {task.task_id} PDF生成完成，输出文件: {final_output_filename}")
        return final_output_filename

    def generate_docx_output(self, task, unique_id, filename, translated_content, extracted_images, target_lang, output_path=None, output_filename=None):
        """生成Word输出文件

        Args:
            task: 任务对象
            unique_id: 唯一ID
            filename: 原始文件名
            translated_content: 翻译后的内容
            extracted_images: 提取的图像
            target_lang: 目标语言
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名

        Returns:
            str: 输出文件名
        """
        # 使用lazy import确保测试@patch能生效
        from services.translation_service import DocxGenerator, os as _os
        # 如果用户指定了输出文件名，则使用用户指定的文件名
        if output_filename:
            final_output_filename = output_filename
        else:
            final_output_filename = f"translated_{unique_id}_{_os.path.splitext(filename)[0]}.docx"
        docx_filepath = _os.path.join(output_path if output_path else config.OUTPUT_FOLDER, final_output_filename)

        # 创建Word生成器实例
        docx_generator = DocxGenerator()

        # 记录传递给Word生成器的图像信息
        logger.info(f"任务 {task.task_id} 传递 {len(extracted_images)} 个图像到Word生成器")
        for i, image in enumerate(extracted_images):
            logger.debug(f"任务 {task.task_id} 传递图像 {i+1}: 页码={image.page_num}, 路径={image.image_path}, 边界框={image.bbox}")

        # 生成翻译后的Word文档
        docx_generator.generate_docx(translated_content, extracted_images, docx_filepath, target_lang)
        logger.info(f"任务 {task.task_id} Word文档生成完成，输出文件: {final_output_filename}")
        return final_output_filename

    def generate_markdown_output(self, task, unique_id, filename, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path=None, output_filename=None, tmp_dir=None):
        """生成Markdown输出文件

        Args:
            task: 任务对象
            unique_id: 唯一ID
            filename: 原始文件名
            translated_content: 翻译后的内容
            extracted_images: 提取的图像
            target_lang: 目标语言
            translator_type: 翻译器类型
            chapters: 章节信息
            chapter_split: 是否按章节拆分
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件

        Returns:
            str: 输出文件名
        """
        from services.translation_service import os as _os
        # 生成Markdown文件名
        md_filename = f"translated_{unique_id}_{_os.path.splitext(filename)[0]}.md"
        # 使用tmp_dir存放Markdown文件
        md_filepath = _os.path.join(tmp_dir if tmp_dir else (output_path if output_path else config.OUTPUT_FOLDER), md_filename)

        # 根据翻译器类型选择布局模型
        api_key, api_url, layout_model = self._get_markdown_generator_config(translator_type)

        # 创建Markdown生成器实例
        markdown_generator = create_markdown_generator(
            api_type=translator_type,
            api_key=api_key,
            api_url=api_url,
            model=layout_model
        )

        # 记录传递给Markdown生成器的图像信息
        logger.info(f"任务 {task.task_id} 传递 {len(extracted_images)} 个图像到Markdown生成器")
        for i, image in enumerate(extracted_images):
            logger.debug(f"任务 {task.task_id} 传递图像 {i+1}: 页码={image.page_num}, 路径={image.image_path}, 边界框={image.bbox}")

        # 使用传入的章节信息
        logger.info(f"任务 {task.task_id} 接收到 {len(chapters) if chapters else 0} 个章节，章节拆分: {chapter_split}")

        # 生成翻译后的Markdown文档
        try:
            # 使用unique_id作为doc_id，确保每个文档有独立的图像目录
            # 根据chapter_split参数决定是否传递章节信息
            markdown_result = markdown_generator.generate_markdown(
                translated_content, extracted_images, md_filepath, target_lang,
                doc_id=unique_id,
                chapters=chapters if chapter_split and chapters and len(chapters) > 0 else None
            )

            # 处理返回的MarkdownGenerationResult
            # 检查是否有警告信息
            if hasattr(markdown_result, 'warnings') and markdown_result.warnings:
                for warning in markdown_result.warnings:
                    logger.warning(f"任务 {task.task_id} Markdown生成警告: {warning['message']}")
                    # 添加警告到任务对象
                    task.add_warning(warning['message'], warning['context'])

            # 构建输出文件列表
            if chapter_split and chapters and len(chapters) > 0:
                return self._generate_chapter_zip(task, unique_id, filename, md_filename, output_path, output_filename, tmp_dir)
            else:
                return self._generate_single_zip(task, unique_id, filename, md_filepath, output_path, output_filename, tmp_dir)
        finally:
            # 清理临时图像目录
            self._cleanup_temp_images(unique_id, output_path, tmp_dir)

    def _get_markdown_generator_config(self, translator_type):
        """获取Markdown生成器配置

        Args:
            translator_type: 翻译器类型

        Returns:
            tuple: (api_key, api_url, layout_model)
        """
        if translator_type == 'aiping':
            api_key = config.AIPING_API_KEY
            api_url = config.AIPING_API_URL
            layout_model = config.AIPING_MODEL_LAYOUT
        elif translator_type == 'silicon_flow':
            api_key = config.SILICON_FLOW_API_KEY
            api_url = config.SILICON_FLOW_API_URL
            layout_model = config.SILICON_FLOW_MODEL_LAYOUT
        else:
            # 默认使用aiping的布局模型
            api_key = config.AIPING_API_KEY
            api_url = config.AIPING_API_URL
            layout_model = config.AIPING_MODEL_LAYOUT
        return api_key, api_url, layout_model

    def _generate_chapter_zip(self, task, unique_id, filename, md_filename, output_path=None, output_filename=None, tmp_dir=None):
        """生成章节Markdown压缩文件

        Args:
            task: 任务对象
            unique_id: 唯一ID
            filename: 原始文件名
            md_filename: Markdown文件名
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件

        Returns:
            str: 压缩文件名
        """
        from services.translation_service import create_zip, os as _os
        # 使用tmp_dir查找章节文件
        base_dir = tmp_dir if tmp_dir else (output_path if output_path else config.OUTPUT_FOLDER)
        chapter_files = glob.glob(_os.path.join(base_dir, "*.md"))
        logger.info(f"找到的MD文件: {[os.path.basename(f) for f in chapter_files]}")
        # 过滤出章节文件
        chapter_files = [f for f in chapter_files if _os.path.basename(f) != md_filename]
        logger.info(f"过滤后的章节文件: {[os.path.basename(f) for f in chapter_files]}")

        # 创建包含所有Markdown文件和图像目录的zip文件
        # 如果用户指定了输出文件名，则使用用户指定的文件名
        if output_filename:
            zip_filename = output_filename
        else:
            zip_filename = f"translated_{unique_id}_{_os.path.splitext(filename)[0]}.zip"
        zip_filepath = _os.path.join(output_path if output_path else config.OUTPUT_FOLDER, zip_filename)

        # 检查是否存在当前文档的图像目录
        images_dir = _os.path.join(base_dir, f'images_{unique_id}')
        directories_to_include = []
        if _os.path.exists(images_dir):
            directories_to_include.append(images_dir)

        # 创建zip文件
        create_zip(zip_filepath, chapter_files, directories_to_include)
        logger.info(f"任务 {task.task_id} 章节Markdown压缩文件生成完成，输出文件: {zip_filename}")
        return zip_filename

    def _generate_single_zip(self, task, unique_id, filename, md_filepath, output_path=None, output_filename=None, tmp_dir=None):
        """生成单个Markdown压缩文件

        Args:
            task: 任务对象
            unique_id: 唯一ID
            filename: 原始文件名
            md_filepath: Markdown文件路径
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件

        Returns:
            str: 压缩文件名
        """
        from services.translation_service import create_zip, os as _os
        logger.info(f"任务 {task.task_id} Markdown文档生成完成，输出文件: {_os.path.basename(md_filepath)}")

        # 创建包含Markdown文件和当前文档图像目录的zip文件
        base_dir = output_path if output_path else config.OUTPUT_FOLDER
        # 如果用户指定了输出文件名，则使用用户指定的文件名
        if output_filename:
            zip_filename = output_filename
        else:
            zip_filename = f"translated_{unique_id}_{_os.path.splitext(filename)[0]}.zip"
        zip_filepath = _os.path.join(base_dir, zip_filename)

        # 检查是否存在当前文档的图像目录（优先使用tmp_dir）
        images_dir = _os.path.join(tmp_dir if tmp_dir else base_dir, f'images_{unique_id}')
        directories_to_include = []
        if _os.path.exists(images_dir):
            directories_to_include.append(images_dir)

        # 创建zip文件
        create_zip(zip_filepath, [md_filepath], directories_to_include)
        logger.info(f"任务 {task.task_id} Markdown压缩文件生成完成，输出文件: {zip_filename}")
        return zip_filename

    def _cleanup_temp_images(self, unique_id, output_path=None, tmp_dir=None):
        """清理临时图像目录

        Args:
            unique_id: 唯一ID
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            tmp_dir: 临时文件目录，用于存放中间文件
        """
        base_dir = tmp_dir if tmp_dir else (output_path if output_path else config.OUTPUT_FOLDER)
        images_dir = os.path.join(base_dir, f'images_{unique_id}')
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
            logger.info(f"已清理临时图像目录: {images_dir}")

    def _cleanup_ocr_temp_images(self, extracted_images):
        """清理OCR提取的临时图片目录（temp_images）

        在全部输出文件生成完成后调用，确保 markdown_generator 的
        _copy_images_to_output 已成功复制图片后再清理。

        Args:
            extracted_images (list): 提取的图像列表
        """
        if not extracted_images:
            return

        # 从图像路径提取临时目录
        temp_dirs = set()
        for img in extracted_images:
            img_path = getattr(img, 'image_path', None)
            if img_path and img_path != '':
                img_dir = os.path.dirname(img_path)
                if img_dir:
                    temp_dirs.add(img_dir)

        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"已清理OCR临时图片目录: {temp_dir}")
                except Exception as e:
                    logger.warning(f"清理OCR临时图片目录失败: {e}")

    def cleanup_resources(self, task, input_filepath, output_filepath=None):
        """清理资源

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            output_filepath: 输出文件路径（可选）
        """
        from services.translation_service import remove_file, os as _os
        try:
            # 清理临时文件
            if input_filepath and _os.path.exists(input_filepath):
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 已清理临时文件: {input_filepath}")

            # 清理输出文件（如果任务被取消）
            if output_filepath and _os.path.exists(output_filepath):
                remove_file(output_filepath)
                logger.info(f"任务 {task.task_id} 已清理输出文件: {output_filepath}")
        except Exception as e:
            logger.error(f"任务 {task.task_id} 清理资源时出错: {str(e)}")

    def cleanup_on_cancel(self, task, input_filepath):
        """任务取消时的资源清理

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
        """
        from services.translation_service import remove_file, os as _os
        try:
            # 清理临时文件
            if input_filepath and _os.path.exists(input_filepath):
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理临时文件: {input_filepath}")
        except Exception as e:
            logger.error(f"任务 {task.task_id} 取消时清理资源出错: {str(e)}")

    def cleanup_output_directory(self):
        """清理输出目录中的旧文件"""
        from services.translation_service import os as _os
        if _os.path.exists(config.OUTPUT_FOLDER):
            for file_name in _os.listdir(config.OUTPUT_FOLDER):
                file_path = _os.path.join(config.OUTPUT_FOLDER, file_name)
                if _os.path.isfile(file_path):
                    # 清理所有类型的输出文件
                    if file_path.endswith(('.pdf', '.docx', '.md', '.zip')):
                        try:
                            if _os.access(file_path, os.W_OK):
                                _os.remove(file_path)
                                logger.info(f"清理旧输出文件: {file_path}")
                            else:
                                logger.warning(f"没有权限清理文件: {file_path}")
                        except Exception as e:
                            logger.warning(f"清理文件时出错: {file_path}, 错误: {str(e)}")
                elif _os.path.isdir(file_path) and file_name.startswith('images_'):
                    # 清理图像目录
                    try:
                        if _os.access(file_path, os.W_OK):
                            shutil.rmtree(file_path)
                            logger.info(f"清理旧图像目录: {file_path}")
                        else:
                            logger.warning(f"没有权限清理目录: {file_path}")
                    except Exception as e:
                        logger.warning(f"清理目录时出错: {file_path}, 错误: {str(e)}")
            logger.info("输出目录清理完成")
