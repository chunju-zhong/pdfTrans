import os, base64
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

TMP = os.environ.get('TMPDIR', '/tmp')

# Read original PNG
with open('temp_images/llm_ocr_page_6.png', 'rb') as f:
    png_data = f.read()
png_b64 = base64.b64encode(png_data).decode()
print(f'Test 1 - Original PNG base64: {len(png_b64)/1024:.0f}KB')

# Test with half-size image
from PIL import Image
import io
img = Image.open('temp_images/llm_ocr_page_6.png')
w, h = img.size
img_resized = img.resize((w//2, h//2), Image.LANCZOS)
buf = io.BytesIO()
img_resized.save(buf, 'PNG')
half_b64 = base64.b64encode(buf.getvalue()).decode()
print(f'Test 2 - Half size PNG base64: {len(half_b64)/1024:.0f}KB')

# Test: JPEG
buf = io.BytesIO()
img.save(buf, 'JPEG', quality=85)
jpg_b64 = base64.b64encode(buf.getvalue()).decode()
print(f'Test 3 - JPEG base64: {len(jpg_b64)/1024:.0f}KB')

# Test: Half JPEG
buf = io.BytesIO()
img_resized.save(buf, 'JPEG', quality=85)
half_jpg_b64 = base64.b64encode(buf.getvalue()).decode()
print(f'Test 4 - Half size JPEG base64: {len(half_jpg_b64)/1024:.0f}KB')

client = OpenAI(
    base_url=os.environ.get('QIANFAN_API_URL', 'https://qianfan.baidubce.com/v2'),
    api_key=os.environ.get('QIANFAN_API_KEY', ''),
    timeout=300
)

for name, fmt_prefix, b64_data, prompt_text in [
    ('Half JPEG simple', 'image/jpeg', half_jpg_b64, 'OCR this image.'),
    ('Half JPEG deepseek', 'image/jpeg', half_jpg_b64, '<image>\n<|grounding|>Convert the document to markdown.'),
    ('Half PNG simple', 'image/png', half_b64, 'OCR this image.'),
]:
    try:
        r = client.chat.completions.create(
            model='deepseek-ocr',
            messages=[{'role': 'user', 'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:{fmt_prefix};base64,{b64_data}'}},
                {'type': 'text', 'text': prompt_text}
            ]}],
            max_tokens=8192
        )
        text = r.choices[0].message.content
        print(f'\n{name}: OK, len={len(text)}')
        print(f'First 300: {text[:300]}')
        print(f'Last 300: {text[-300:]}')
    except Exception as e:
        print(f'\n{name}: FAILED - {e}')
