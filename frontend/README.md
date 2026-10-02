# Frontend

> 状态：首页真实查询链路与详情/举报流程保留；发布失物、登记拾物和匹配通知为本地演示
>
> 最后验证：2026-10-02

前端使用 Vue 3、TypeScript、Vue Router 和 Vite。首页通过 `GET /api/v1/items` 读取后端数据，支持关键词搜索、条件筛选、记录类型切换和分页；点击物品卡片进入独立详情页，详情页下方的“举报”按钮可进入举报提交页。举报提交目前也是本地演示，不会修改后端或 MySQL。

独立页面路径：`/publish/lost`（发布失物）、`/publish/found`（登记拾物）、`/notifications`（匹配通知）、`/notifications/:id`（匹配详情）。这些流程在后端未启动时也能演示，但首页真实物品列表仍需后端；后端未启动时首页会保留连接错误与重试提示。模拟服务位于 `src/services/`，没有假设发布、匹配或反馈接口已经存在。

发布与登记表单的草稿、演示记录和通知处理状态分别保存在浏览器 `localStorage`；所选图片保存在 IndexedDB，浏览器清理站点数据后无法恢复。示例通知首次初始化一次，之后已读与确认/拒绝操作会保留。演示编号以 `demo-` 开头，和真实物品编号区分。通知得分及维度解释是预设模拟数据，不是 AI 计算结果，也不代表找回概率。确认匹配仅表示接受候选，后续认领与归还仍须线下核验。

图片规则为前端暂定：JPG、PNG、WebP，每张不超过 5MB，最多 3 张。图片只在当前浏览器保存，不会上传服务器。若浏览器禁用或耗尽本地存储，表单会显示错误而不提示发布成功。

前端模块边界和数据流见 [前端架构](../docs/architecture/frontend.md)，页面状态和视觉规则见 [设计资料](../docs/design/README.md)。本文只维护前端安装、运行、检查命令和源码目录职责。

## 环境要求

- Node.js 18、20 或 22 及以上版本（由当前 Vite 6.4.3 声明）。
- npm。
- 若需查看首页真实列表，已按 [后端开发说明](../backend/README.md) 启动 FastAPI 和 MySQL；本地演示页面不要求启动后端。
- 当前验证环境：Node.js 24.14.1、npm 11.11.0。

## 本地运行

以下命令均在 `frontend/` 目录执行。Windows PowerShell 建议使用 `npm.cmd`：

```powershell
npm.cmd install
Copy-Item .env.example .env
npm.cmd run dev
```

`.env.example` 默认将请求发送到 `http://127.0.0.1:8000`。如果后端使用其他地址，请在 `.env` 中修改 `VITE_API_BASE_URL`。启动成功后，Vite 会输出 `http://127.0.0.1:5173/`。

在 CMD、Git Bash、macOS 或 Linux 中可使用：

```bash
npm install
cp .env.example .env
npm run dev
```

## 检查与构建

```powershell
npm.cmd test
npm.cmd run type-check
npm.cmd run build
```

- `test` 使用 Vitest 检查请求参数、错误响应、数据转换、表单校验、本地状态与举报存储逻辑。
- `type-check` 使用 `vue-tsc` 检查 TypeScript 和 Vue 组件类型。
- `build` 先执行类型检查，再生成 `dist/` 生产构建结果。
- 当前尚未配置浏览器端自动化测试。

## 常见问题

- PowerShell 报错“禁止运行脚本”：将 `npm` 改为 `npm.cmd`，不需要修改系统执行策略。
- `npm.cmd install` 失败：先运行 `node --version` 和 `npm.cmd --version` 确认环境，再检查网络是否可访问 npm 包注册表。
- 页面提示无法连接服务：确认后端已启动，并检查 `.env` 中的 `VITE_API_BASE_URL`；修改环境变量后需要重启 Vite。
- 5173 端口被占用：Vite 会报告启动失败；先停止占用该端口的旧开发服务后重试。

## 目录职责

- `src/api/`：真实后端请求、错误处理和接口数据转换
- `src/assets/`：需要参与构建的静态资源
- `src/components/`：通用组件
- `src/layouts/`：页面布局
- `src/router/`：首页、详情/举报和本地演示页面路由
- `src/services/`：前端演示记录、通知、图片存储与表单校验
- `src/stores/`：跨页面物品缓存和浏览器本地举报记录
- `src/styles/`：全局样式与设计变量
- `src/types/`：共享类型
- `src/views/`：页面级视图
- `public/`：不参与构建处理的公共资源
- `src/**/*.test.ts`：与接口、存储和校验模块同目录的单元测试

`src/layouts/` 目前仅为预留结构，不含业务实现。
