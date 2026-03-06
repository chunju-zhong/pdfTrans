import time
import os
import logging
from services.glossary_service import GlossaryService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestGlossaryService:
    """测试术语提取服务"""
    
    def __init__(self):
        """初始化测试类"""
        self.glossary_service = GlossaryService()
    
    def test_single_pdf(self, pdf_path, source_lang='English', target_lang='Chinese', extractor_type='aiping'):
        """测试单个PDF文件的术语提取
        
        Args:
            pdf_path (str): PDF文件路径
            source_lang (str): 源语言
            target_lang (str): 目标语言
            extractor_type (str): 提取器类型
        """
        logger.info(f"测试单个PDF文件: {pdf_path}")
        
        start_time = time.time()
        glossary = self.glossary_service.extract_glossary_from_pdf(
            pdf_path=pdf_path,
            source_lang=source_lang,
            target_lang=target_lang,
            extractor_type=extractor_type
        )
        end_time = time.time()
        
        logger.info(f"提取完成，耗时: {end_time - start_time:.2f} 秒")
        logger.info(f"提取到的术语数: {len(glossary.split('\n')) if glossary else 0}")
        
        return glossary, end_time - start_time
    
    def test_multiple_pdfs(self, pdf_paths, source_lang='English', target_lang='Chinese', extractor_type='aiping'):
        """测试多个PDF文件的术语提取
        
        Args:
            pdf_paths (list[str]): PDF文件路径列表
            source_lang (str): 源语言
            target_lang (str): 目标语言
            extractor_type (str): 提取器类型
        """
        logger.info(f"测试多个PDF文件，共 {len(pdf_paths)} 个")
        
        start_time = time.time()
        
        # 单线程处理
        single_thread_results = {}
        for pdf_path in pdf_paths:
            glossary, _ = self.test_single_pdf(pdf_path, source_lang, target_lang, extractor_type)
            single_thread_results[pdf_path] = glossary
        
        single_thread_time = time.time() - start_time
        logger.info(f"单线程处理耗时: {single_thread_time:.2f} 秒")
        
        # 多线程处理
        start_time = time.time()
        
        # 由于当前的GlossaryService没有提供批量处理的方法，我们模拟并发处理
        import concurrent.futures
        multi_thread_results = {}
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_pdf = {
                executor.submit(
                    self.glossary_service.extract_glossary_from_pdf, 
                    pdf_path, 
                    source_lang, 
                    target_lang, 
                    extractor_type
                ): pdf_path for pdf_path in pdf_paths
            }
            
            for future in concurrent.futures.as_completed(future_to_pdf):
                pdf_path = future_to_pdf[future]
                try:
                    glossary = future.result()
                    multi_thread_results[pdf_path] = glossary
                except Exception as e:
                    logger.error(f"处理PDF文件 {pdf_path} 时出错: {str(e)}")
                    multi_thread_results[pdf_path] = ""
        
        multi_thread_time = time.time() - start_time
        logger.info(f"多线程处理耗时: {multi_thread_time:.2f} 秒")
        logger.info(f"性能提升: {single_thread_time / multi_thread_time:.2f} 倍")
        
        return single_thread_results, multi_thread_results, single_thread_time, multi_thread_time
    
    def test_edge_cases(self):
        """测试边缘情况"""
        logger.info("测试边缘情况")
        
        # 测试不存在的文件
        logger.info("测试不存在的文件")
        glossary, time_taken = self.test_single_pdf("non_existent_file.pdf")
        logger.info(f"不存在的文件测试完成，耗时: {time_taken:.2f} 秒")
        
        # 测试空PDF文件（如果存在）
        empty_pdf = "test_empty.pdf"
        if os.path.exists(empty_pdf):
            logger.info("测试空PDF文件")
            glossary, time_taken = self.test_single_pdf(empty_pdf)
            logger.info(f"空PDF文件测试完成，耗时: {time_taken:.2f} 秒")
        
        # 测试只有一页的PDF文件
        one_page_pdf = "test_one_page.pdf"
        if os.path.exists(one_page_pdf):
            logger.info("测试只有一页的PDF文件")
            glossary, time_taken = self.test_single_pdf(one_page_pdf)
            logger.info(f"只有一页的PDF文件测试完成，耗时: {time_taken:.2f} 秒")
    
    def test_different_sizes(self):
        """测试不同大小的PDF文件"""
        logger.info("测试不同大小的PDF文件")
        
        # 假设我们有不同大小的PDF文件
        pdf_files = [
            "small_file.pdf",  # 小文件
            "medium_file.pdf",  # 中等文件
            "large_file.pdf"  # 大文件
        ]
        
        results = {}
        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                logger.info(f"测试文件: {pdf_file}")
                file_size = os.path.getsize(pdf_file) / (1024 * 1024)  # 转换为MB
                logger.info(f"文件大小: {file_size:.2f} MB")
                
                glossary, time_taken = self.test_single_pdf(pdf_file)
                results[pdf_file] = {
                    "size": file_size,
                    "time": time_taken,
                    "terms": len(glossary.split('\n')) if glossary else 0
                }
        
        # 打印结果
        logger.info("不同大小PDF文件测试结果:")
        for pdf_file, result in results.items():
            logger.info(f"{pdf_file}: 大小={result['size']:.2f} MB, 耗时={result['time']:.2f} 秒, 术语数={result['terms']}")
    
    def test_thread_pool_sizes(self, pdf_path):
        """测试不同线程池大小的性能
        
        Args:
            pdf_path (str): PDF文件路径
        """
        logger.info("测试不同线程池大小的性能")
        
        if not os.path.exists(pdf_path):
            logger.warning(f"文件不存在: {pdf_path}")
            return
        
        # 测试不同的线程池大小
        thread_pool_sizes = [1, 2, 4, 8, 16]
        results = {}
        
        for size in thread_pool_sizes:
            logger.info(f"测试线程池大小: {size}")
            
            # 创建新的GlossaryService实例，设置线程池大小
            service = GlossaryService(max_workers=size)
            
            start_time = time.time()
            glossary = service.extract_glossary_from_pdf(
                pdf_path=pdf_path,
                source_lang='English',
                target_lang='Chinese',
                extractor_type='aiping'
            )
            end_time = time.time()
            
            time_taken = end_time - start_time
            results[size] = {
                "time": time_taken,
                "terms": len(glossary.split('\n')) if glossary else 0
            }
            
            logger.info(f"线程池大小 {size}: 耗时={time_taken:.2f} 秒, 术语数={results[size]['terms']}")
        
        # 打印结果
        logger.info("不同线程池大小测试结果:")
        for size, result in results.items():
            logger.info(f"线程池大小 {size}: 耗时={result['time']:.2f} 秒, 术语数={result['terms']}")

if __name__ == "__main__":
    test = TestGlossaryService()
    
    # 测试边缘情况
    test.test_edge_cases()
    
    # 测试不同大小的PDF文件
    test.test_different_sizes()
    
    # 测试不同线程池大小
    test_pdf = "test_pdf.pdf"
    if os.path.exists(test_pdf):
        test.test_thread_pool_sizes(test_pdf)
    
    # 测试多个PDF文件
    pdf_files = ["test_pdf.pdf"]
    if pdf_files:
        test.test_multiple_pdfs(pdf_files)
