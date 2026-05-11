# JWT 鉴权

> 本任务在 RAG 跑通后补上，阶段一先占位，不影响其他任务推进。

为接口加 JWT 鉴权，实现用户隔离。未携带有效 token 的请求返回 HTTP 401。

---

## 设计原则

- 只做 stateless JWT，不做 session，不引入额外存储
- Token 由后端签发，前端存 localStorage（演示场景，非生产安全标准）
- 用户数据隔离：conversation / message 查询时过滤 `user_id = current_user.id`，防止越权访问

---

## Token 结构

```json
{
  "sub": "user_id",
  "exp": 1234567890
}
```

签发和校验用 `python-jose`（或 `PyJWT`），密钥从 `SECRET_KEY` 环境变量读取。

---

## 接口改造

新增两个接口：

```
POST /auth/register   # 注册，返回 JWT
POST /auth/login      # 登录，返回 JWT
```

现有需要鉴权的接口统一加 `current_user: User = Depends(get_current_user)` 依赖注入，`get_current_user` 从 `Authorization: Bearer <token>` 中解析并校验 token。

---

## 用户隔离

- `GET /conversations` 只返回 `current_user` 的 conversation
- `POST /ai/chat` 用 `current_user.id` 替换请求体里的 `user_id`（防止客户端伪造）
- `rate_limiter` 已按 `user_id` 隔离，鉴权接入后直接用 `current_user.id`

---

## 不做的事

- Token 刷新（refresh token）：演示场景不需要
- Token 黑名单（注销）：不做，Token 自然过期即可
- RBAC / 权限分级：当前只有普通用户角色

---

## 实现文件

| 文件 | 变更 |
|------|------|
| `core/security.py` | 新建，JWT 签发 / 校验，`get_current_user` 依赖函数 |
| `routers/auth.py` | 新建，`/auth/register` 和 `/auth/login` 接口 |
| `routers/conversations.py` | 接入 `get_current_user`，过滤 user_id |
| `routers/messages.py` | 接入 `get_current_user`，校验 conversation 归属 |
| `routers/ai_chat.py` | 接入 `get_current_user`，user_id 从 token 取 |
| `main.py` | 注册 auth router |
| `requirements.txt` | 新增 `python-jose[cryptography]` 或 `PyJWT` |
| `.env.example` | 新增 `SECRET_KEY` |
