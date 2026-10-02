# Backend

> 状态：FastAPI、MySQL、SQLAlchemy、Alembic 和只读物品列表接口已完成首轮验证。

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

代码检查和测试均应以退出码 `0` 结束。

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

## 目录职责

- `app/api/v1/`：版本化接口路由
- `app/core/`：配置、安全和通用基础设施
- `app/models/`：数据库模型
- `app/schemas/`：请求与响应数据结构
- `app/repositories/`：数据访问
- `app/services/`：业务编排
- `alembic/`：数据库迁移
- `tests/`：后端测试

`app/matching/`、`app/calibration/`、`app/integrations/` 和 `app/tasks/` 属于架构计划，当前仓库尚无这些实现目录。

## 尚未实现

- 用户认证、发布、修改和关闭记录
- 图片上传、候选匹配、通知和其他外部集成
