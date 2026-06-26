"""完整的翻译管道测试：第6页藏文→中文，使用qianfan+deepseek-ocr"""
import os, sys, uuid, json, logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from dotenv import load_dotenv
load_dotenv()

# 查找PDF
import glob
pdf_files = sorted(glob.glob('uploads/*W3PD1098*'))
if not pdf_files:
    print("ERROR: No PDF found in uploads/")
    sys.exit(1)

pdf_path = pdf_files[-1]  # 最新的
print(f"PDF: {pdf_path}")

# 创建模拟任务
class MockTask:
    def __init__(self):
        self.task_id = f"test_{uuid.uuid4().hex[:8]}"
        self._status = 'pending'
        self._canceled = False

    def set_status(self, status):
        self._status = status
        print(f"  [Task] 状态 -> {status}")

    def is_canceled(self):
        return self._canceled

    def update_phase_progress(self, phase, progress, message):
        print(f"  [Progress] {phase}: {progress}% - {message}")
        return True

# 确保必要的service模块可以被导入
sys.path.insert(0, '.')
from services.translation_service import TranslationService

service = TranslationService()
task = MockTask()

unique_id = uuid.uuid4().hex[:8]

print("\n===== 开始翻译管道 =====")
print(f"源语言: bo (藏文)")
print(f"目标语言: zh (中文)")
print(f"翻译器: qianfan")
print(f"OCR模式: True, 引擎: llm")
print(f"页码范围: 6")

result = service.process_translation_sync(
    task=task,
    input_filepath=pdf_path,
    source_lang='bo',
    target_lang='zh',
    translator_type='qianfan',
    unique_id=unique_id,
    filename=os.path.basename(pdf_path),
    page_range="6",
    output_format="pdf",
    semantic_merge=False,
    use_llm_merging=False,
    chapter_split=False,
    ocr_mode=True,
    ocr_engine='llm',
    ocr_lang='bo',
    is_cli=True,
)

print(f"\n===== 结果 =====")
if result:
    print(f"✅ 翻译成功! 输出文件: {result}")
else:
    print(f"❌ 翻译失败")