print("=" * 50)
print("4. in, is 演示")
print("=" * 50)

print("--- in: 检查成员关系 ---")
fruits = ["苹果", "香蕉", "橙子"]
print(f"'香蕉' in fruits: {'香蕉' in fruits}")
print(f"'葡萄' in fruits: {'葡萄' in fruits}")

text = "Hello World"
print(f"'World' in text: {'World' in text}")

print("\n--- is: 检查对象身份 ---")
a = [1, 2, 3]
b = [1, 2, 3]
c = a

print(f"a == b: {a == b}")
print(f"a is b: {a is b}")
print(f"a is c: {a is c}")

x = 256
y = 256
print(f"\n小整数池: x = 256, y = 256")
print(f"x == y: {x == y}")
print(f"x is y: {x is y}")

print("\n--- 字符串驻留 ---")
s1 = "hello"
s2 = "hello"
print(f"s1 is s2: {s1 is s2}")