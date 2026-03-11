from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
import threading
import fitz  # PyMuPDF用于获取PDF页数
from config import config
from utils.logging_config import setup_logging, get_logger
from utils.file_utils import allowed_file, ensure_directory_exists
from services.task_service import task_service
from services.translation_service import translation_service
from services.glossary_service import glossary_service

# 配置日志
setup_logging()
logger = get_logger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(config)

# 确保上传和输出目录存在
ensure_directory_exists(app.config['UPLOAD_FOLDER'])
ensure_directory_exists(app.config['OUTPUT_FOLDER'])

@app.route('/')
def index():
    """主页路由"""
    return render_template('index.html',
                           supported_languages=config.SUPPORTED_LANGUAGES,
                           default_source=config.DEFAULT_SOURCE_LANGUAGE,
                           default_target=config.DEFAULT_TARGET_LANGUAGE,
                           default_translator=config.DEFAULT_TRANSLATOR,
                           default_doc_type=config.DEFAULT_DOC_TYPE)

@app.route('/translate', methods=['POST'])
def translate():
    """翻译路由（异步）"""
    # 检查请求中是否包含文件
    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    file = request.files['pdf_file']
    
    # 检查文件是否为空
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    # 检查文件类型
    if file and allowed_file(file.filename):
        try:
            # 获取翻译参数
            source_lang = request.form.get('source_lang', config.DEFAULT_SOURCE_LANGUAGE)
            target_lang = request.form.get('target_lang', config.DEFAULT_TARGET_LANGUAGE)
            translator_type = request.form.get('translator', 'silicon_flow')
            doc_type = request.form.get('doc_type', config.DEFAULT_DOC_TYPE)
            glossary = request.form.get('glossary', '')
            page_range = request.form.get('page_range', '')
            output_format = request.form.get('output_format', 'pdf')
            semantic_merge = request.form.get('semantic_merge', '') == 'on'
            use_llm_merging = request.form.get('use_llm_merging', '') == 'on'
            chapter_split = request.form.get('chapter_split', '') == 'on'
            
            # 打印所有参数值
            logger.info(f"前端传递的参数值:")
            logger.info(f"  source_lang: {source_lang}")
            logger.info(f"  target_lang: {target_lang}")
            logger.info(f"  translator_type: {translator_type}")
            logger.info(f"  doc_type: {doc_type}")
            logger.info(f"  page_range: {page_range}")
            logger.info(f"  output_format: {output_format}")
            logger.info(f"  semantic_merge: {semantic_merge}")
            logger.info(f"  use_llm_merging: {use_llm_merging}")
            logger.info(f"  chapter_split: {chapter_split}")
            
            # 保存文件（在主线程中完成）
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())[:8]
            input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
            file.save(input_filepath)
            
            # 创建任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务对象
            task = task_service.create_task(task_id, file.filename)
            task.update_progress(10, '文件保存完成...')
            
            # 启动异步翻译任务，传递文件路径、unique_id和filename
            threading.Thread(target=translation_service.process_translation, 
                            args=(task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, doc_type, glossary, page_range, output_format, semantic_merge, use_llm_merging, chapter_split)).start()
            
            # 返回任务ID
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': '翻译任务已启动'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f"创建任务失败: {str(e)}"})
    
    return jsonify({'success': False, 'message': '不支持的文件类型'})

@app.route('/progress/<task_id>')
def get_progress(task_id):
    """获取任务进度API"""
    task = task_service.get_task(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'status': task.status,
        'progress': task.progress,
        'message': task.message,
        'result_file': task.result_file,
        'attachments': getattr(task, 'attachments', []),
        'error': task.error,
        'canceled': task.canceled,
        'warnings': getattr(task, 'warnings', [])
    })

@app.route('/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """取消翻译任务API"""
    if not task_service.cancel_task(task_id):
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '翻译任务已取消'
    })

@app.route('/download/<filename>')
def download(filename):
    """下载页面路由"""
    return render_template('download.html', filename=filename)

@app.route('/download_file/<filename>')
def download_file(filename):
    """实际文件下载路由"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/get_pdf_pages', methods=['POST'])
def get_pdf_pages():
    """获取PDF文件的总页数"""
    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    file = request.files['pdf_file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        try:
            # 保存临时文件
            temp_filename = secure_filename(file.filename)
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4()}_{temp_filename}")
            file.save(temp_filepath)
            
            # 使用PyMuPDF获取PDF页数
            with fitz.open(temp_filepath) as doc:
                total_pages = len(doc)
            
            # 删除临时文件
            os.remove(temp_filepath)
            
            return jsonify({
                'success': True,
                'total_pages': total_pages
            })
        except Exception as e:
            logger.error(f"获取PDF页数失败: {str(e)}")
            return jsonify({'success': False, 'message': f"获取PDF页数失败: {str(e)}"})
    
    return jsonify({'success': False, 'message': '不支持的文件类型'})

# 术语提取相关路由
@app.route('/extract_glossary', methods=['POST'])
def extract_glossary():
    """提取术语表路由（异步）"""
    # 检查请求中是否包含文件
    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    file = request.files['pdf_file']
    
    # 检查文件是否为空
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})
    
    # 检查文件类型
    if file and allowed_file(file.filename):
        try:
            # 获取参数
            source_lang = request.form.get('source_lang', config.DEFAULT_SOURCE_LANGUAGE)
            target_lang = request.form.get('target_lang', config.DEFAULT_TARGET_LANGUAGE)
            translator_type = request.form.get('translator', 'aiping')
            page_range = request.form.get('page_range', '')
            doc_type = request.form.get('doc_type', config.DEFAULT_DOC_TYPE)
            
            # 解析页码范围
            pages = None
            if page_range:
                try:
                    # 解析页码范围，支持如"1-3,5,7-9"格式
                    page_list = []
                    ranges = page_range.split(',')
                    for r in ranges:
                        r = r.strip()
                        if '-' in r:
                            start, end = r.split('-')
                            page_list.extend(range(int(start), int(end) + 1))
                        else:
                            page_list.append(int(r))
                    # 去重并排序
                    pages = sorted(list(set(page_list)))
                    logger.info(f"解析页码范围: {page_range} -> {pages}")
                except Exception as e:
                    logger.warning(f"解析页码范围失败: {str(e)}")
                    pages = None
            
            # 保存文件
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())[:8]
            input_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"glossary_{unique_id}_{filename}")
            file.save(input_filepath)
            
            # 创建任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务对象
            task = task_service.create_task(task_id, file.filename)
            task.update_progress(10, '文件保存完成...')
            
            # 启动异步术语提取任务
            threading.Thread(target=process_glossary_extraction, 
                            args=(task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, pages, doc_type)).start()
            
            # 返回任务ID
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': '术语提取任务已启动'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': f"创建任务失败: {str(e)}"})
    
    return jsonify({'success': False, 'message': '不支持的文件类型'})

@app.route('/glossary_progress/<task_id>')
def get_glossary_progress(task_id):
    """获取术语提取任务进度API"""
    task = task_service.get_task(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'status': task.status,
        'progress': task.progress,
        'message': task.message,
        'glossary': getattr(task, 'glossary', ''),
        'error': task.error
    })

@app.route('/glossary_cancel/<task_id>', methods=['POST'])
def cancel_glossary_task(task_id):
    """取消术语提取任务API"""
    if not task_service.cancel_task(task_id):
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '术语提取任务已取消'
    })

def process_glossary_extraction(task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, pages=None, doc_type=None):
    """异步术语提取任务处理函数"""
    try:
        logger.info(f"开始处理术语提取任务 {task.task_id}，文件: {filename}")
        # 更新任务状态为处理中
        task.set_status('processing')
        
        # 提取术语表
        task.update_progress(30, '正在提取PDF文本...')
        
        # 调用术语提取服务，传递task对象用于进度更新
        glossary = glossary_service.extract_glossary_from_pdf(
            input_filepath, source_lang, target_lang, translator_type, pages, doc_type, task
        )
        
        task.update_progress(100, '术语提取完成！')
        # 设置任务结果
        task.set_status('completed')
        task.glossary = glossary
        # 修复f-string中的反斜杠问题
        line_count = len(glossary.split('\n')) if glossary else 0
        logger.info(f"任务 {task.task_id} 完成，提取到 {line_count} 个术语")
        
    except Exception as e:
        logger.error(f"术语提取任务失败: {str(e)}")
        task.set_status('error')
        task.error = str(e)
        # 清理临时文件
        if os.path.exists(input_filepath):
            os.remove(input_filepath)

if __name__ == '__main__':
    import sys
    port = 5000
    if len(sys.argv) > 2 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    app.run(host='0.0.0.0', port=port)
