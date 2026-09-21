# LostLink

> 状态：前端首页原型已验证，后端尚未初始化
>
> 最后验证：2026-09-21

LostLink 是面向校园失物招领场景的软件工程课程项目。当前前端原型用于验证失物和拾物记录的搜索、筛选与详情查看交互；它不包含真实用户、后端接口或持久化数据。

## 当前状态

已实现：

- 基于 Vue 3、TypeScript 和 Vite 的可运行前端工程。
- 首页关键词搜索，以及类别、校区、时间和记录类型筛选。
- 东丽校区北区/南区二级筛选，以及宁河校区整体筛选。
- 记录卡片、空结果、详情弹窗和响应式布局。

尚未实现：

- FastAPI 后端、MySQL 数据库和 Alembic 迁移。
- 用户认证、失物/拾物发布、真实查询、匹配通知和文件上传。
- 前端单元测试、后端测试和端到端测试。

## 快速开始

当前只能独立运行前端。Vite 6.4.3 要求 Node.js 18、20 或 22 及以上版本；本项目最后在 Node.js 24.14.1 和 npm 11.11.0 上验证。

在仓库根目录使用 Windows PowerShell 执行：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

启动成功后，终端会显示 `http://127.0.0.1:5173/`。打开该地址即可查看首页原型。停止服务时在终端按 `Ctrl+C`。

提交前检查：

```powershell
cd frontend
npm.cmd run type-check
npm.cmd run build
```

已验证的预期结果是类型检查退出码为 0，且 Vite 在 `frontend/dist/` 生成构建结果。`dist/` 只是本地产物，不提交到 Git。

如果 PowerShell 提示禁止运行 `npm.ps1`，请使用上述 `npm.cmd` 命令，无需修改系统执行策略。

## 目录说明

```text
LostLink/
├─ .github/              # GitHub Issue 与 Pull Request 模板
├─ backend/              # 后端工程骨架
│  ├─ alembic/           # 数据库迁移目录
│  ├─ app/               # 后端应用分层目录
│  └─ tests/             # 后端测试目录
├─ frontend/             # 前端工程骨架
│  ├─ public/            # 公共静态资源
│  ├─ src/               # 前端源码分层目录
│  └─ tests/             # 前端测试目录
├─ docs/                 # 架构、接口与设计文档
├─ scripts/              # 项目辅助脚本预留目录
├─ CONTRIBUTING.md       # 协作与提交规范
└─ README.md             # 项目入口说明
```

更完整的目录职责见 [docs/architecture.md](docs/architecture.md)。

## 后续开发顺序

1. 团队确认需求范围和数据模型。
2. 建立前后端最小可运行环境。
3. 设计并评审接口契约。
4. 按模块逐步实现功能和测试。
5. 完成联调、验收和部署说明。

## 协作入口

- 开始开发前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
- 架构边界见 [docs/architecture.md](docs/architecture.md)。
- 开发流程见 [docs/development.md](docs/development.md)。
- 命名和提交约定见 [docs/conventions.md](docs/conventions.md)。
- 首页设计与实现状态见 [docs/design/README.md](docs/design/README.md)。
- 前端运行和目录说明见 [frontend/README.md](frontend/README.md)。
- 接口文档状态见 [docs/api/README.md](docs/api/README.md)。
- 未发布变更见 [CHANGELOG.md](CHANGELOG.md)。
