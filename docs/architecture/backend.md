# 后端架构

> 状态：FastAPI、SQLAlchemy、MySQL、Alembic 和只读物品列表接口已实现；认证及写入业务仍为计划。
>
> 最后核对：2026-09-30；本次文档同步未修改或重测后端代码。

本文记录后端分层和依赖方向。安装、启动、迁移和检查命令维护在 [backend/README.md](../../backend/README.md)。

## 计划结构

```text
HTTP API
   ↓
API / Schema
   ↓
Service
   ├─ Repository → Model → MySQL
   ├─ Matching
   ├─ Calibration
   └─ Integration
```

初期采用模块化单体，不拆分为多个网络服务。匹配、反馈校准和外部集成保持清晰模块边界，但随同一个 FastAPI 应用部署。

## 分层职责

- `api/v1/`：接收参数、进入权限校验、调用 Service 并组织 HTTP 响应。
- `schemas/`：定义请求、响应及其校验，不直接表达数据库内部结构。
- `services/`：编排业务流程、事务边界和跨模块规则。
- `repositories/`：封装数据库查询与持久化，不实现业务流程。
- `models/`：表达数据库持久化结构和关系。
- `matching/`：生成候选匹配、分数和可解释依据。
- `calibration/`：根据已确认反馈评估或调整匹配策略。
- `integrations/`：隔离 AI、地图、对象存储和通知供应商。
- `tasks/`：后台或异步任务入口，具体队列方案待真实需求确认。
- `core/`：配置、安全和通用基础设施。

## 依赖规则

- API 层调用 Service，不直接读写数据库。
- Service 可以依赖 Repository、Matching 和 Integration，不依赖前端页面。
- Repository 只负责持久化，不发送通知或编排用户流程。
- Matching 不直接修改用户数据或发送通知。
- 外部服务响应转换为项目内部类型后，才能进入业务模块。
- 数据库 Model 不直接作为公开 API 响应；对外字段由 Schema 明确定义。

## 安全与可靠性边界

- 每个受保护操作在服务端检查身份、角色和资源归属。
- 日志不记录密码、令牌、完整联系方式或不必要的个人信息。
- 外部请求必须设置超时、有限重试和降级路径。
- 文件上传执行类型、大小、文件头、存储隔离和访问权限检查。
- 数据结构通过 Alembic migration 演进，具体要求见 [数据库与迁移](database.md)。

## 尚未确定

认证机制、任务队列、对象存储、部署平台和监控方案仍未确认。这些选择应在相关需求出现时评审，必要时新增 ADR。
