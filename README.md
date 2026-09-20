# LostLink

LostLink 是面向校园失物招领场景的软件工程课程项目。

项目希望把失物、拾物信息的发布、检索、匹配和状态跟踪集中到一个协作流程中，减少信息分散和重复沟通。当前产品范围仍处于团队确认阶段，需求草案见 [docs/requirements.md](docs/requirements.md)。

## 当前状态

仓库已建立项目目录、协作模板和开发约定。前端目录已包含一个可独立运行的 Vue 3 首页原型，用于演示失物招领记录的搜索、筛选与详情查看。后端与真实业务接口尚未实现。

后续计划采用以下技术边界（尚未形成可运行工程）：

- 前端：Vue 3
- 后端：FastAPI
- 数据库：MySQL
- 数据库迁移：Alembic
- 测试：前后端分别维护独立测试目录

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

## 建议的开发顺序

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

项目尚不可运行，因此当前没有安装或启动命令。前后端工程初始化后，应分别在 `frontend/README.md` 和 `backend/README.md` 中补充经过验证的命令。
