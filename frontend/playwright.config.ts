import { defineConfig, devices } from '@playwright/test'

const databaseUrl = process.env.E2E_DATABASE_URL
if (!databaseUrl) {
  throw new Error('请先启动隔离测试数据库并设置 E2E_DATABASE_URL，详见 docs/development/testing.md。')
}
const database = new URL(databaseUrl)
if (!['127.0.0.1', 'localhost'].includes(database.hostname) || database.pathname !== '/lostlink_test') {
  throw new Error('浏览器测试只允许连接本机的 lostlink_test 数据库。')
}

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  // 不用重试掩盖首轮失败，测试必须使用独立账号且可重复运行。
  retries: 0,
  workers: 1,
  timeout: 45_000,
  globalTimeout: 10 * 60_000,
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'test-results/e2e.xml' }],
  ],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    timezoneId: 'Asia/Shanghai',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: 'uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port 18000',
      cwd: '../backend',
      url: 'http://127.0.0.1:18000/health',
      env: {
        DATABASE_URL: databaseUrl,
        APP_ENV: 'test',
        MATCHING_AI_ENABLED: 'false',
        CORS_ORIGINS: '["http://127.0.0.1:4173"]',
        UPLOAD_DIRECTORY: 'var/e2e-uploads',
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: 'npm run build && npm run preview -- --host 127.0.0.1 --port 4173 --strictPort',
      url: 'http://127.0.0.1:4173',
      env: { VITE_API_BASE_URL: 'http://127.0.0.1:18000' },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
})
