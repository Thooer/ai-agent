print("=" * 50)
print("1. lambda, global, nonlocal 演示")
print("=" * 50)

counter = 0

def outer():
    count = 0

    def inner():
        nonlocal count
        count += 1
        return count

    increment = lambda: count + 10
    return inner, increment

inner_func, lambda_func = outer()

print(f"global counter (外部): {counter}")
print(f"lambda 增加 10: {lambda_func()}")
print(f"nonlocal 增加 1: {inner_func()}")

def modify_global():
    global counter
    counter += 100

print(f"调用 modify_global() 前: {counter}")
modify_global()
print(f"调用 modify_global() 后: {counter}")