# JWT 鉴权

文档解析是第一个需要 user_id 的接口，在此之前补上 JWT，接口签名一次写对，不留 dev user 技术债。

---

## 设计原则

- Stateless JWT，不做 session，不引入额外存储
- `python-jose[cryptography]` 签发/校验
- 密钥从 `SECRET_KEY` 环境变量读取
- Token 存前端 localStorage（演示场景，非生产安全标准）
- 不做 refresh token、token 黑名单、RBAC

---

## Token 结构

```json
{
  "sub": "user_id (UUID string)",
  "exp": 1234567890
}
```

过期时间默认 7 天（演示场景，面试不会纠结这个数字）。

---

## 新增接口

```
POST /auth/register   body: {name, email, password}  → {access_token, token_type}
POST /auth/login      body: {email, password}         → {access_token, token_type}
```

密码用 `bcrypt` hash 存库，`users` 表新增 `hashed_password` 字段（Alembic 0004）。

---

## 现有接口改造

`get_current_user` 依赖函数从 `Authorization: Bearer <token>` 解析并校验 token，返回 `User` ORM 对象。

需要鉴权的接口加 `current_user: User = Depends(get_current_user)`：

| 接口 | 改造内容 |
|------|----------|
| `POST /ai/chat` | user_id 从 token 取，不再从 request body 读 |
| `POST /documents/upload` | （阶段二新增）强制鉴权 |
| `GET /documents` | （阶段二新增）只返回当前用户的文档 |
| `GET /conversations` | 过滤 user_id = current_user.id |
| `GET /messages` | 校验 conversation 归属 |

---

## 限流对接

`rate_limiter` 已按 user_id 隔离，JWT 接入后直接用 `current_user.id`，无需改限流逻辑。

---

## 实现文件

| 文件 | 说明 |
|------|------|
| `core/security.py` | JWT 签发/校验，`get_current_user` 依赖函数，bcrypt hash 工具函数 |
| `routers/auth.py` | `/auth/register`、`/auth/login` |
| `alembic/versions/0004_users_password.py` | users 表加 hashed_password 字段 |
| `models/orm.py` | User 模型加 hashed_password 字段 |
| `main.py` | 注册 auth router |
| `requirements.txt` | 新增 `python-jose[cryptography]`、`passlib[bcrypt]` |
| `.env.example` | 新增 `SECRET_KEY` |
