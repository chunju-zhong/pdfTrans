#!/usr/bin/env python3
"""测试优化后的翻译提示词效果 - 验证"禁止膨胀"和"忠实直译"规则"""
from modules.aiping_translator import AipingTranslator
from config import config

# 测试模型列表
MODELS = ["Qwen3-32B", "GLM-4.7-Flash", "GLM-5.1", "Doubao-Seed-2.0-pro", "DeepSeek-V4-Pro"]

# 测试文本（藏文）
test_texts = [
    ("目录句式", "སློགས་བམ་ཀ་པར་བཀའ་རྫོགས་པ་ཆེན་པོ་དམ་ཆོས་དགོངས་པ་ཡོངས་འདུས་ལས། ཡང་ཟབ་གསང་བའི་རྡེའུ་མིག་ལ་ལྡེབ་བཞི།"),
    ("教法论述", "རྫོགས་པ་ཆེན་པོ་ནི་སེམས་ཀྱི་རང་བཞིན་འོད་གསལ་བ་སྟེ། ཀུན་གཞི་ཆོས་སྐུའི་ངོ་བོ་ཉིད་དུ་གནས་པའོ།"),
    ("仪轨文", "ཨོཾ་ཨཱཿཧཱུྃ་བཛྲ་གུ་རུ་པདྨ་སིདྡྷི་ཧཱུྃ། བླ་མ་པདྨ་འབྱུང་གནས་ལ་གསོལ་བ་འདེབས།"),
]

# 藏文术语表（可选，用于测试术语一致性）
GLOSSARY = """ལྡེབ་: 页码
རྡེའུ་མིག: 心髓、窍诀
ཀ་པར: 分函名称
རྫོགས་པ་ཆེན་པོ: 大圆满
བཀའ་: 圣教/甘珠尔
དགོངས་པ་: 密意/意趣
ཡོངས་འདུས་: 总集
འོད་གསལ་: 光明
ཆོས་སྐུ་: 法身
ཀུན་གཞི་: 阿赖耶
བླ་མ་: 上师"""

def validate_translation(original, translation, label):
    """验证翻译结果是否符合"禁止膨胀"和"忠实直译"规则"""
    issues = []

    # 1. 检查是否包含原文不存在的词汇（膨胀检测）
    forbidden_words = [
        "作者", "大师所著", "木刻版", "伏藏", "版本", "品类",
        "传承", "注释", "注：", "说明：", "备注", "（注）", "[注]",
        "编造", "虚构", "原文未提及"
    ]

    for word in forbidden_words:
        if word in translation:
            issues.append(f"❌ 包含膨胀词汇: '{word}'")

    # 2. 检查翻译长度是否与原文相当（长度膨胀检测）
    # 藏文字符通常比中文短，所以允许翻译长度略长，但不应超过2倍
    original_len = len(original)
    translation_len = len(translation)
    ratio = translation_len / original_len if original_len > 0 else 0

    if ratio > 2.5:
        issues.append(f"❌ 翻译长度膨胀: 原文{original_len}字 → 翻译{translation_len}字 (比例{ratio:.2f})")
    elif ratio > 2.0:
        issues.append(f"⚠️  翻译长度偏长: 原文{original_len}字 → 翻译{translation_len}字 (比例{ratio:.2f})")

    # 3. 检查是否包含英文注释或括号解释
    if any(char in translation for char in ['[', ']', '(', ')']):
        # 允许括号，但不允许英文注释
        if any(eng_word in translation for eng_word in ['note', 'Note', 'comment', 'Comment', 'original']):
            issues.append(f"❌ 包含英文注释")

    # 4. 检查是否包含元注释（如"注："、"说明："等）
    meta_comment_patterns = ["注：", "说明：", "备注：", "注意：", "译者注", "翻译注"]
    for pattern in meta_comment_patterns:
        if pattern in translation:
            issues.append(f"❌ 包含元注释: '{pattern}'")

    # 5. 检查是否输出原文（违反"禁止元注释和原文输出"规则）
    # 如果翻译结果中包含大量藏文原文，说明模型可能混淆了
    tibetan_chars = sum(1 for char in translation if '\u0F00' <= char <= '\u0FFF')
    if tibetan_chars > len(translation) * 0.3:  # 如果超过30%是藏文
        issues.append(f"❌ 翻译结果包含过多原文藏文 ({tibetan_chars}/{len(translation)}字符)")

    return issues

def test_optimized_prompt():
    """测试优化后的提示词效果"""
    print("=" * 80)
    print("测试优化后的翻译提示词效果")
    print("验证规则: 禁止膨胀、忠实直译、无编造")
    print("=" * 80)

    # 先展示生成的系统提示词
    print("\n【生成的系统提示词】")
    print("-" * 80)

    # 创建一个临时翻译器实例来生成提示词
    temp_translator = AipingTranslator(
        api_key=config.AIPING_API_KEY,
        api_url=config.AIPING_API_URL,
        model=MODELS[0]
    )

    # 使用 _generate_system_prompt 方法生成提示词
    system_prompt = temp_translator._generate_system_prompt(
        doc_type="藏传佛教文献",
        source_lang_name="藏文",
        target_lang_name="中文",
        glossary=GLOSSARY
    )

    print(system_prompt)
    print("-" * 80)

    # 测试每个模型
    for model in MODELS:
        print(f"\n{'=' * 80}")
        print(f"测试模型: {model}")
        print(f"{'=' * 80}")

        # 创建翻译器实例
        translator = AipingTranslator(
            api_key=config.AIPING_API_KEY,
            api_url=config.AIPING_API_URL,
            model=model
        )

        # 测试每种文本类型
        for label, text in test_texts:
            print(f"\n【{label}】原文: {text}")
            print("-" * 80)

            try:
                # 使用优化后的提示词进行翻译
                result = translator.translate(
                    text=text,
                    source_lang='bo',  # 藏文
                    target_lang='zh',  # 中文
                    doc_type="藏传佛教文献",
                    glossary=GLOSSARY
                )

                translation = result.content
                print(f"翻译结果: {translation}")

                # 验证翻译结果
                issues = validate_translation(text, translation, label)

                if issues:
                    print(f"\n验证结果: ❌ 未通过")
                    for issue in issues:
                        print(f"  {issue}")
                else:
                    print(f"\n验证结果: ✅ 通过")
                    print(f"  ✓ 无膨胀词汇")
                    print(f"  ✓ 长度适中")
                    print(f"  ✓ 无元注释")
                    print(f"  ✓ 无原文输出")

                # 显示token使用情况
                if result.token_usage:
                    print(f"\nToken使用: {result.token_usage}")

                # 显示截断信息
                if result.truncation_info.truncated:
                    print(f"\n⚠️  翻译被截断: {result.truncation_info.finish_reason}")

            except Exception as e:
                print(f"❌ 翻译失败: {str(e)}")

    print(f"\n{'=' * 80}")
    print("测试完成")
    print("=" * 80)

def test_prompt_comparison():
    """对比优化前后提示词的差异"""
    print("\n" + "=" * 80)
    print("对比优化前后提示词")
    print("=" * 80)

    # 旧版藏文专用提示词（来自 test_bo_translate.py）
    old_prompt = """你是精通藏传佛教文献的藏译中翻译专家，遵循以下规则：

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

    # 新版通用提示词（通过 _generate_system_prompt 生成）
    temp_translator = AipingTranslator(
        api_key=config.AIPING_API_KEY,
        api_url=config.AIPING_API_URL,
        model=MODELS[0]
    )

    new_prompt = temp_translator._generate_system_prompt(
        doc_type="藏传佛教文献",
        source_lang_name="藏文",
        target_lang_name="中文",
        glossary=GLOSSARY
    )

    print("\n【旧版藏文专用提示词】")
    print("-" * 80)
    print(old_prompt[:500] + "...")  # 只显示前500字符
    print("-" * 80)

    print("\n【新版通用提示词】")
    print("-" * 80)
    print(new_prompt[:500] + "...")  # 只显示前500字符
    print("-" * 80)

    print("\n【关键差异】")
    print("1. 新版提示词是通用的，适用于所有语言对")
    print("2. 新版提示词通过参数化生成，更灵活")
    print("3. 新版提示词强调'禁止膨胀'和'忠实直译'为核心原则")
    print("4. 新版提示词包含更详细的格式保持规则")
    print("5. 新版提示词明确禁止元注释和原文输出")

if __name__ == "__main__":
    # 运行主测试
    test_optimized_prompt()

    # 运行对比测试
    test_prompt_comparison()