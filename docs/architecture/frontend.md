# 前端架构

> 状态：首页原型已实现；API、Router、Store 和 Layout 目录仍为预留结构。
>
> 最后核对：2026-09-26

本文记录前端模块边界和依赖原则。安装、运行和检查命令见 [frontend/README.md](../../frontend/README.md)，页面和交互状态见 [设计资料](../design/README.md)。

## 当前结构

```text
index.html
    ↓
src/main.ts
    ↓
App.vue
    ↓
HomeView.vue
    ├─ SiteHeader.vue
    ├─ ItemCard.vue
    └─ ItemDetailDialog.vue
```

`HomeView.vue` 当前持有虚构记录和筛选状态，通过 `computed` 计算可见结果。父组件使用 Props 向卡片和弹窗传递记录，子组件通过 Emit 通知父组件。共享记录类型位于 `src/types/item.ts`。

## 模块职责

- `views/`：页面级组合和页面状态，不直接散布底层请求细节。
- `components/`：可复用界面单元，通过明确的 Props 和 Emits 协作。
- `api/`：统一封装 HTTP 调用、响应转换和通用错误处理。
- `stores/`：只保存跨页面共享且需要持续存在的客户端状态。
- `router/`：页面导航、路由参数和访问边界。
- `layouts/`：跨页面共享的布局骨架。
- `types/`：前端共享类型；API 类型以后优先从 OpenAPI 生成。
- `styles/`：全局设计变量和跨组件基础样式。

## 数据流原则

1. View 或 Store 调用 `api/`，不直接在多个组件中编写 `fetch`。
2. `api/` 把服务端响应转换为前端可使用的稳定类型。
3. 页面状态尽量保持局部；只有多个页面确实共享时才进入 Store。
4. 组件不直接依赖数据库字段或第三方服务私有字段。
5. 加载、空结果、无权限、校验失败和服务错误都作为明确状态设计。

## 与后端的边界

- 前端只通过公开 HTTP API 访问业务能力，不连接数据库或携带服务端密钥。
- 请求、响应、错误和兼容性以 [API 契约](../api/README.md) 为准。
- 权限必须由后端执行；前端隐藏按钮不能作为安全控制。
- 后端初始化后，优先从 OpenAPI 生成或校验接口类型，避免手工维护两套字段定义。

## 引入新基础设施的条件

Router、Store、组件库或其他基础设施应在出现真实需求时引入，并同时补充测试和文档。预留目录不代表相关能力已经实现。
