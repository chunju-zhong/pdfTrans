#!/usr/bin/env python3
"""测试藏文翻译 - 多模型对比"""
from openai import OpenAI
from config import config

client = OpenAI(
    base_url=config.AIPING_API_URL,
    api_key=config.AIPING_API_KEY,
    timeout=60.0,
)

MODELS = ["Qwen3-32B", "GLM-4.7-Flash", "GLM-5.1", "Doubao-Seed-2.0-pro", "DeepSeek-V4-Pro"]

# 测试文本
test_texts = [
    ("目录句式", "སློགས་བམ་ཀ་པར་བཀའ་རྫོགས་པ་ཆེན་པོ་དམ་ཆོས་དགོངས་པ་ཡོངས་འདུས་ལས། ཡང་ཟབ་གསང་བའི་རྡེའུ་མིག་ལ་ལྡེབ་བཞི།"),
    ("教法论述", "རྫོགས་པ་ཆེན་པོ་ནི་སེམས་ཀྱི་རང་བཞིན་འོད་གསལ་བ་སྟེ། ཀུན་གཞི་ཆོས་སྐུའི་ངོ་བོ་ཉིད་དུ་གནས་པའོ།"),
    ("仪轨文", "ཨོཾ་ཨཱཿཧཱུྃ་བཛྲ་གུ་རུ་པདྨ་སིདྡྷི་ཧཱུྃ། བླ་མ་པདྨ་འབྱུང་གནས་ལ་གསོལ་བ་འདེབས།"),
]

# 通用优化版v2提示词
prompt = """你是精通藏传佛教文献的藏译中翻译专家，遵循以下规则：

一、核心原则
1. 忠实直译：只翻译原文明确包含的信息，禁止脑补、添加原文不存在的典籍别名、版本、品类、传承等细节；
2. 术语准确：使用藏传佛教汉译通行术语，不自行创译；
3. 禁止膨胀：翻译长度与原文相当，不添加解释性说明；
4. 仅客观直译目录，不编造作者、虚构典籍别名。

二、关键术语规范（按原文语境选用，不强行套用）
- ལྡེབ་ = 页码（不译作函、品、卷）
- རྡེའུ་མིག = 心髓、窍诀（不译作伏藏、木刻版）
- ཀ་པར = 分函名称，不是数字"第四"
- རྫོགས་པ་ཆེན་པོ = 大圆满
- བཀའ་ = 圣教/甘珠尔
- དགོངས་པ་ = 密意/意趣
- ཡོངས་འདུས་ = 总集
- འོད་གསལ་ = 光明
- ཆོས་སྐུ་ = 法身
- ཀུན་གཞི་ = 阿赖耶
- བླ་མ་ = 上师
- སློགས་བམ་ཀ་པར་=《大圆满圣教密意总集》噶巴分函

三、目录句式识别
当文本出现"Aལས། Bལ་ལྡེབ་数字"句式时，译为"出自A，篇目B见于第数字页"。

四、其他文本类型
- 教法论述：保持论述逻辑，术语准确，不添加解释性扩展；
- 仪轨祈请：保持敬语风格，咒语（嗡啊吽等种子字）音译保留。"""

def translate(model, user_text):
    response = client.chat.completions.create(
        model=model,
        stream=True,
        temperature=0.1,
        top_p=0.9,
        max_tokens=8192,
        extra_body=config.AIPING_EXTRA_BODY,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"翻译藏文：\n{user_text}"}
        ]
    )
    result = ""
    for chunk in response:
        if hasattr(chunk, "choices") and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                result += delta.content
    return result

for label, text in test_texts:
    print(f"\n{'='*70}")
    print(f"【{label}】原文: {text}")
    print(f"{'='*70}")
    for model in MODELS:
        try:
            r = translate(model, text)
            print(f"  {model:25s} → {r}")
        except Exception as e:
            print(f"  {model:25s} → [错误] {e}")
