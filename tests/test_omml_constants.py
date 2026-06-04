"""Test OMML conversion for formula with constants"""
import re
from latex2mathml.converter import convert as latex_to_mathml
from lxml import etree
from modules.docx_generator import DocxGenerator

# 模拟 _insert_formula_omml 中的预处理步骤
latex_raw = r'\mathsf{SSP} = 0.6^{*}[(\mathsf{TSS}_{i n}/\mathsf{TBOD}_{S i n}) + 1]-[(0.72^{*}\mathsf{F})/(\mathsf{BA}_{BOD} + (1.33^{*}\mathsf{F}))]'
prev = None
latex = latex_raw
while prev != latex:
    prev = latex
    latex = re.sub(r'\\(?:mathsf|mathrm|mathbf|mathit|mathcal|mathbb|mathfrak|mathscr|mathtt)\{([^}]*)\}', r'\1', latex)

print(f"原始 LaTeX:  {latex_raw}")
print(f"预处理后:    {latex}")
print()

gen = DocxGenerator()
mathml = latex_to_mathml(latex)
mathml_tree = etree.fromstring(mathml.encode('utf-8'))
omml_elem = gen._mathml_to_omml_element(mathml_tree)

if omml_elem is not None:
    omml_str = etree.tostring(omml_elem, pretty_print=True).decode()
    print(omml_str[:5000])

    omml_raw = etree.tostring(omml_elem).decode()
    for num in ['0.6', '0.72', '1.33', '1']:
        found = num in omml_raw
        print(f"  Number {num}: {'FOUND' if found else 'MISSING!'}")
else:
    print("OMML conversion returned None!")
