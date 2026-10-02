# API 文档

本目录用于存放接口约定、字段说明、错误码和接口变更记录。当前后端由 FastAPI 生成 OpenAPI，运行后可访问 `/openapi.json` 和 `/docs`；仓库尚未配置持续集成导出或校验 OpenAPI，不要把它写成已有自动流程。

当前仅有只读业务接口 `GET /api/v1/items`，另有 `GET /health` 健康检查。接口的可执行定义以 FastAPI 生成的 `/openapi.json` 为准；本文件记录跨端使用约定和示例。前端发布、拾物登记、举报、匹配通知及反馈没有后端接口，它们只调用浏览器本地模拟服务。

## 已实现接口

### `GET /api/v1/items`

查询公开的失物和拾物记录。正式运行时数据由 SQLAlchemy Repository 从 MySQL 获取；自动测试可以替换为内存 Repository。

支持 `keyword`、`type`、`category`、`campus`、`area`、`status`、`days`、`page` 和 `page_size` 查询参数。未指定 `status` 时只返回 `active` 记录；结果按发生时间和标识符稳定倒序排列。

成功响应示例（虚构值，仅示意字段结构，不代表当前数据库记录）：

```json
{
  "items": [
    {
      "id": 3,
      "type": "found",
      "category": "数码",
      "title": "白色无线耳机",
      "description": "白色充电仓，外壳有轻微划痕，耳机已妥善保管。",
      "location": "操场南门",
      "campus": "宁河校区",
      "area": null,
      "occurred_at": "2026-09-29T08:00:00Z",
      "status": "active",
      "contact_hint": "请描述蓝牙名称或保护套特征。"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

参数校验失败时返回 `422` 和下文规定的统一错误结构。

## 契约工作流

1. 前后端在实现前确认路径、方法、权限、请求、响应、错误和示例。
2. 通过 FastAPI 路由和 Schema 提交接口草案，预览生成的 OpenAPI 并完成评审。
3. 后端按照已评审契约实现，前端可使用导出的契约生成类型或模拟数据。
4. 使用契约测试检查实现与定义是否一致。
5. 行为变化时在同一个 Pull Request 中更新契约、测试和相关说明。

本地启动命令见 [backend/README.md](../../backend/README.md)。服务启动后访问 `http://127.0.0.1:8000/openapi.json` 获取当前契约，或访问 `http://127.0.0.1:8000/docs` 预览；尚无仓库内固定的导出文件和自动契约测试。

## 基本约定

- API 路径包含版本前缀，例如 `/api/v1/items`。
- 路径使用小写复数名词和连字符，不把动作随意写进资源路径。
- 时间使用带时区的 ISO 8601 字符串，并明确服务端保存策略。
- 标识符在所有接口中保持同一种类型和命名。
- 列表接口统一分页，并返回稳定、确定的排序结果。
- 更新接口明确区分未提供字段与显式传入 `null`。
- 每个接口声明可能返回的状态码、错误结构和权限要求。

## 错误响应

后端已实现统一错误结构。以下是格式示意，`request_id` 为示例值：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数不正确",
  "details": [
    {
      "field": "query.page",
      "message": "Input should be greater than or equal to 1",
      "type": "greater_than_equal"
    }
  ],
  "request_id": "示例请求标识"
}
```

- `code` 是供程序稳定判断的机器可读标识。
- `message` 是可展示或便于理解的概括，不包含内部堆栈或敏感数据。
- `details` 用于字段校验等结构化信息。
- `request_id` 用于关联日志，不能包含个人信息。

当前参数校验错误返回 HTTP `422`、`code=VALIDATION_ERROR`，`details` 为字段、消息和类型的数组；数据库异常返回 HTTP `503`、`code=DATABASE_UNAVAILABLE`；未处理异常返回 HTTP `500`、`code=INTERNAL_SERVER_ERROR`。这些状态由当前异常处理器定义，不表示尚未实现的发布或匹配接口已有对应错误契约。

## 兼容性

- 新增可选字段通常可以保持兼容，但客户端不能假设枚举永远只有当前值。
- 删除字段、改变含义、收紧校验或修改字段类型属于破坏性变化。
- 破坏性变化必须给出迁移窗口，并评估是否需要新 API 版本。
- 数据库字段不直接等于公开 API 字段；对外契约由 Schema 明确定义。

## 接口评审清单

- [ ] 对应需求和验收条件已经确认
- [ ] 正常、无权限、参数错误、资源不存在和冲突场景均已定义
- [ ] 请求与响应包含清晰示例
- [ ] 个人信息和敏感字段的可见范围已经确认
- [ ] 分页、排序、幂等性和重复提交行为已经明确
- [ ] 前后端均能依据契约独立实现和测试
