# LostLink

> 状态：只读物品列表已接入 FastAPI 与 MySQL；发布、登记、举报和匹配通知为前端本地演示
>
> 前端最后验证：2026-10-02；后端与 MySQL 联调记录：2026-09-30

LostLink 是面向校园失物招领场景的软件工程课程项目。首页通过 FastAPI 和 MySQL 查询失物、拾物记录；点击卡片进入独立详情页。发布失物、登记拾物、举报和匹配通知已有可操作的前端页面，但只保存或读取当前浏览器的演示数据，没有对应的后端写入、真实匹配或通知服务。

项目希望把失物、拾物信息的发布、检索、匹配和状态跟踪集中到一个协作流程中，减少信息分散和重复沟通。当前产品范围仍处于团队确认阶段，需求草案见 [docs/product/requirements.md](docs/product/requirements.md)。

## 当前状态

已实现：

- 基于 Vue 3、TypeScript 和 Vite 的可运行前端工程。
- 首页关键词搜索，以及类别、校区、时间和记录类型筛选。
- 东丽校区北区/南区二级筛选，以及宁河校区整体筛选。
- 记录卡片、空结果、独立详情页、举报提交页和响应式布局；举报记录只保存在浏览器。
- 发布失物、登记拾物共用前端表单，支持校验、草稿和本地图片预览；匹配通知支持筛选、已读、候选详情及确认/拒绝演示。
- FastAPI 应用入口、健康检查、统一错误响应和 OpenAPI 文档。
- 使用 SQLAlchemy 查询 MySQL 的 `GET /api/v1/items` 筛选与分页接口。
- MySQL 8.4 本地容器配置和首个 Alembic migration。
- 前端接口、本地表单及状态存储单元测试，以及后端代码检查、接口测试和可选 MySQL 集成测试。

尚未实现：

- 用户认证、服务端发布与编辑、真实匹配与通知、服务端图片上传和认领归还。
- 浏览器端自动化测试，以及发布、认证和完整业务流程的服务端测试。

## 快速开始

查看首页真实列表需要启动 FastAPI 和 MySQL；只演示发布、拾物登记与匹配通知时可以不启动后端。前端最后在 Node.js 24.14.1 和 npm 11.11.0 上通过检查。需要完整列表数据时，先按 [backend/README.md](backend/README.md) 启动数据库、执行迁移和演示数据脚本，再启动前端。

在仓库根目录使用 Windows PowerShell 执行：

```powershell
cd frontend
npm.cmd install
Copy-Item .env.example .env
npm.cmd run dev
```

启动成功后，以终端显示的地址为准，通常是 `http://127.0.0.1:5173/`。`/publish/lost`、`/publish/found`、`/notifications` 不依赖后端；首页在后端不可用时会显示连接错误和重试入口。停止服务时在终端按 `Ctrl+C`。

提交前检查：

```powershell
cd frontend
npm.cmd test
npm.cmd run type-check
npm.cmd run build
```

2026-10-02 验证结果：5 个测试文件中的 14 个测试通过，类型检查与构建通过；Vite 在 `frontend/dist/` 生成构建结果。`dist/` 只是本地产物，不提交到 Git。

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
│  └─ src/               # 前端源码、页面和同目录单元测试
├─ docs/                 # 项目级文档中心
│  ├─ product/           # 需求范围与用户流程
│  ├─ architecture/      # 系统、前端、后端、数据库与 ADR
│  ├─ api/               # 跨端接口契约
│  ├─ development/       # 环境、流程、测试与约定
│  ├─ design/            # 页面、交互与视觉说明
│  └─ operations/        # 部署、运行与安全
├─ scripts/              # 项目辅助脚本说明目录
├─ CONTRIBUTING.md       # 协作与提交规范
└─ README.md             # 项目入口说明
```

更完整的目录职责见 [系统架构总览](docs/architecture/overview.md)。

## 后续开发顺序

1. 团队确认身份、联系方式、图片和匹配反馈的正式需求与隐私规则。
2. 为当前本地演示流程设计服务端接口、权限、数据模型和迁移，并完成评审。
3. 将前端模拟服务逐项替换为真实接口，补充跨端测试与浏览器端自动化测试。
4. 完成认领归还闭环、联调、验收和部署准备。

## 文档入口

- [文档中心](docs/README.md)：按产品、架构、开发、设计和运维主题浏览全部文档。
- [前端开发说明](frontend/README.md)：前端安装、运行、检查命令和目录职责。
- [后端开发说明](backend/README.md)：后端当前状态、计划中的运行入口和目录职责。
- [贡献指南](CONTRIBUTING.md)：分支、提交、评审和协作要求。
- [变更记录](CHANGELOG.md)：对使用者和开发者有影响的变化。

## 开始协作

1. 从需求文档中选择一个已确认的需求，创建对应 Issue。
2. 在 Issue 中写明范围、验收条件、负责人和依赖。
3. 按 [CONTRIBUTING.md](CONTRIBUTING.md) 创建分支并提交 Pull Request。
4. 功能、测试和相关文档在同一个 Pull Request 中交付。

当前首页只读查询已完成前后端联调；前端演示记录不会写入 MySQL，也不会出现在首页真实列表中。下一阶段可实现用户认证和失物/拾物发布接口，并补充浏览器端自动化测试。
