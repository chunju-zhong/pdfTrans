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
            semantic_merge = request.form.get('semantic_merge', 'on') == 'on'
            
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
                            args=(task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, doc_type, glossary, page_range, output_format, semantic_merge)).start()
            
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
        'canceled': task.canceled
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

if __name__ == '__main__':
    import sys
    port = 5000
    if len(sys.argv) > 2 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    app.run(host='0.0.0.0', port=port)
