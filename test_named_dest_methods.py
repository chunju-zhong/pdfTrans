import fitz

# 测试fitz.utils.resolve_named_dest方法是否存在
print("测试fitz.utils.resolve_named_dest方法:")
if hasattr(fitz.utils, 'resolve_named_dest'):
    print("✓ fitz.utils.resolve_named_dest方法存在")
else:
    print("✗ fitz.utils.resolve_named_dest方法不存在")

# 测试doc.dest_to_rect方法是否存在
doc = fitz.open()
print("\n测试doc.dest_to_rect方法:")
if hasattr(doc, 'dest_to_rect'):
    print("✓ doc.dest_to_rect方法存在")
else:
    print("✗ doc.dest_to_rect方法不存在")

# 检查fitz.utils中的其他方法
print("\nfitz.utils中的方法:")
utils_methods = [method for method in dir(fitz.utils) if not method.startswith('_')]
for method in sorted(utils_methods):
    if 'dest' in method.lower():
        print(f"  - {method}")

doc.close()