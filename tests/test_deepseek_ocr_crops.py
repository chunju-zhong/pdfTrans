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

# Test A: tiny 10x10 crop
tiny = img.crop((0, 0, 10, 10))
buf = io.BytesIO()
tiny.save(buf, 'PNG')
tiny_b64 = base64.b64encode(buf.getvalue()).decode()
print(f'A) 10x10 crop: {len(tiny_b64)/1024:.0f}KB')

# Test B: 100x50 crop (a small strip that might have text)
crop = img.crop((0, 0, 100, 50))
buf = io.BytesIO()
crop.save(buf, 'PNG')
crop_b64 = base64.b64encode(buf.getvalue()).decode()
print(f'B) 100x50 crop: {len(crop_b64)/1024:.0f}KB')

# Test C: 200x100 crop
crop2 = img.crop((0, 0, 200, 100))
buf = io.BytesIO()
crop2.save(buf, 'PNG')
crop2_b64 = base64.b64encode(buf.getvalue()).decode()
print(f'C) 200x100 crop: {len(crop2_b64)/1024:.0f}KB')

for name, b64, mt in [('A) 10x10', tiny_b64, 50), ('B) 100x50', crop_b64, 50), ('C) 200x100', crop2_b64, 50)]:
    try:
        r = client.chat.completions.create(
            model='deepseek-ocr',
            messages=[{'role': 'user', 'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{b64}'}},
                {'type': 'text', 'text': 'OCR this image.'}
            ]}],
            max_tokens=mt
        )
        text = r.choices[0].message.content
        print(f'{name}: OK (len={len(text)}) - {text[:100]}')
    except Exception as e:
        print(f'{name}: FAILED - {e}')

# Test D: full JPEG with max_tokens=50
print(f'D) Full JPEG: {len(full_jpg_b64)/1024:.0f}KB')
try:
    r = client.chat.completions.create(
        model='deepseek-ocr',
        messages=[{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{full_jpg_b64}'}},
            {'type': 'text', 'text': 'OCR this image.'}
        ]}],
        max_tokens=50
    )
    text = r.choices[0].message.content
    print(f'D: OK (len={len(text)}) - {text[:100]}')
except Exception as e:
    print(f'D: FAILED - {e}')
