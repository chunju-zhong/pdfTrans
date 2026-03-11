import fitz

# 测试resolve_named_dest方法是否存在
doc = fitz.open()

# 检查Document对象是否有resolve_named_dest方法
if hasattr(doc, 'resolve_named_dest'):
    print("✓ resolve_named_dest方法存在")
    # 尝试调用方法（可能会失败，因为这是一个空文档）
    try:
        result = doc.resolve_named_dest("test")
        print(f"  调用结果: {result}")
    except Exception as e:
        print(f"  调用异常: {e}")
else:
    print("✗ resolve_named_dest方法不存在")

# 检查Document对象的所有方法
print("\nDocument对象的方法:")
methods = [method for method in dir(doc) if not method.startswith('_')]
for method in sorted(methods):
    if 'dest' in method.lower():
        print(f"  - {method}")

doc.close()