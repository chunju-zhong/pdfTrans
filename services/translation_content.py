from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.extraction import PdfPage
from utils.text_processing import merge_semantic_blocks, merge_semantic_blocks_with_llm, merge_semantic_blocks_with_llm_two_phase, split_translated_result
from utils.logging_config import get_logger

from config import config

logger = get_logger(__name__)


class TranslationContentTranslator:
    """内容翻译：负责文本块的翻译处理"""

    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor

    def translate_content(self, task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary):
        """翻译文本内容

        Args:
            task: 任务对象
            text_blocks: 文本块列表
            semantic_merge: 是否启用语义块合并
            use_llm_merging: 是否使用大模型进行语义块合并
            translator: 翻译器实例
            semantic_analyzer: 语义分析器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表

        Returns:
            tuple: (page_translated_blocks_dict, merged_translations, translated_blocks)
        """
        if semantic_merge:
            task.update_phase_progress('semantic_merge', 0, '正在进行语义合并...')
            logger.info(f"任务 {task.task_id} 开始语义块合并，原始块数量: {len(text_blocks)}")

            def _merge_progress_cb(current, total):
                if total > 0:
                    percent = int(current / total * 100)
                    task.update_phase_progress('semantic_merge', percent, f'正在合并语义块: {current}/{total}')

            # 根据配置选择合并方法
            if use_llm_merging:
                logger.info(f"任务 {task.task_id} 使用大模型进行语义块合并")
                # 根据配置选择使用两阶段并行合并或原方法
                if config.USE_TWO_PHASE_MERGE:
                    logger.info(f"任务 {task.task_id} 使用两阶段并行合并方法")
                    # 使用lazy import确保测试@patch能生效
                    from services.translation_service import merge_semantic_blocks_with_llm_two_phase as _merge_two_phase
                    merged_blocks, block_mapping = _merge_two_phase(
                        text_blocks, semantic_analyzer, source_lang,
                        max_workers=config.MERGE_MAX_WORKERS,
                        batch_size=config.MERGE_BATCH_SIZE,
                        progress_callback=_merge_progress_cb
                    )
                else:
                    logger.info(f"任务 {task.task_id} 使用原始串行合并方法")
                    from services.translation_service import merge_semantic_blocks_with_llm as _merge_llm
                    merged_blocks, block_mapping = _merge_llm(text_blocks, semantic_analyzer, source_lang, progress_callback=_merge_progress_cb)
            else:
                logger.info(f"任务 {task.task_id} 使用规则-based方法进行语义块合并")
                # 使用规则-based方法进行语义块合并
                from services.translation_service import merge_semantic_blocks as _merge_rules
                merged_blocks, block_mapping = _merge_rules(text_blocks, progress_callback=_merge_progress_cb)

            logger.info(f"任务 {task.task_id} 语义块合并完成，原始块数量: {len(text_blocks)}, 合并后块数量: {len(merged_blocks)}")

            task.update_phase_progress('semantic_merge', 100, '语义块合并完成，开始翻译...')

            # 记录合并块的数量摘要
            logger.info(f"任务 {task.task_id} 语义块合并完成，共 {len(merged_blocks)} 个合并块")
            for i, merged_block in enumerate(merged_blocks):
                logger.debug(f"任务 {task.task_id} 合并块 {i+1} 内容: {merged_block.block_text}")

            # 处理合并后的块
            return self.process_merged_blocks(
                task, merged_blocks, translator, source_lang, target_lang, doc_type, glossary
            )
        else:
            logger.info(f"任务 {task.task_id} 跳过语义块合并，直接按原始块翻译")
            # 直接翻译原始块
            return self.process_original_blocks(
                task, text_blocks, translator, source_lang, target_lang, doc_type, glossary
            )

    def _translate_content(self, task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary, all_page_nums):
        """翻译文本内容（内部封装，返回字典格式）

        Args:
            task: 任务对象
            text_blocks: 文本块列表
            semantic_merge: 是否启用语义块合并
            use_llm_merging: 是否使用大模型进行语义块合并
            translator: 翻译器实例
            semantic_analyzer: 语义分析器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            all_page_nums: 所有页码列表（包括没有文本块的页面）

        Returns:
            dict: 翻译后的内容
        """
        logger.info(f"任务 {task.task_id} 开始翻译文本内容")
        # 准备翻译内容
        translated_content = {
            'tables': []
        }

        # 收集所有页面的所有块，方便上下文查找
        logger.info(f"任务 {task.task_id} 将blocks信息添加到translated_content中")
        translated_content['blocks'] = []

        # 翻译文本内容
        page_translated_blocks_dict, merged_translations, translated_blocks = self.translate_content(
            task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary
        )

        # 添加合并后的翻译结果到translated_content
        translated_content['merged_translations'] = merged_translations

        # 将翻译结果添加到translated_content中，确保所有页面（包括无文本块的页面）都被保留
        blocks_list = []
        for page_num in sorted(all_page_nums):
            if page_num in page_translated_blocks_dict:
                blocks_list.append(page_translated_blocks_dict[page_num])
            else:
                logger.info(f"任务 {task.task_id} 页码 {page_num} 无翻译文本块，保留空页面")
                blocks_list.append(PdfPage(page_num, []))
        translated_content['blocks'] = blocks_list

        logger.info(f"任务 {task.task_id} 翻译完成，总翻译块数量: {translated_blocks}")

        # 直接使用原始样式信息，不再需要text_content字段
        logger.info(f"任务 {task.task_id} 直接使用原始样式信息，不再需要text_content字段")

        logger.info(f"任务 {task.task_id} 文本翻译完成")

        if task.is_canceled():
            return None

        return translated_content

    def translate_merged_block(self, task, merged_block, index, translator, source_lang, target_lang, doc_type, glossary, total_blocks):
        """翻译单个合并块

        Args:
            task: 任务对象
            merged_block: 合并块
            index: 合并块索引
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            total_blocks: 总块数

        Returns:
            tuple: (translated_merged_block, block_results, page_num)
        """
        logger.info(f"任务 {task.task_id} 处理合并块 {index+1}/{total_blocks}")
        logger.debug(f"任务 {task.task_id} 合并块 {index+1} 原文: {merged_block.block_text}")

        if any(getattr(b, 'is_formula', False) for b in merged_block.original_blocks):
            block_results = []
            for j, block_info in enumerate(merged_block.original_blocks):
                text_block = block_info
                translated_text_block = text_block.copy()
                translated_text_block.block_text = text_block.block_text
                translated_text_block.update_style(
                    font=text_block.font,
                    font_size=text_block.font_size,
                    color=text_block.color,
                    flags=text_block.flags
                )
                block_results.append((text_block.page_num, translated_text_block))
            from models.merged_block import MergedBlock
            translated_merged_block = MergedBlock(
                block_text=merged_block.block_text,
                original_blocks=merged_block.original_blocks,
                max_width=merged_block.max_width,
                max_height=merged_block.max_height
            )
            return translated_merged_block, block_results, merged_block.page_num

        merged_text = merged_block.block_text
        logger.info(f'合并翻译请求: 原文前100字符="{merged_text[:100]}", 长度={len(merged_text)}')
        translation_result = translator.translate(
            merged_text,
            source_lang,
            target_lang,
            doc_type=doc_type,
            glossary=glossary
        )
        merged_translation = translation_result.content
        logger.info(f'合并翻译结果: 结果前200字符="{merged_translation[:200]}", 长度={len(merged_translation)}')
        if self._is_translation_unchanged(merged_translation, merged_text):
            logger.warning(f'合并翻译结果与原文实质相同（可能未翻译）: 原文前100字符="{merged_text[:100]}", 结果前200字符="{merged_translation[:200]}"')
        logger.info(f"任务 {task.task_id} 合并块 {index+1} 翻译结果: {merged_translation}")

        # 检查是否被截断
        if translation_result.truncated:
            logger.warning(f"任务 {task.task_id} 合并块 {index+1} 翻译被截断: {translation_result.truncation_info}")
            # 添加警告到任务对象
            task.add_warning("翻译被截断", {
                "process": "translation",
                "block_index": index,
                "token_usage": translation_result.token_usage,
                "finish_reason": translation_result.finish_reason
            })

        # 保存合并后的翻译结果
        from models.merged_block import MergedBlock

        first_block = merged_block.original_blocks[0]
        first_text_block = first_block
        page_num = merged_block.page_num
        logger.info(f"合并块 {index+1} 第一个原始块字体大小: {first_text_block.font_size}, 文本: '{first_text_block.block_text[:50]}...'")

        # 创建新的 MergedBlock 对象，使用翻译后的文本作为 block_text
        translated_merged_block = MergedBlock(
            block_text=merged_translation,
            original_blocks=merged_block.original_blocks,
            max_width=merged_block.max_width,
            max_height=merged_block.max_height
        )

        # 记录合并块中所有原始块的字体大小
        for j, block_info in enumerate(merged_block.original_blocks):
            text_block = block_info
            logger.debug(f"合并块 {index+1} 原始块 {j+1} 字体大小: {text_block.font_size}, 文本: '{text_block.block_text[:50]}...'")

        # 拆分翻译结果
        original_blocks = merged_block.original_blocks
        from services.translation_service import split_translated_result as _split_translated_result
        translated_block_texts = _split_translated_result(merged_translation, original_blocks)
        logger.info(f"任务 {task.task_id} 合并块 {index+1} 拆分结果: {translated_block_texts}")

        # 获取合并块的最大宽度（高度不再使用最大值，各块保留原始高度）
        max_width = merged_block.max_width

        # 准备拆分后的结果
        block_results = []
        for j, block_text in enumerate(translated_block_texts):
            original_block_info = original_blocks[j]
            text_block = original_block_info  # 获取TextBlock对象
            page_num = original_block_info.page_num

            # 更新原始文本框：宽度使用合并块最大宽度，高度使用原始块自身高度
            original_bbox = text_block.block_bbox
            if max_width > 0:
                # 计算新的边界框：所有拆分块统一使用合并块的完整宽度
                # 从 original_blocks 计算合并块的左右边界（MergedBlock 无 block_bbox 属性）
                merged_x0 = min(b.block_bbox[0] for b in merged_block.original_blocks)
                merged_x1 = max(b.block_bbox[2] for b in merged_block.original_blocks)
                # x0=合并块左边界, x1=合并块右边界, y/h保留原始块自身值
                new_bbox = (merged_x0, original_bbox[1], merged_x1, original_bbox[3])
            else:
                new_bbox = original_bbox

            # 使用 copy() 方法创建翻译后的 TextBlock 对象
            translated_text_block = text_block.copy()
            translated_text_block.block_text = block_text
            translated_text_block.block_bbox = new_bbox
            translated_text_block.page_num = page_num

            # 更新样式信息 - 使用每个拆分块的原始样式
            translated_text_block.update_style(
                font=text_block.font,
                font_size=text_block.font_size,
                color=text_block.color,
                flags=text_block.flags
            )

            # 记录每个拆分块使用的原始样式
            logger.info(f"任务 {task.task_id} 拆分块 {j+1} 使用原始样式: 字体={text_block.font}, 字体大小={text_block.font_size}")

            block_results.append((page_num, translated_text_block))

        return translated_merged_block, block_results, page_num

    def process_merged_blocks(self, task, merged_blocks, translator, source_lang, target_lang, doc_type, glossary):
        """处理语义合并后的块

        Args:
            task: 任务对象
            merged_blocks: 合并后的块
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表

        Returns:
            tuple: (page_translated_blocks_dict, merged_translations, translated_blocks)
        """
        translated_blocks = 0
        total_blocks = len(merged_blocks)

        # 动态构建页面级别的翻译结果字典
        page_translated_blocks_dict = {}
        # 线程安全的结果收集
        merged_translations = []
        results_lock = threading.Lock()

        # 使用类的线程池实例并行翻译
        # 提交所有翻译任务
        future_to_block = {self.executor.submit(self.translate_merged_block, task, block, i, translator, source_lang, target_lang, doc_type, glossary, total_blocks): (block, i)
                         for i, block in enumerate(merged_blocks)}

        # 收集所有结果，保存原始索引
        results = {}
        completed_blocks = 0

        for future in as_completed(future_to_block):
            try:
                block, index = future_to_block[future]
                translated_merged_block, block_results, page_num = future.result()

                with results_lock:
                    # 保存结果和原始索引
                    results[index] = (translated_merged_block, block_results)

                    completed_blocks += 1
                    phase_percent = int((completed_blocks / total_blocks) * 100)
                    task.update_phase_progress('translation', phase_percent, f'正在翻译: {completed_blocks}/{total_blocks} 个文本块')

            except Exception as e:
                logger.error(f"任务 {task.task_id} 翻译合并块时出错: {str(e)}")
                # 回退到原文，避免空白
                block, index = future_to_block[future]
                results[index] = (block, [
                    (b.page_num, b.copy()) for b in block.original_blocks
                ])

        # 所有任务完成后，按原始顺序处理结果
        for index in sorted(results.keys()):
            translated_merged_block, block_results = results[index]

            # 添加到合并结果列表（按原始顺序）
            merged_translations.append(translated_merged_block)

            # 处理拆分后的结果
            for page_num, translated_text_block in block_results:
                # 动态创建页面对象（如果不存在）
                if page_num not in page_translated_blocks_dict:
                    page_translated_blocks_dict[page_num] = PdfPage(page_num, [])
                # 添加到对应页面的翻译结果中
                page_translated_blocks_dict[page_num].text_blocks.append(translated_text_block)
                translated_blocks += 1

        return page_translated_blocks_dict, merged_translations, translated_blocks

    def _is_translation_unchanged(self, translated_text: str, original_text: str) -> bool:
        """判断翻译结果是否实质上未翻译（含 LLM 自行添加 ||| 等格式符的情况）

        Args:
            translated_text: LLM 返回的翻译结果
            original_text: 原始文本

        Returns:
            True 表示实质上未翻译，False 表示已翻译
        """
        # 快速路径：完全相同
        if translated_text == original_text:
            return True

        # 检测 LLM 是否在原文基础上自行添加了 ||| 分隔符但未翻译
        # 例如: 原文 "A B" → 结果 "A ||| B"
        if '|||' in translated_text:
            # 剥离 ||| 及其前后空白
            parts = re.split(r'\s*\|\|\|\s*', translated_text)
            parts = [p.strip() for p in parts if p.strip()]

            if not parts:
                return False

            # 将原文按空白拆分为候选词
            original_words = set(original_text.split())

            # 检查每个分段是否都来自原文（允许微小空白差异）
            for part in parts:
                part_clean = part.strip()
                if not part_clean:
                    continue
                # 分段必须在原文中能找到（作为子串或词）
                if part_clean not in original_text and part_clean not in original_words:
                    return False

            # 所有分段都来自原文 → 未翻译（只是被 ||| 分隔了）
            return True

        return False

    def translate_original_block(self, task, block_info, index, translator, source_lang, target_lang, doc_type, glossary, total_blocks):
        """翻译单个原始块

        Args:
            task: 任务对象
            block_info: 原始块信息
            index: 块索引
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            total_blocks: 总块数

        Returns:
            tuple: (page_num, translated_text_block, translated_merged_block)
        """
        text_block = block_info
        page_num = block_info.page_num

        logger.info(f"任务 {task.task_id} 处理原始块 {index+1}/{total_blocks}")
        logger.info(f"任务 {task.task_id} 原始块 {index+1} 原文: {text_block.block_text}")

        if getattr(text_block, 'is_formula', False):
            translated_text_block = text_block.copy()
            translated_text_block.block_text = text_block.block_text
            translated_text_block.update_style(
                font=text_block.font,
                font_size=text_block.font_size,
                color=text_block.color,
                flags=text_block.flags
            )
            from models.merged_block import MergedBlock
            bbox = text_block.block_bbox
            width = bbox[2] - bbox[0] if len(bbox) >= 4 else 0
            height = bbox[3] - bbox[1] if len(bbox) >= 4 else 0
            translated_merged_block = MergedBlock(
                block_text=text_block.block_text,
                original_blocks=[block_info],
                max_width=width,
                max_height=height
            )
            return page_num, translated_text_block, translated_merged_block

        logger.info(f"任务 {task.task_id} 原始块 {index+1} 是正文块，开始翻译")
        # 调用翻译API
        logger.info(f'翻译请求: 原文前100字符="{text_block.block_text[:100]}", 长度={len(text_block.block_text)}')
        translation_result = translator.translate(
            text_block.block_text,
            source_lang,
            target_lang,
            doc_type=doc_type,
            glossary=glossary
        )
        translated_text = translation_result.content
        logger.info(f'翻译结果: 结果前200字符="{translated_text[:200]}", 长度={len(translated_text)}')
        if self._is_translation_unchanged(translated_text, text_block.block_text):
            logger.warning(f'翻译结果与原文实质相同（可能未翻译）: 原文前100字符="{text_block.block_text[:100]}", 结果前200字符="{translated_text[:200]}"')
        logger.info(f"任务 {task.task_id} 原始块 {index+1} 翻译结果: {translated_text}")

        # 检查是否被截断
        if translation_result.truncated:
            logger.warning(f"任务 {task.task_id} 原始块 {index+1} 翻译被截断: {translation_result.truncation_info}")
            # 添加警告到任务对象
            task.add_warning("翻译被截断", {
                "process": "translation",
                "block_index": index,
                "token_usage": translation_result.token_usage,
                "finish_reason": translation_result.finish_reason
            })

        # 保存翻译结果，用于Word生成
        from models.merged_block import MergedBlock

        # 计算块的宽度和高度
        bbox = text_block.block_bbox
        width = bbox[2] - bbox[0] if len(bbox) >= 4 else 0
        height = bbox[3] - bbox[1] if len(bbox) >= 4 else 0

        # 创建新的 MergedBlock 对象，使用翻译后的文本作为 block_text
        translated_merged_block = MergedBlock(
            block_text=translated_text,
            original_blocks=[block_info],
            max_width=width,
            max_height=height
        )

        # 使用 copy() 方法创建翻译后的 TextBlock 对象
        translated_text_block = text_block.copy()
        translated_text_block.block_text = translated_text

        # 更新样式信息
        translated_text_block.update_style(
            font=text_block.font,
            font_size=text_block.font_size,
            color=text_block.color,
            flags=text_block.flags
        )

        return page_num, translated_text_block, translated_merged_block

    def process_original_blocks(self, task, text_blocks, translator, source_lang, target_lang, doc_type, glossary):
        """直接处理原始块（不进行语义合并）

        Args:
            task: 任务对象
            text_blocks: 所有原始块
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表

        Returns:
            tuple: (page_translated_blocks_dict, merged_translations, translated_blocks)
        """
        total_original_blocks = len(text_blocks)
        translated_blocks = 0

        # 动态构建页面级别的翻译结果字典
        page_translated_blocks_dict = {}
        # 保存翻译结果，用于Word生成
        merged_translations = []
        # 线程安全的结果收集
        results_lock = threading.Lock()

        # 使用类的线程池实例并行翻译
        # 提交所有翻译任务
        future_to_block = {self.executor.submit(self.translate_original_block, task, block, i, translator, source_lang, target_lang, doc_type, glossary, total_original_blocks): (block, i)
                         for i, block in enumerate(text_blocks)}

        # 收集所有结果，保存原始索引
        results = {}
        completed_blocks = 0

        for future in as_completed(future_to_block):
            try:
                block, index = future_to_block[future]
                page_num, translated_text_block, translated_merged_block = future.result()

                with results_lock:
                    # 保存结果和原始索引
                    results[index] = (page_num, translated_text_block, translated_merged_block)

                    completed_blocks += 1
                    phase_percent = int((completed_blocks / total_original_blocks) * 100)
                    task.update_phase_progress('translation', phase_percent, f'正在翻译: {completed_blocks}/{total_original_blocks} 个文本块')

            except Exception as e:
                logger.error(f"任务 {task.task_id} 翻译原始块时出错: {str(e)}")
                # 回退到原文，避免空白
                block, index = future_to_block[future]
                from models.merged_block import MergedBlock
                bbox = block.block_bbox
                width = bbox[2] - bbox[0] if len(bbox) >= 4 else 0
                height = bbox[3] - bbox[1] if len(bbox) >= 4 else 0
                fallback_merged = MergedBlock(
                    block_text=block.block_text,
                    original_blocks=[block],
                    max_width=width,
                    max_height=height
                )
                fallback_text_block = block.copy()
                results[index] = (block.page_num, fallback_text_block, fallback_merged)

        # 所有任务完成后，按原始顺序处理结果
        for index in sorted(results.keys()):
            page_num, translated_text_block, translated_merged_block = results[index]

            # 添加到合并结果列表（按原始顺序）
            merged_translations.append(translated_merged_block)

            # 动态创建页面对象（如果不存在）
            if page_num not in page_translated_blocks_dict:
                page_translated_blocks_dict[page_num] = PdfPage(page_num, [])

            # 添加到对应页面的翻译结果中
            page_translated_blocks_dict[page_num].text_blocks.append(translated_text_block)
            translated_blocks += 1

        return page_translated_blocks_dict, merged_translations, translated_blocks
