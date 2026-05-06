import asyncio

print("=" * 50)
print("2. async, await 演示")
print("=" * 50)

async def fetch_data(delay, name):
    await asyncio.sleep(delay)
    return f"{name} 数据获取完成"

async def main():
    print("开始异步任务...")

    result1 = await fetch_data(0.1, "任务A")
    print(result1)

    result2 = await fetch_data(0.1, "任务B")
    print(result2)

    results = await asyncio.gather(
        fetch_data(0.1, "并行任务1"),
        fetch_data(0.1, "并行任务2"),
        fetch_data(0.1, "并行任务3")
    )
    print("并行任务结果:", results)

asyncio.run(main())