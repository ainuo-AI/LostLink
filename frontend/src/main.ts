import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/main.css'

// 应用入口：先注册 Vue Router，再把根组件挂载到 index.html 的 #app 节点。
createApp(App).use(router).mount('#app')
