# Frontend

> 状态：公开查询、认证、图片发布、举报、匹配通知和管理控制台均已接入 FastAPI
>
> 最后验证：2026-10-06

前端使用 Vue 3、TypeScript、Vue Router 和 Vite。`VITE_API_BASE_URL` 指向 FastAPI
服务，所有 HTTP 请求统一经过 `src/api/client.ts`，页面组件不直接拼接服务地址或
Bearer 请求头。

## 已接入的真实流程

- 首页通过 `GET /api/v1/items` 查询、筛选和分页展示公开记录。
- `/register` 创建本地校园账号，`/login` 建立 Bearer 会话。
- 会话令牌仅保存在当前标签页的 `sessionStorage`，刷新时通过
  `GET /api/v1/users/me` 向服务端重新确认；关闭标签页或退出登录后清除。
- `/publish/lost` 和 `/publish/found` 通过 `POST /api/v1/items` 发布记录；未登录用户
  会先进入登录页，登录后返回原目标。
- `/my` 读取当前用户摘要和个人记录，支持筛选、分页、编辑、标记找回/归还、关闭
  记录和退出登录。记录归属与状态转换最终由后端校验。

图片在填写草稿期间暂存在 IndexedDB，发布时依次上传并把服务端图片编号关联到物品。
举报、匹配通知及反馈均使用真实接口；`/admin/*` 仅允许服务端确认的管理员访问，
可执行举报处理、用户限制/恢复、审计查询和校准版本操作。

## 环境要求

- Node.js 18、20、22 或更高版本
- npm
- 真实业务流程需要先按 [后端开发说明](../backend/README.md) 启动 FastAPI 和 MySQL

## 本地运行

在 `frontend/` 目录执行：

```bash
npm ci
cp -n .env.example .env
npm run dev
```

Windows PowerShell 使用：

```powershell
npm.cmd ci
Copy-Item .env.example .env -ErrorAction SilentlyContinue
npm.cmd run dev
```

默认配置把请求发送到 `http://127.0.0.1:8000`，前端通常运行在
`http://127.0.0.1:5173/`。修改 `.env` 中的 `VITE_API_BASE_URL` 后需要重启 Vite。

## 检查与构建

```bash
npm run type-check
npm test
npm run build
npm audit --omit=dev
```

- `type-check` 检查 TypeScript 和 Vue 组件类型。
- `test` 检查认证、物品、举报与匹配接口适配、数据转换、表单校验和草稿存储。
- `build` 生成 `dist/` 生产构建结果。
- 2026-10-06 验证结果：6 个测试文件、17 个测试通过，生产构建通过，依赖审计为
  0 个已知漏洞。

## 目录职责

- `src/api/`：真实后端请求、统一错误和接口数据转换
- `src/components/`：通用组件和真实发布表单
- `src/router/`：页面路由、登录保护和管理员角色入口控制
- `src/services/`：匹配 API 适配、图片草稿等页面服务
- `src/stores/`：认证会话、导航缓存和举报 API 适配
- `src/types/`：认证、物品、举报和匹配模块共享类型
- `src/views/`：登录注册、查询、发布、个人管理、匹配通知和管理页面

前端模块边界和数据流见 [前端架构](../docs/architecture/frontend.md)，页面状态和视觉
规则见 [设计资料](../docs/design/README.md)。
