# LostLink

> 状态：前端首页原型已验证，后端尚未初始化
>
> 最后验证：2026-09-21

LostLink 是面向校园失物招领场景的软件工程课程项目。当前前端原型用于验证失物和拾物记录的搜索、筛选与详情查看交互；它不包含真实用户、后端接口或持久化数据。

项目希望把失物、拾物信息的发布、检索、匹配和状态跟踪集中到一个协作流程中，减少信息分散和重复沟通。当前产品范围仍处于团队确认阶段，需求草案见 [docs/requirements.md](docs/requirements.md)。

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

1. 团队评审并确认需求范围、验收标准和数据模型。
2. 建立前后端最小可运行环境。
3. 设计并评审接口契约。
4. 按模块逐步实现功能和测试。
5. 完成联调、验收和部署说明。

## 文档入口

| 文档 | 用途 |
| --- | --- |
| [需求与范围](docs/requirements.md) | 明确做什么、不做什么以及如何验收 |
| [本地环境搭建](docs/dev-setup.md) | 说明如何准备依赖并在开发电脑上运行项目 |
| [架构边界](docs/architecture.md) | 说明系统拆分、数据流和模块职责 |
| [首页设计说明](docs/design/README.md) | 说明首页交互、页面状态、响应式规则和已知缺口 |
| [前端说明](frontend/README.md) | 说明前端运行、检查命令和目录职责 |
| [开发流程](docs/development.md) | 从 Issue 到合并的完整工作流 |
| [项目约定](docs/conventions.md) | 统一命名、依赖、文档和安全约定 |
| [API 文档](docs/api/README.md) | 维护接口契约和变更规则 |
| [数据库与迁移](docs/database.md) | 维护数据结构和 migration 流程 |
| [测试策略](docs/testing.md) | 说明测试范围、分层和完成标准 |
| [部署说明](docs/deploy.md) | 说明环境、发布、验证和回滚流程 |
| [运行手册](docs/runbook.md) | 说明上线后的监控和故障处理 |
| [安全说明](docs/security.md) | 说明数据、密钥、权限和漏洞处理要求 |
| [技术决策记录](docs/adr/README.md) | 记录重要技术选择的背景和影响 |
| [贡献指南](CONTRIBUTING.md) | 说明分支、提交、评审和协作要求 |
| [变更记录](CHANGELOG.md) | 记录对使用者和开发者有影响的变化 |

## 开始协作

1. 从需求文档中选择一个已确认的需求，创建对应 Issue。
2. 在 Issue 中写明范围、验收条件、负责人和依赖。
3. 按 [CONTRIBUTING.md](CONTRIBUTING.md) 创建分支并提交 Pull Request。
4. 功能、测试和相关文档在同一个 Pull Request 中交付。

当前前端首页原型可按“快速开始”中的命令独立运行；后端尚未初始化，暂时没有后端安装或启动命令。
