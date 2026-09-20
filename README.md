# LostLink

LostLink 是面向校园失物招领场景的软件工程课程项目。

## 当前状态

仓库已建立项目目录、协作模板和开发约定。前端目录已包含一个可独立运行的 Vue 3 首页原型，用于演示失物招领记录的搜索、筛选与详情查看。后端与真实业务接口尚未实现。

后续计划采用以下技术边界：

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
