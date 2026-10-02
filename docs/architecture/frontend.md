# 前端架构

> 状态：真实只读首页、Vue Router 页面导航、跨页面物品缓存及独立本地演示服务已实现；Layout 目录仍未承担业务。
>
> 最后核对：2026-10-02

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
    ├─ ItemDetailView.vue → stores/itemNavigation.ts → 现有列表接口
    ├─ ReportSubmitView.vue → stores/reports.ts → localStorage
    ├─ PublishLostView.vue / RegisterFoundView.vue
    │    └─ ItemEntryForm.vue → services/localItems.ts / imageStore.ts
    └─ NotificationsView.vue / MatchDetailView.vue
         └─ services/matches.ts → localStorage
```

`HomeView.vue` 持有筛选、分页、加载和错误状态，通过 `api/items.ts` 请求后端并将 API 数据转换为页面模型。过期请求会通过 `AbortController` 取消。卡片进入独立详情路由；详情刷新时，`itemNavigation.ts` 可从现有列表接口查找该物品。发布与拾物登记复用 `ItemEntryForm.vue` 和 `ImagePicker.vue`，但草稿按记录类型隔离。通知列表与详情通过独立模拟服务共享状态，页面本身不直接操作存储键。

## 模块职责

- `views/`：页面级组合和页面状态，不直接散布底层请求细节。
- `components/`：可复用界面单元，通过明确的 Props 和 Emits 协作。
- `api/`：统一封装 HTTP 调用、响应转换和通用错误处理。
- `services/`：前端演示表单校验、记录、图片和通知的本地实现；不能当作后端 API。
- `stores/`：跨页面物品缓存及本地举报演示状态。
- `router/`：首页、物品详情、举报、发布和匹配通知的 URL 导航。
- `layouts/`：预留目录，当前无业务实现。
- `types/`：前端共享类型；API 类型以后优先从 OpenAPI 生成。
- `styles/`：全局设计变量和跨组件基础样式。

## 数据流原则

1. 真实后端数据只通过 `api/` 获取；首页查询不与本地演示记录合并。
2. `api/` 把服务端响应转换为前端展示类型；本地演示数据使用独立 `demo-` 标识和类型。
3. 演示服务以 Promise 接口提供存取，UI 负责加载、校验、错误和成功状态；图片二进制存于 IndexedDB，不放入 `localStorage`。
4. 页面状态尽量保持局部，跨页面数据由专门模块管理，组件不直接依赖数据库或外部供应商字段。
5. 后续接入正式接口时，由后端校验权限和输入；当前前端校验只保证本地演示体验，不是安全边界。

## 与后端的边界

- 前端只通过公开 HTTP API 访问业务能力，不连接数据库或携带服务端密钥。
- 请求、响应、错误和兼容性以 [API 契约](../api/README.md) 为准。
- 权限必须由后端执行；前端隐藏按钮不能作为安全控制。
- 接口继续扩展时，优先从 OpenAPI 生成或校验接口类型，避免手工维护两套字段定义。

## 引入新基础设施的条件

Vue Router 已用于可刷新和前进后退的页面流程；项目未引入大型组件库或额外状态管理库。若引入新基础设施，应说明实际需求、测试与迁移影响，不能把预留目录写成已经实现。
