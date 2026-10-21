import { defineConfig } from 'vitest/config'

export default defineConfig({
  // 浏览器用例由 Playwright 执行，避免 Vitest 把 e2e/*.spec.ts 当作单元测试。
  test: { include: ['src/**/*.test.ts'] },
})
