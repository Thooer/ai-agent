def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为零！")
    return a / b

try:
    result = divide(10, 0)
    print(f"结果: {result}")
except ValueError as e:
    print(f"捕获到异常: {e}")
except Exception as e:
    print(f"其他异常: {e}")
finally:
    print("无论如何都会执行 finally 代码块")

print("\n--- 第二次调用，正常的除法 ---")

try:
    result = divide(10, 2)
    print(f"结果: {result}")
except ValueError as e:
    print(f"捕获到异常: {e}")
finally:
    print("无论如何都会执行 finally 代码块")