import os, base64, io
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from PIL import Image

client = OpenAI(
    base_url=os.environ.get('QIANFAN_API_URL', 'https://qianfan.baidubce.com/v2'),
    api_key=os.environ.get('QIANFAN_API_KEY', ''),
    timeout=120
)

img = Image.open('temp_images/llm_ocr_page_6.png')
w, h = img.size
print(f'Page 6: {w}x{h}px')

# Test: full image as JPEG with max_tokens=50
buf = io.BytesIO()
img.save(buf, 'JPEG', quality=85)
full_b64 = base64.b64encode(buf.getvalue()).decode()
print(f'Full JPEG: {len(full_b64)/1024:.0f}KB base64')

try:
    r = client.chat.completions.create(
        model='deepseek-ocr',
        messages=[{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{full_b64}'}},
            {'type': 'text', 'text': 'OCR this image.'}
        ]}],
        max_tokens=50
    )
    text = r.choices[0].message.content
    print(f'Full image max_tokens=50: OK, len={len(text)}')
    print(f'Result: {text[:300]}')
except Exception as e:
    print(f'Full image max_tokens=50: FAILED - {e}')

# Test: full image with max_tokens=8192
try:
    r = client.chat.completions.create(
        model='deepseek-ocr',
        messages=[{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{full_b64}'}},
            {'type': 'text', 'text': 'OCR this image.'}
        ]}],
        max_tokens=8192
    )
    text = r.choices[0].message.content
    print(f'Full image max_tokens=8192: OK, len={len(text)}')
    print(f'First 200: {text[:200]}')
    print(f'Last 200: {text[-200:]}')
except Exception as e:
    print(f'Full image max_tokens=8192: FAILED - {e}')
