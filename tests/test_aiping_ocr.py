import os, base64
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

with open('temp_images/llm_ocr_page_6.png', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()
print(f'Image base64 size: {len(img_b64)/1024:.0f}KB')

client = OpenAI(
    base_url=os.environ.get('AIPING_API_URL', 'https://aiping.cn/api/v1'),
    api_key=os.environ.get('AIPING_API_KEY', ''),
    timeout=300
)
model = os.environ.get('AIPING_OCR_LLM_MODEL', 'DeepSeek-OCR')
print(f'Model: {model}')

try:
    r = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}},
            {'type': 'text', 'text': 'OCR this image.'}
        ]}],
        max_tokens=8192
    )
    text = r.choices[0].message.content
    print(f'OK, len={len(text)}')
    print(f'Result: {text[:500]}')
except Exception as e:
    print(f'AIPING FAILED: {e}')
