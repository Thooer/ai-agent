print("=" * 50)
print("5. pass, with, yield 演示")
print("=" * 50)

print("--- pass: 占位语句 ---")
class EmptyClass:
    pass

def not_implemented_yet():
    pass

def unimplemented_function():
    pass

print("创建了 EmptyClass 实例:", EmptyClass())
print("调用 not_implemented_yet():", not_implemented_yet())

print("\n--- with: 上下文管理器 ---")
class FileManager:
    def __init__(self, filename):
        self.filename = filename
        self.file = None

    def __enter__(self):
        self.file = open(self.filename, 'w')
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        return False

with FileManager('demo.txt') as f:
    f.write("Hello, World!")

with open('demo.txt', 'r') as f:
    print("写入文件内容:", f.read())

import os
os.remove('demo.txt')

print("\n--- yield: 生成器 ---")
def count_up_to(n):
    count = 1
    while count <= n:
        yield count
        count += 1

counter = count_up_to(5)
print("使用 yield 生成数据:")
for num in counter:
    print(f"  生成: {num}")

print("\n手动获取生成器值:")
gen = count_up_to(3)
print(f"next(gen): {next(gen)}")
print(f"next(gen): {next(gen)}")
print(f"next(gen): {next(gen)}")