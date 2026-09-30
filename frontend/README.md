# Frontend

> 状态：首页与 FastAPI 只读物品接口的真实交互已验证
>
> 最后验证：2026-09-30

前端使用 Vue 3、TypeScript 和 Vite。首页通过 `GET /api/v1/items` 读取后端数据，支持关键词搜索、条件筛选、记录类型切换、分页和详情弹窗，并为加载失败提供重试入口。

前端模块边界和数据流见 [前端架构](../docs/architecture/frontend.md)，页面状态和视觉规则见 [设计资料](../docs/design/README.md)。本文只维护前端安装、运行、检查命令和源码目录职责。

## 环境要求

- Node.js 18、20 或 22 及以上版本（由当前 Vite 6.4.3 声明）。
- npm。
- 已按 [后端开发说明](../backend/README.md) 启动 FastAPI 和 MySQL。
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

- `test` 使用 Vitest 检查请求参数、错误响应和数据转换逻辑。
- `type-check` 使用 `vue-tsc` 检查 TypeScript 和 Vue 组件类型。
- `build` 先执行类型检查，再生成 `dist/` 生产构建结果。
- 2026-09-30 已验证 4 个前端测试、类型检查和生产构建全部通过。当前尚未配置浏览器端自动化测试。

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
- `src/router/`：路由配置
- `src/stores/`：全局状态
- `src/styles/`：全局样式与设计变量
- `src/types/`：共享类型
- `src/views/`：页面级视图
- `public/`：不参与构建处理的公共资源
- `src/api/*.test.ts`：前端接口层单元测试

`src/layouts/`、`src/router/` 和 `src/stores/` 目前仅为预留结构，不含业务实现。
