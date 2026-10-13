// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/main.css'

// 应用入口：先注册 Vue Router，再把根组件挂载到 index.html 的 #app 节点。
// 设计文档对应：图2-1、图4-4、表4-1 浏览器中注册路由并挂载 Vue 客户端。
createApp(App).use(router).mount('#app')
