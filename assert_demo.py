print("=" * 50)
print("3. assert 演示")
print("=" * 50)

def divide(a, b):
    assert b != 0, "除数不能为零"
    return a / b

def login(username, password):
    assert len(username) >= 3, "用户名至少3个字符"
    assert len(password) >= 6, "密码至少6个字符"
    return True

print("测试 divide(10, 2):", divide(10, 2))

try:
    divide(10, 0)
except AssertionError as e:
    print(f"断言失败: {e}")

print("测试 login('john', 'password123'):", login("john", "password123"))

try:
    login("jo", "123")
except AssertionError as e:
    print(f"断言失败: {e}")