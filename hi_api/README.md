
# hi_api

这是一个最小的 FastAPI 后端骨架示例，方便本地开发和演示。项目以内存存储为示例实现，便于快速运行，后续可以替换为真实数据库（如 SQLite/SQLAlchemy）。

项目结构：

```
hi_api/
├── main.py          # 入口文件（创建 app 实例、注册路由）
├── api/             # 路由模块
│   ├── __init__.py
│   ├── items.py     # 物品相关接口
│   └── users.py     # 用户相关接口
├── models/          # 数据模型（Pydantic 模型）
│   ├── __init__.py
│   ├── item.py      # Item, ItemCreate
│   └── user.py      # User, UserCreate
├── services/        # 业务逻辑层（内存实现，便于替换为 DB）
│   ├── __init__.py
│   ├── item_service.py
│   └── user_service.py
├── db/              # 数据库相关（占位实现）
│   ├── __init__.py
│   └── database.py
└── utils/           # 工具函数（认证示例）
		├── __init__.py
		└── auth.py
```

各文件说明（简要）：

- `main.py`
	- 创建 FastAPI 应用并包含路由模块。
	- 可使用 `python main.py`（内部调用 uvicorn）启动开发服务器。

- `api/items.py`
	- 提供物品相关的 REST 接口：
		- POST `/items/`：创建物品，接收 `ItemCreate`。
		- GET `/items/`：列出所有物品，返回 `List[Item]`。
		- GET `/items/{id}`：根据 id 获取单个物品。

- `api/users.py`
	- 提供用户相关接口：
		- POST `/users/`：创建用户（示例不保存密码哈希，仅演示数据结构）。
		- GET `/users/`：列出用户。
		- GET `/users/me`：返回当前认证用户（依赖 `utils.auth.get_current_user`）。

- `models/item.py`, `models/user.py`
	- 使用 Pydantic 定义请求与响应模型（`ItemCreate`, `Item`, `UserCreate`, `User`）。

- `services/*`
	- 业务逻辑层，当前实现为内存存储（自动分配 id、列表、查询等方法）。
	- 后续可在这里替换为数据库操作（SQLAlchemy、ORM 等）。

- `db/database.py`
	- 提供一个非常简单的 InMemoryDB 占位类，供以后扩展使用。

- `utils/auth.py`
	- 提供一个 FastAPI 依赖函数 `get_current_user`，示例中的 token 解析非常简单（以 email 作为 token）。
	- 示例 token 格式：直接使用邮箱（`Authorization: Bearer alice@example.com`）或 `user:alice@example.com`。

快速运行（PowerShell）:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

启动后访问：

- 自动生成的文档（Swagger UI）： http://127.0.0.1:8000/docs
- Redoc： http://127.0.0.1:8000/redoc

示例：

1) 创建用户：

POST /users/  body: {"email":"alice@example.com","full_name":"Alice","password":"secret"}

2) 使用 demo token 访问受保护接口：在请求头中添加

```
Authorization: Bearer alice@example.com
```

3) 创建 item：

POST /items/  body: {"name":"Book","description":"A good book"}

注意事项：

- 当前实现仅用于演示与本地开发，认证与存储不适合生产环境。
- 若需我帮助把存储替换为 SQLite/SQLAlchemy 或增加 JWT 认证，我可以继续实现。
