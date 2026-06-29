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
buf = io.BytesIO()
img.save(buf, 'JPEG', quality=85)
full_b64 = base64.b64encode(buf.getvalue()).decode()

# Binary search for max working max_tokens
for mt in [4096, 2048, 1024, 512, 256, 128, 64]:
    try:
        r = client.chat.completions.create(
            model='deepseek-ocr',
            messages=[{'role': 'user', 'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{full_b64}'}},
                {'type': 'text', 'text': 'OCR this image.'}
            ]}],
            max_tokens=mt
        )
        text = r.choices[0].message.content
        print(f'max_tokens={mt}: OK, len={len(text)}, preview={text[:100]}')
    except Exception as e:
        print(f'max_tokens={mt}: FAILED')
