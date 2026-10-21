// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 通过 Vue 插件编译 .vue 单文件组件。
// 设计文档对应：图4-4、表4-1 Vue/Vite 前端的本地开发运行配置。
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
  },
})
