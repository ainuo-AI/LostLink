# Frontend

前端使用 Vue 3 + TypeScript + Vite。当前已实现可独立演示的首页，包含关键词搜索、条件筛选、记录类型切换和详情弹窗。演示数据目前保存在页面中，后续可通过 `src/api/` 替换为后端接口。

## 本地运行

```bash
npm install
npm run dev
```

## 检查与构建

```bash
npm run type-check
npm run build
```

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
