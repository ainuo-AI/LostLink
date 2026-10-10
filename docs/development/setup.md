# 本地开发环境

> 状态：Vue、FastAPI 和 MySQL 的普通用户、匹配、举报与管理链路已有本地联调记录。
>
> 文档核对：2026-10-10；前端、后端与 MySQL 联调历史记录：2026-10-06

本文提供从获取仓库到验证当前可运行部分的完整入口。前端和后端的专项命令分别维护在 [frontend/README.md](../../frontend/README.md) 和 [backend/README.md](../../backend/README.md)。

## 当前可以运行什么

- 可以运行 Vue 首页，并通过 FastAPI 查询 MySQL 中的物品记录。
- 注册、登录、发布失物、登记拾物和个人记录管理需要同时启动前端、后端与 MySQL；这些操作会写入真实本地数据库。
- 图片、`/notifications`、举报和 `/admin/*` 都使用真实后端接口，需要同时启动 FastAPI 与 MySQL。
- MySQL Compose 配置、四份 Alembic migration 和演示数据脚本已完成；最新 migration 已完成本地 MySQL 升级验证，破坏性回滚仍只允许在一次性数据库执行。浏览器端自动化测试尚未配置。

## 1. 获取项目

```powershell
git clone https://github.com/ainuo-AI/LostLink.git
cd LostLink
```

默认开发分支为 `main`。当前仓库不使用 Git submodule 或 Git LFS。

## 2. 准备前端环境

当前前端使用 Vue 3、TypeScript 和 Vite。项目最后在 Node.js 24.14.1 和 npm 11.11.0 上验证；Vite 6.4.3 支持符合其 `engines` 声明的 Node.js 版本。

先确认本机工具：

```powershell
node --version
npm.cmd --version
```

Windows PowerShell 建议使用 `npm.cmd`，避免本机执行策略阻止 `npm.ps1`。

## 3. 安装并启动后端

后端使用 Python 3.12 和 uv。在仓库根目录另开终端执行：

```powershell
cd backend
uv sync
Copy-Item .env.example .env
docker compose up -d mysql
uv run alembic upgrade head
uv run python -m scripts.seed_items
uv run uvicorn app.main:app --reload
```

访问 `http://127.0.0.1:8000/health` 应获得状态响应，访问 `http://127.0.0.1:8000/docs` 可以查看 OpenAPI 页面。详细接口和检查命令见 [后端开发说明](../../backend/README.md)。

## 4. 安装并启动前端

在仓库根目录再开一个终端，避免从 `backend/` 目录执行错误的相对路径：

```powershell
cd frontend
npm.cmd ci
Copy-Item .env.example .env
npm.cmd run dev
```

`.env.example` 默认把 API 地址设置为 `http://127.0.0.1:8000`。Vite 默认显示类似 `http://127.0.0.1:5173/` 的本地地址，以终端输出为准。后端及数据库已启动且演示数据已导入时，首页、认证、发布、举报、匹配和管理流程均可使用。后端未启动时，真实接口页面会显示连接错误。

停止服务时在运行终端按 `Ctrl+C`。

## 5. 检查前端

在 `frontend/` 目录执行：

```powershell
npm.cmd test
npm.cmd run type-check
npm.cmd run build
```

预期结果：

- 2026-10-10 已验证 7 个测试文件中的 22 个测试通过，涵盖认证、物品、举报与匹配拒绝 API 适配和表单校验。
- 类型检查退出码为 0。
- Vite 在 `frontend/dist/` 生成生产构建结果。
- `dist/` 是本地产物，不提交到 Git。

当前尚无可重复执行的浏览器端自动化测试。正式接口运行需要 MySQL；默认后端测试使用内存 Repository，不会连接个人数据库，数据库集成测试必须使用已迁移的隔离 MySQL。图片、举报、匹配与管理流程已经完成服务化。

## 常见问题

### PowerShell 禁止运行脚本

使用 `npm.cmd` 代替 `npm`，无需为项目修改系统执行策略。

### 5173 端口被占用

Vite 可能选择其他端口或报告冲突。以终端实际显示的地址为准；需要固定端口时先停止旧的开发服务。

### 依赖安装失败

先记录 `node --version` 和 `npm.cmd --version`，再检查网络、npm registry 和锁文件是否被意外修改。不要直接删除锁文件来掩盖依赖问题。

## 文档维护要求

- 修改运行时版本、依赖管理、环境变量或启动命令时，同步更新本文和对应子项目 README。
- 根文档只保留完整搭建顺序；专项参数和命令优先维护在离代码最近的 README 中。
- 命令必须在干净环境中验证，不再适用的步骤直接删除。
- 只适用于特定操作系统的步骤应明确标注，并提供其他平台可采用的等价命令。
