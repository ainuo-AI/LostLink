# Backend

> 状态：账号认证、物品与图片、举报、匹配通知、管理审计和校准接口均已实现；全部 migration 已在本地 MySQL 完成升级验证。
>
> 最后验证：2026-10-06；33 个默认测试和 3 个 MySQL 集成测试通过。

后端采用 Python 3.12、FastAPI、SQLAlchemy 和 MySQL，并按照“接口层 → 服务层 → 数据访问层 → 数据模型层”组织。`GET /api/v1/items` 通过 Repository 查询 MySQL；内存 Repository 只用于不依赖数据库的快速测试。

完整的分层职责和依赖规则见 [后端架构](../docs/architecture/backend.md)，数据库演进要求见 [数据库与迁移](../docs/architecture/database.md)。

## 环境要求

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop，或兼容 MySQL 8.4 配置的本地 MySQL

依赖版本记录在 `pyproject.toml` 和 `uv.lock`。虚拟环境、缓存和 `.env` 不提交到 Git。

## 安装与启动

先在 `backend/` 目录安装依赖并复制本地配置。

```powershell
# Windows PowerShell
uv sync
Copy-Item .env.example .env
```

```bash
# macOS 或 Linux
uv sync
cp .env.example .env
```

然后在两种系统上执行相同命令：

```bash
docker compose up -d mysql
uv run alembic upgrade head
uv run python -m scripts.seed_items
uv run uvicorn app.main:app --reload
```

启动后的默认地址：

- 健康检查：`http://127.0.0.1:8000/health`
- OpenAPI UI：`http://127.0.0.1:8000/docs`
- 物品列表：`http://127.0.0.1:8000/api/v1/items`

`compose.yaml` 为 macOS 和 Windows 提供相同的 MySQL 8.4、UTF-8 和 UTC 配置。`.env.example` 中的账号仅供本地开发；生产环境必须替换为独立强密码。

如果系统已有 MySQL，可以不使用 Docker，但需要自行创建数据库和最小权限账号，并在 `.env` 中设置 `DATABASE_URL`。

## 数据库迁移

在 `backend/` 目录执行：

```powershell
# 升级到最新结构
uv run alembic upgrade head

# 查看当前版本
uv run alembic current

# 查看迁移历史
uv run alembic history

# 回滚一个版本；执行前必须确认不会丢失有效数据
uv run alembic downgrade -1
```

已经合并或在共享环境执行过的 migration 不得修改；结构变化必须创建新的 migration。

## 检查命令

```bash
uv run ruff check .
uv run pytest
```

默认测试使用内存 Repository，不会连接个人数据库。数据库集成测试需要显式提供隔离的测试库：

```powershell
$env:TEST_DATABASE_URL = $env:DATABASE_URL
uv run pytest -m mysql
```

代码检查和测试均应以退出码 `0` 结束。2026-10-06 的最近一次验证中，Ruff
检查通过，33 个默认测试及 3 个显式启用的 MySQL 集成测试通过。

## 当前接口

### `GET /health`

返回服务名称、版本和运行环境，用于确认 FastAPI 已成功启动。

### `GET /api/v1/items`

返回稳定排序的分页记录，支持以下查询参数：

| 参数 | 作用 |
| --- | --- |
| `keyword` | 搜索标题、描述、类别和地点 |
| `type` | `lost` 或 `found` |
| `category` | 精确匹配物品类别 |
| `campus` | 东丽校区或宁河校区 |
| `area` | 北区或南区 |
| `status` | 记录状态；未提供时只返回 `active` |
| `days` | 查询最近 1～365 天 |
| `page` | 页码，从 1 开始 |
| `page_size` | 每页数量，范围 1～100 |

示例：

```text
GET /api/v1/items?keyword=耳机&type=found&campus=宁河校区&page=1&page_size=20
```

### 物品发布与管理

| 方法与路径 | 认证 | 作用 |
| --- | --- | --- |
| `GET /api/v1/items/{id}` | 否 | 读取单条记录的公开详情，不返回完整联系方式和发布者编号 |
| `POST /api/v1/items` | Bearer | 发布失物或拾物，所有者固定为当前用户 |
| `GET /api/v1/users/me/items` | Bearer | 按类型、状态和分页查询自己的记录 |
| `PATCH /api/v1/items/{id}` | Bearer | 发布者或管理员编辑仍在进行中的记录 |
| `PATCH /api/v1/items/{id}/status` | Bearer | 标记为已找回、已归还或已关闭，并写入状态审计 |

完整联系方式只在发布响应和“我的记录”等所有者视图中返回，公开列表与公开详情仅返回 `contact_hint`。失物只能进入 `recovered` 或 `closed`，拾物只能进入 `returned` 或 `closed`；第一阶段的终态不可重复修改。

图片通过 `POST /api/v1/uploads/images` 上传，支持 JPG、PNG 和 WebP，默认单张最多 5MB。发布或编辑请求最多传入三个属于当前用户的 `image_ids`；关联成功后公开物品响应通过 `image_urls` 返回读取地址。

### 举报、匹配与管理

| 模块 | 主要接口 |
| --- | --- |
| 举报 | `POST /api/v1/items/{id}/reports`、`GET /api/v1/users/me/reports`、`GET/PATCH /api/v1/admin/reports` |
| 匹配 | `GET /api/v1/notifications`、`GET /api/v1/matches/{id}`、已读和反馈接口 |
| 管理 | `/api/v1/admin/overview`、`/api/v1/admin/users`、`/api/v1/admin/audit` |
| 校准 | `/api/v1/admin/calibration/tasks`、`/api/v1/admin/calibration/versions` |

新物品发布后会与同校区、相反类型的进行中记录进行规则评分，并向双方所有者创建去重通知。匹配分数是候选排序信号，不表示找回概率。管理员处理举报、用户状态和校准版本时必须提供理由，服务端写入不可变审计日志。

### 用户认证

| 方法与路径 | 作用 |
| --- | --- |
| `POST /api/v1/auth/register` | 使用校园账号和至少 8 位密码注册普通用户 |
| `POST /api/v1/auth/login` | 登录并返回有有效期的 Bearer 会话令牌 |
| `POST /api/v1/auth/logout` | 吊销当前 Bearer 会话 |
| `GET /api/v1/users/me` | 返回当前用户、角色、状态和校园验证状态 |

除注册和登录外，受保护接口使用 `Authorization: Bearer <access_token>`。密码使用带随机盐的 scrypt 摘要保存；会话令牌只在登录响应中返回明文，数据库只保存 SHA-256 摘要。连续登录失败次数、临时锁定时间和会话有效期可以通过 `.env` 中的 `AUTH_*` 配置调整。

当前注册仅创建本地账号，`campus_verified` 默认为 `false`；校园统一身份供应商尚未确定，系统不会把本地注册误写为已完成校园认证。

## 目录职责

- `app/api/v1/`：版本化接口路由
- `app/core/`：配置、安全和通用基础设施
- `app/models/`：数据库模型
- `app/schemas/`：请求与响应数据结构
- `app/repositories/`：数据访问
- `app/services/`：业务编排
- `alembic/`：数据库迁移
- `tests/`：后端测试

当前匹配与校准规则位于 Service 和 Repository 分层中；`app/integrations/` 与 `app/tasks/` 仍为将来接入外部服务和异步任务预留。

## 后续范围

- 校园统一身份验证、密码重置、物品删除和完整认领核验
- 对象存储、异步匹配、站外通知和其他外部集成
