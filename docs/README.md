# LostLink 文档中心

本文档中心是项目级信息的统一入口。前端和后端目录中的 `README.md` 只说明各自的安装、运行、检查命令和源码目录；需求、跨端架构、API 契约、开发流程及运维规范统一在这里维护。

> 当前状态：认证、物品、图片、举报、匹配和管理页面已完成 Vue、FastAPI 与 MySQL 联调；部署环境尚未初始化。
>
> 最后核对：2026-10-06

## 从哪里开始

| 你想了解 | 建议阅读 |
| --- | --- |
| 项目做什么、第一阶段包含什么 | [需求与范围](product/requirements.md) |
| 用户目前如何使用完整本地联调流程 | [核心用户流程](product/user-flows.md) |
| 系统如何拆分、前后端怎样协作 | [系统架构总览](architecture/overview.md) |
| 如何在本地运行项目 | [本地开发环境](development/setup.md) |
| 如何参与开发和提交变更 | [开发流程](development/workflow.md) 与 [贡献指南](../CONTRIBUTING.md) |
| 页面和交互目前做到什么程度 | [设计资料](design/README.md) |
| 接口契约如何维护 | [API 文档](api/README.md) |
| 如何测试、部署或排查故障 | [测试策略](development/testing.md) 与 [运维文档](#运维) |

## 产品

- [需求与范围](product/requirements.md)：项目目标、角色、MVP 范围、验收标准和待确认事项。
- [核心用户流程](product/user-flows.md)：已联调的认证、物品、举报、匹配和管理流程，以及待实现的认领核验。

## 架构

- [系统架构总览](architecture/overview.md)：系统边界、主要数据流、依赖方向和技术状态。
- [前端架构](architecture/frontend.md)：前端模块职责、状态流转和与 API 的边界。
- [后端架构](architecture/backend.md)：后端分层、业务模块和依赖规则。
- [数据库与迁移](architecture/database.md)：数据结构演进、migration 和数据字典要求。
- [技术决策记录](architecture/adr/README.md)：需要长期保留背景和取舍的架构决策。

## 接口与设计

- [API 文档](api/README.md)：接口契约、错误结构、兼容性和评审清单。
- [设计资料](design/README.md)：页面清单、首页流程、视觉规范、页面状态和可访问性。

## 开发

- [本地开发环境](development/setup.md)：从克隆仓库到启动 MySQL、后端和前端，并验证当前功能。
- [开发流程](development/workflow.md)：从需求确认、接口评审到合并的工作流。
- [测试策略](development/testing.md)：各层测试范围、测试数据和合并门槛。
- [项目约定](development/conventions.md)：命名、文档、依赖和安全约定。
- [前端开发说明](../frontend/README.md)：前端专项命令和目录职责。
- [后端开发说明](../backend/README.md)：后端当前状态和目录职责。

## 运维

- [部署说明](operations/deployment.md)：环境、发布顺序、回滚原则和发布记录。
- [运行手册](operations/runbook.md)：故障响应流程与上线前需补充的运行信息。
- [安全说明](operations/security.md)：账号、个人信息、上传、日志和外部服务安全要求。

## 文档边界

为避免前后端分别维护互相冲突的说明，文档按以下规则归档：

| 内容 | 唯一维护位置 |
| --- | --- |
| 项目简介、当前状态、最短启动路径 | 根目录 `README.md` |
| 前端安装、命令和源码目录 | `frontend/README.md` |
| 后端安装、命令和源码目录 | `backend/README.md` |
| 用户需求和端到端流程 | `docs/product/` |
| 系统边界、模块职责和技术决策 | `docs/architecture/` |
| 请求、响应、错误码和兼容性 | 后端生成的 `/openapi.json` 为现有接口事实来源，`docs/api/` 说明跨端约定 |
| 团队开发、测试和通用约定 | `docs/development/` |
| 页面、交互和视觉状态 | `docs/design/` |
| 部署、故障处理和安全 | `docs/operations/` |

文档中可以链接其他位置，但不要复制整段内容。某项事实发生变化时，只更新它的唯一维护位置以及必要的入口链接。

## 维护要求

- 文档必须区分“已实现”“已验证”“计划中”和“待确认”，不能把目录骨架描述成可用能力。
- 运行命令、版本号和访问地址必须实际验证，并在相关文档中记录最后核对日期。
- 功能变化应在同一个 Pull Request 中更新代码、测试和相关文档。
- 接口变化更新 OpenAPI 和 API 说明；数据结构变化更新 migration 和数据库文档。
- 重大且难以撤销的技术选择新增 ADR，不直接改写已接受 ADR 的历史结论。
