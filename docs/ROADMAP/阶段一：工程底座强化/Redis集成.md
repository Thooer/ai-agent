# Redis 集成设计

这个项目里 Redis 有三个用途，设计上要分清楚。

---

## 1. Embedding 缓存

同一段文本反复 embed 是纯浪费。以文本内容的 hash 为 key，embedding 向量为 value。

```
key:   embed:{sha256(text)}
value: 二进制序列化的向量（MessagePack 或 numpy tobytes）
TTL:   7d
```

存储格式用二进制序列化而非 JSON 数组，节省 40-60% 内存，序列化/反序列化开销也更小。

Redis 需配置 `maxmemory-policy: volatile-lru`，内存满时自动淘汰最冷的带 TTL 的 key，防止 OOM。

批量写入 chunks 时用 Pipeline，避免 for 循环里发几十次 SET 请求。

---

## 2. 限流

用滑动窗口（ZSET）按用户 ID 限制每分钟的 LLM 调用次数，防止单用户打爆 API 配额。

```
key:   ratelimit:{user_id}
value: ZSET，member 为请求时间戳，score 同 member
TTL:   2 分钟（自动清理）
```

每次请求：
1. `ZREMRANGEBYSCORE` 删掉一分钟前的记录
2. `ZCARD` 统计当前窗口内的请求数
3. 未超限则 `ZADD` 写入当前时间戳

相比固定窗口（INCR + 分钟时间戳），ZSET 滑动窗口避免了跨分钟边界的突发问题。

---

## 3. 任务状态（文档入库进度）

文档解析 + chunking + embedding 是耗时操作，不能同步等。用 Redis Hash 存任务状态，前端轮询或 SSE 推进度。

```
key:    task:{task_id}
value:  Hash
  - status:   pending / processing / done / failed
  - progress: 0-100
  - error:    错误信息（失败时）
TTL:    1h
```

用 HSET 而非 JSON string，支持局部原子更新（如只更新 progress），避免并发场景下的脏写。

后端 worker 更新进度时同步 `PUBLISH task:{task_id}`，SSE 接口 `SUBSCRIBE` 该频道直接推给前端，延迟更低，减少轮询压力。

---

## 设计原则

- key 命名统一用 `{project}:{env}:{module}:{id}` 格式，多项目共用 Redis 时不冲突
- 所有 key 都设 TTL，不留僵尸数据
- embedding 缓存用 GET/SET + Pipeline，限流用 ZSET 滑动窗口，任务状态用 HSET

---

## 实现文件

| 文件 | 作用 |
|------|------|
| `core/redis_client.py` | Redis 单例连接，`get_redis()` 全局复用同一个连接池，`close_redis()` 在应用关闭时释放 |
| `core/config.py` | 新增 `REDIS_URL`、`REDIS_PROJECT_PREFIX` 两个配置项，从 `.env` 读取 |
| `services/embedding_cache.py` | embedding 缓存的读写，向量用 msgpack 二进制序列化，批量写入走 Pipeline |
| `services/rate_limiter.py` | ZSET 滑动窗口限流，`is_rate_limited()` 返回 bool，整个检查+写入在一个 Pipeline 事务里原子执行 |
| `services/task_state.py` | 文档入库任务的状态机，用 HSET 支持局部字段更新，暴露 `create/update_progress/complete/fail/get` 五个函数 |
| `routers/ai_chat.py` | 在 `/ai/chat` 入口接入限流，超限直接返回 HTTP 429 |
| `main.py` | lifespan 里加入 Redis 连接预热和关闭 |
| `postgresql/docker-compose.yml` | 新增 Redis 服务，配置 `--maxmemory 256mb --maxmemory-policy volatile-lru` |
| `requirements.txt` | 新增 `redis[hiredis]==7.4.0`、`msgpack==1.1.2` |

---

## 测试

测试脚本保存在 `tests/test_redis.py`，运行方式：

```bash
python tests/test_redis.py
```

需要 Redis 在 `localhost:6379` 运行（`docker compose up -d` 启动即可）。

覆盖的测试点：

**Embedding 缓存**
- cache miss 返回 None
- set 后 cache hit 返回正确向量
- 不同文本互不干扰
- Pipeline 批量写入后逐条命中
- TTL 已设置

**限流**
- 首次请求不被限流
- 请求计数正确递增
- 达到 50 次上限后触发限流
- 滑动窗口过期后恢复正常（旧记录清除后不再限流）

**任务状态**
- 创建任务初始状态为 pending、progress 为 0
- 更新进度后状态变为 processing
- 完成后状态为 done、progress 为 100
- 失败路径：status 为 failed，error 字段有内容
- 不存在的 task_id 返回 None
- TTL 已设置

手动调试结果（`curl` + Redis CLI）：
- `/health` 返回 `{"status":"ok","database":"connected"}`
- 限流：向 Redis 注入 50 条记录后，第 51 次 `/ai/chat` 请求返回 HTTP 429
- embedding cache 读写、task state 状态流转均验证正常

---

## 备注

- `REDIS_PROJECT_PREFIX` 默认值为 `ai-agent:dev`，生产环境改为 `ai-agent:prod`，多环境共用同一个 Redis 实例时不会串 key
- embedding cache 目前没有 HTTP 接口，RAG 阶段的 ingestion pipeline 直接调用 `services/embedding_cache.py`
- task state 的 Pub/Sub 推进度部分（`PUBLISH/SUBSCRIBE`）在设计里已预留，RAG ingestion 接入时实现
- 限流阈值 `MAX_REQUESTS = 50` 在 `services/rate_limiter.py` 顶部，可按需调整

