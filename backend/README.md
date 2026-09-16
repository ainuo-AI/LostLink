# Backend

后端计划采用 FastAPI，并按照“接口层 → 服务层 → 数据访问层 → 数据模型层”组织。

当前目录只定义分层边界，不包含启动入口、接口、模型、依赖或业务实现。

## 目录职责

- `app/api/v1/`：版本化接口路由
- `app/core/`：配置、安全和通用基础设施
- `app/models/`：数据库模型
- `app/schemas/`：请求与响应数据结构
- `app/repositories/`：数据访问
- `app/services/`：业务编排
- `app/matching/`：匹配策略
- `app/calibration/`：反馈校准策略
- `app/integrations/`：外部 AI、地图和通知适配器
- `app/tasks/`：后台任务
- `alembic/`：数据库迁移
- `tests/`：后端测试
