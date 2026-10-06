# API 文档

本目录用于存放接口约定、字段说明、错误码和接口变更记录。当前后端由 FastAPI 生成 OpenAPI，运行后可访问 `/openapi.json` 和 `/docs`；仓库尚未配置持续集成导出或校验 OpenAPI，不要把它写成已有自动流程。

当前已有账号认证、物品与图片、举报、匹配通知、管理审计和校准版本接口。接口的可执行定义以 FastAPI 生成的 `/openapi.json` 为准；本文件记录跨端使用约定和示例，前端已接入这些真实接口。

2026-10-07 增加可选 [OpenAI 兼容图文匹配](multimodal-matching.md)，沿用现有通知接口，并在模型评估成功的候选中增加 `AI 图文` 解释维度；默认关闭，真实供应商联调待验证。

## 已实现接口

### 认证与当前用户

| 方法与路径 | 认证 | 说明 |
| --- | --- | --- |
| `POST /api/v1/auth/register` | 否 | 创建默认 `role=user`、`status=active`、`campus_verified=false` 的本地账号 |
| `POST /api/v1/auth/login` | 否 | 验证密码并签发不透明 Bearer 会话令牌 |
| `POST /api/v1/auth/logout` | Bearer | 吊销当前会话，不影响同一账号的其他会话 |
| `GET /api/v1/users/me` | Bearer | 读取当前账号、角色、状态和校园验证状态 |

注册账号允许 3～64 位字母、数字及 `._@-`，密码长度为 8～128。登录失败统一返回 `401`、`code=AUTHENTICATION_FAILED`，不会说明账号是否存在；默认连续 5 次失败后锁定登录 15 分钟。缺少、过期或已吊销的令牌返回 `401`、`code=UNAUTHENTICATED`，受限账号返回 `403`、`code=ACCOUNT_RESTRICTED`。

登录成功响应中的 `access_token` 只在该响应中明文出现，客户端后续通过 `Authorization: Bearer <access_token>` 发送。当前前端将会话保存在当前标签页的 `sessionStorage`，刷新时调用 `GET /api/v1/users/me` 重新确认；关闭标签页、主动退出或发现会话过期后清除。正式部署前仍需结合 XSS 风险和会话策略复审该方案。

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
      "contact_hint": "请描述蓝牙名称或保护套特征。",
      "image_urls": ["/api/v1/uploads/images/12"]
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

参数校验失败时返回 `422` 和下文规定的统一错误结构。

### 物品详情与管理

| 方法与路径 | 认证 | 说明 |
| --- | --- | --- |
| `GET /api/v1/items/{id}` | 否 | 返回任意状态记录的公开字段；不存在时返回 `ITEM_NOT_FOUND` |
| `POST /api/v1/items` | Bearer | 创建 `active` 记录，`owner_id` 只取当前会话用户 |
| `GET /api/v1/users/me/items` | Bearer | 查询自己的全部状态记录，支持 `type`、`status`、`page` 和 `page_size` |
| `PATCH /api/v1/items/{id}` | Bearer | 所有者或管理员编辑 active 记录；禁止修改类型、所有者和状态 |
| `PATCH /api/v1/items/{id}/status` | Bearer | 执行终态转换并原子写入状态审计 |

发布字段包括类型、类别、标题、描述、校区、区域、地点、带时区发生时间、联系方式和公开联系说明。拾物记录还必须提供 `storage_method=self|office`、保管地点和可联系时间。完整联系方式属于私密字段，只在发布者/管理员视图返回；公开响应仅含 `contact_hint`。

更新接口通过请求字段是否出现区分“不修改”和“显式设为 null”。图片先通过 `POST /api/v1/uploads/images` 上传，再把最多三个 `image_ids` 传给发布或更新接口；公开响应的 `image_urls` 可直接用于展示。

状态规则：

- `lost: active → recovered | closed`
- `found: active → returned | closed`
- 当前终态不可恢复或重复提交，非法转换返回 `409`、`code=INVALID_STATUS_TRANSITION`
- 非所有者修改返回 `403`、`code=FORBIDDEN`

### 图片、举报与匹配通知

| 方法与路径 | 认证 | 说明 |
| --- | --- | --- |
| `POST /api/v1/uploads/images` | Bearer | 上传 JPG、PNG 或 WebP；默认最大 5MB |
| `GET /api/v1/uploads/images/{id}` | 否 | 读取已经关联物品的图片 |
| `DELETE /api/v1/uploads/images/{id}` | Bearer | 删除自己的未关联临时图片 |
| `POST /api/v1/items/{id}/reports` | Bearer | 提交举报；禁止自举报和重复待处理举报 |
| `GET /api/v1/users/me/reports` | Bearer | 查看自己的举报及处理结果 |
| `GET /api/v1/notifications` | Bearer | 查看匹配通知、状态和未读数量 |
| `GET /api/v1/matches/{id}` | Bearer | 查看自己的候选详情和评分解释 |
| `PATCH /api/v1/notifications/{id}/read` | Bearer | 标记通知已读 |
| `PATCH /api/v1/matches/{id}/feedback` | Bearer | 确认或拒绝待处理候选 |

### 管理端

`/api/v1/admin/*` 全部要求 `role=admin`。主要接口包括概览统计、举报列表与处理、用户查询与状态修改、只读审计日志、校准任务创建以及候选版本的批准、拒绝、启用和回滚。管理写操作必须提供理由，并写入 `admin_audit_logs`。

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

当前参数校验错误返回 HTTP `422`、`code=VALIDATION_ERROR`，`details` 为字段、消息和类型的数组；业务校验使用对应稳定错误码；数据库异常返回 HTTP `503`、`code=DATABASE_UNAVAILABLE`；未处理异常返回 HTTP `500`、`code=INTERNAL_SERVER_ERROR`。

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
