import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 通过 Vue 插件编译 .vue 单文件组件。
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
  },
})
