# 架构边界

> 状态：前端原型已验证，后端架构仍为计划
>
> 最后验证：2026-09-21

## 当前实现

仓库目前只有可运行的前端首页原型。前端使用 Vue 3、TypeScript 和 Vite，数据来自 `HomeView.vue` 中的虚构数组，没有通过 HTTP 请求后端。

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

当前首页的数据流为：

1. `HomeView.vue` 持有演示记录和筛选状态。
2. Vue `computed` 根据关键词、类别、校区、区域、时间和记录类型计算可见结果。
3. 父组件通过 Props 向卡片和弹窗传递记录，子组件通过 Emit 通知父组件打开或关闭详情。
4. `src/types/item.ts` 统一记录、校区和区域的 TypeScript 类型。

`src/api/`、`src/router/`、`src/stores/` 和 `src/layouts/` 目前只是预留目录，不应视为已实现能力。

## 计划的总体结构

LostLink 计划采用以下前后端分离结构：

```text
Vue 3 前端
    ↓ HTTP API
FastAPI 接口层
    ↓
服务层
    ↓
数据访问层
    ↓
MySQL
```

匹配、反馈校准以及外部服务接入保持独立边界，避免直接散落在接口或页面中。

上述 FastAPI、MySQL、Alembic、匹配、校准和外部服务均尚未实现；具体认证方案、ORM、状态管理库、UI 组件库和部署平台也尚未确定。

## 后端分层约束

- 接口层负责参数接收、权限入口和响应组织。
- Schema 负责输入输出结构及校验。
- Service 负责编排业务流程。
- Repository 负责数据库读写。
- Model 只表达持久化结构和关系。
- Matching 只负责候选匹配与评分策略。
- Calibration 只负责基于反馈调整策略。
- Integration 负责隔离外部 AI、地图和通知服务。
- Task 负责异步或后台执行入口。

## 前端分层约束

- View 负责页面组合，不直接散布底层请求细节。
- Component 负责可复用界面单元。
- API 统一封装后端调用。
- Store 只保存跨页面共享状态。
- Router 维护页面导航和访问边界。
- Type 维护共享数据结构。

当前原型已按 View、Component、Style 和 Type 进行分层。API、Store、Router 和 Layout 层要在出现实际需求时再引入，不提前声称已完成。

## 当前边界

- 用户认证与权限实现
- 失物或拾物发布功能
- 后端搜索、候选匹配和推荐算法（当前只有浏览器内的演示数据筛选）
- AI 特征提取
- 数据库模型与迁移脚本
- 通知、地图和文件上传
- 可运行的后端工程配置
- 自动化单元测试和端到端测试
