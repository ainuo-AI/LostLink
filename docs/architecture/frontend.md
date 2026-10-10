# 前端架构

> 状态：查询、认证、图片发布、举报、匹配和管理控制台均已接入真实接口；Vue Router 负责会话和管理员入口保护。
>
> 最后核对：2026-10-10

本文记录前端模块边界和依赖原则。安装、运行和检查命令见 [frontend/README.md](../../frontend/README.md)，页面和交互状态见 [设计资料](../design/README.md)。

## 当前结构

```text
index.html
    ↓
src/main.ts
    ↓
App.vue
src/router/index.ts
    ├─ HomeView.vue → api/items.ts → api/client.ts → GET /api/v1/items
    ├─ ItemDetailView.vue → stores/itemNavigation.ts → api/items.ts → GET /api/v1/items/{id}
    ├─ ReportSubmitView.vue → stores/reports.ts → 举报 API
    ├─ LoginView.vue / RegisterView.vue → stores/auth.ts → api/auth.ts
    ├─ PublishLostView.vue / RegisterFoundView.vue
    │    └─ ItemEntryForm.vue → api/items.ts + api/media.ts + 本地草稿
    ├─ MyView.vue → api/items.ts → 个人查询、编辑和状态更新
    ├─ NotificationsView.vue / MatchDetailView.vue → services/matches.ts → 匹配 API
    └─ AdminConsole.vue → api/admin.ts → 管理 API
```

`HomeView.vue` 持有筛选、分页、加载和错误状态，通过 `api/items.ts` 请求后端并将 API 数据转换为页面模型。认证 Store 只保存安全用户摘要和当前标签页会话，并在首次受保护导航时向服务端确认。发布与拾物登记复用 `ItemEntryForm.vue`，草稿按记录类型隔离，提交时上传图片。通知、举报和管理页面都通过统一客户端访问后端。

## 模块职责

- `views/`：页面级组合和页面状态，不直接散布底层请求细节。
- `components/`：可复用界面单元，通过明确的 Props 和 Emits 协作。
- `api/`：统一封装 HTTP 调用、响应转换和通用错误处理。
- `services/`：表单校验、草稿、图片暂存和匹配 API 数据转换。
- `stores/`：认证会话、单条物品详情加载及举报 API 适配。
- `router/`：URL 导航、受保护页面会话确认和管理员入口控制。
- `layouts/`：认证和管理控制台使用的页面布局。
- `types/`：前端共享类型；API 类型以后优先从 OpenAPI 生成。
- `styles/`：全局设计变量和跨组件基础样式。

## 数据流原则

1. 真实后端数据只通过 `api/` 获取；未提交草稿和页面状态不得伪装成服务端记录。
2. `api/` 把服务端响应转换为前端展示类型；认证请求由通用客户端统一附加 Bearer 会话。
3. 草稿以 Promise 接口存取；图片发布前暂存在 IndexedDB，提交时上传，不放入 `localStorage`。
4. 页面状态尽量保持局部，跨页面数据由专门模块管理，组件不直接依赖数据库或外部供应商字段。
5. 后端始终校验权限、资源归属、输入和状态转换；前端路由保护与按钮状态不是安全边界。

## 物品展示与匹配反馈

- `api/items.ts` 将服务端 `image_urls` 转换为图片绝对地址；`ItemCard.vue` 取第一张照片并裁剪填满缩略图区，`ItemDetailView.vue` 按比例展示照片。两者在没有照片或加载失败时回退到分类图标。
- `stores/itemNavigation.ts` 为详情和举报页加载单条公开记录，不再读取卡片缓存或扫描首页列表。联系方式取 `contact`，联系说明取 `contact_note`，不使用旧的 `contact_hint` 作为联系方式。
- 详情页仅提供举报操作，不再提供失物或拾物的认领入口。举报成功页显示服务端生成的编号。
- `services/matches.ts` 的 `rejectMatch` 固定提交 `status=rejected`；通知详情支持已读及拒绝，不提供确认匹配操作。历史 `confirmed` 仅用于读取和展示为“已处理”。
- 首页与个人记录卡片已展示实物缩略图；通知列表和举报摘要仍使用分类图标，匹配详情有图片时展示图片。

## 与后端的边界

- 前端只通过公开 HTTP API 访问业务能力，不连接数据库或携带服务端密钥。
- 请求、响应、错误和兼容性以 [API 契约](../api/README.md) 为准。
- 权限必须由后端执行；前端隐藏按钮不能作为安全控制。
- 接口继续扩展时，优先从 OpenAPI 生成或校验接口类型，避免手工维护两套字段定义。

## 引入新基础设施的条件

Vue Router 已用于可刷新和前进后退的页面流程；项目未引入大型组件库或额外状态管理库。若引入新基础设施，应说明实际需求、测试与迁移影响，不能把预留目录写成已经实现。
