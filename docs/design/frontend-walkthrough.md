# LostLink 前端首页讲解

这份说明用于帮助组员阅读当前首页代码，也可作为课堂演示时的答辩提纲。

## 1. 代码在哪里

```text
frontend/
├─ index.html                 # 浏览器入口，提供 #app 挂载点
├─ package.json               # 依赖和 npm 命令
├─ vite.config.ts             # Vite 开发服务器配置
└─ src/
   ├─ main.ts                  # 创建并挂载 Vue 应用
   ├─ App.vue                  # 根组件
   ├─ views/HomeView.vue       # 首页数据、状态和业务交互
   ├─ components/SiteHeader.vue
   ├─ components/ItemCard.vue
   ├─ components/ItemDetailDialog.vue
   ├─ types/item.ts            # 共享 TypeScript 数据类型
   └─ styles/main.css          # 全局样式和响应式布局
```

## 2. 整体执行流程

1. 浏览器打开 `index.html`。
2. `index.html` 加载 `src/main.ts`。
3. `main.ts` 创建 Vue 应用，将 `App.vue` 挂载到 `#app`。
4. `App.vue` 展示 `HomeView.vue`。
5. `HomeView.vue` 组合导航、卡片和详情弹窗等可复用组件。

## 3. 搜索和筛选如何实现

- `ref()` 保存关键词、类别、校区、东丽区域、时间范围和记录类型。
- `v-model` 实现表单控件与状态的双向绑定。
- `computed()` 根据所有条件计算 `filteredItems`。
- `items.filter()` 遍历每条记录，只保留同时满足关键词、类型、类别、校区、区域和时间条件的记录。
- 校园地点是两级联动结构：东丽校区继续区分北区/南区，宁河校区不继续细分。
- 当 `filteredItems` 为空时，`v-if/v-else` 会显示空结果提示。

## 4. 组件如何通信

- 父组件通过 `:item="item"` 把数据传给卡片，这叫 Props 传值。
- 卡片通过 `$emit('open', item)` 通知父组件打开详情，这叫自定义事件。
- 父组件把点击的记录保存到 `selectedItem`。
- `selectedItem` 有值时，`ItemDetailDialog` 通过 `v-if` 渲染；关闭时将它恢复为 `null`。

## 5. 响应式布局如何实现

- 桌面端使用 CSS Grid 组成“左侧筛选 + 右侧结果”。
- 宽度低于 `1080px` 时，卡片由三列改为两列。
- 宽度低于 `820px` 时，导航和筛选面板转为移动端样式。
- 宽度低于 `560px` 时，卡片改为单列，详情弹窗由左右排列改为上下排列。

## 6. 老师可能问的问题

### 为什么使用 Vue 3？

项目架构文档已规定前端使用 Vue 3。Vue 的响应式数据、单文件组件和模板语法适合将页面拆成可复用的业务组件。

### 为什么使用 TypeScript？

`LostFoundItem` 类型可以统一卡片、弹窗和未来 API 的数据结构，让字段缺失或类型错误在编译阶段就被发现。

### 为什么要拆成多个组件？

导航、物品卡片和详情弹窗的职责不同。拆分后更容易阅读、复用、测试和独立修改。

### 现在有没有调用后端？

还没有。当前是前端交互原型，演示数据保存在 `HomeView.vue`。等团队确定 API 契约后，会把请求封装在 `src/api/`，View 只负责页面组合。

### 如何保证页面可用性？

当前已实现键盘 Enter 打开卡片、Esc 关闭弹窗、语义化标签、焦点样式、空结果状态以及 `prefers-reduced-motion` 动画降级。

## 7. 当前局限与下一步

- 当前数据仅用于演示，刷新后不会从数据库读取。
- 发布失物、登记拾物、匹配通知和个人中心页尚未实现。
- 下一步应先评审 API 字段，然后在 `src/api/` 中增加请求封装，将演示数据替换为真实响应。
