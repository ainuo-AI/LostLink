# Frontend

> 状态：首页原型已验证
>
> 最后验证：2026-09-21

前端使用 Vue 3、TypeScript 和 Vite。当前已实现可独立演示的首页，包含关键词搜索、条件筛选、记录类型切换和详情弹窗。所有记录都是保存在 `src/views/HomeView.vue` 中的虚构演示数据，页面尚未调用后端 API。

## 环境要求

- Node.js 18、20 或 22 及以上版本（由当前 Vite 6.4.3 声明）。
- npm。
- 当前验证环境：Node.js 24.14.1、npm 11.11.0、Windows PowerShell。

## 本地运行

以下命令均在 `frontend/` 目录执行。Windows PowerShell 建议使用 `npm.cmd`：

```powershell
npm.cmd install
npm.cmd run dev
```

启动成功后，Vite 会输出 `http://127.0.0.1:5173/`。页面不需要 `.env` 或后端服务即可打开。

在 CMD、Git Bash、macOS 或 Linux 中可使用：

```bash
npm install
npm run dev
```

## 检查与构建

```powershell
npm.cmd run type-check
npm.cmd run build
```

- `type-check` 使用 `vue-tsc` 检查 TypeScript 和 Vue 组件类型。
- `build` 先执行类型检查，再生成 `dist/` 生产构建结果。
- 2026-09-21 执行两项命令均成功，Vite 构建完成且未报错。当前未配置单元测试或端到端测试，不应将上述检查表述为测试通过。

## 常见问题

- PowerShell 报错“禁止运行脚本”：将 `npm` 改为 `npm.cmd`，不需要修改系统执行策略。
- `npm.cmd install` 失败：先运行 `node --version` 和 `npm.cmd --version` 确认环境，再检查网络是否可访问 npm 包注册表。
- 5173 端口被占用：Vite 会报告启动失败；先停止占用该端口的旧开发服务后重试。

## 目录职责

- `src/api/`：后端接口访问封装
- `src/assets/`：需要参与构建的静态资源
- `src/components/`：通用组件
- `src/layouts/`：页面布局
- `src/router/`：路由配置
- `src/stores/`：全局状态
- `src/styles/`：全局样式与设计变量
- `src/types/`：共享类型
- `src/views/`：页面级视图
- `public/`：不参与构建处理的公共资源
- `tests/`：前端测试

`src/api/`、`src/layouts/`、`src/router/`、`src/stores/` 和 `tests/` 目前仅为预留结构，不含业务实现。
