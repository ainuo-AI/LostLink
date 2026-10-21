import { randomUUID } from 'node:crypto'
import { expect, test, type Page } from '@playwright/test'

const apiUrl = 'http://127.0.0.1:18000/api/v1'
const password = 'LostLink-test-password-2026'

async function registerAndLogin(page: Page) {
  const account = `e2e-${randomUUID()}`
  await page.goto('/register')
  await page.getByLabel('校园账号', { exact: true }).fill(account)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByLabel('确认密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '注册账号', exact: true }).click()
  await expect(page.getByRole('status')).toHaveText('账号注册成功，请使用新账号登录。')
  await expect(page.getByLabel('校园账号', { exact: true })).toHaveValue(account)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page).toHaveURL('/my')
  await expect(page.getByRole('heading', { name: account, exact: true })).toBeVisible()
  return account
}

test('未登录不能发布，错误密码不能建立会话', async ({ page, request }) => {
  const account = `e2e-${randomUUID()}`
  const registration = await request.post(`${apiUrl}/auth/register`, {
    data: { account, password },
  })
  expect(registration.status()).toBe(201)

  await page.goto('/publish/lost')
  await expect(page).toHaveURL(/\/login\?.*redirect=/)
  await page.getByLabel('校园账号', { exact: true }).fill(account)
  await page.getByLabel('密码', { exact: true }).fill('incorrect-password')
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page.getByRole('alert')).toHaveText('账号或密码错误，或账号暂时无法登录。')
  await expect(page).toHaveURL(/\/login\?/)
  const anonymous = await request.get(`${apiUrl}/users/me`)
  expect(anonymous.status()).toBe(401)

  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page).toHaveURL('/publish/lost')
  await expect(page.getByRole('heading', { name: '发布失物', exact: true })).toBeVisible()
})

for (const type of ['lost', 'found'] as const) {
  test(`${type === 'lost' ? '失物' : '拾物'}：注册登录、发布、搜索、编辑、关闭与退出`, async ({ page }) => {
    await registerAndLogin(page)
    const title = `CI-${type}-${randomUUID().slice(0, 8)}`
    await page.goto(`/publish/${type}`)
    await page.getByLabel('物品名称').fill(title)
    await page.getByLabel('物品类别').selectOption('数码')
    await page.getByLabel('特征描述').fill('自动化测试专用物品，外壳有蓝色标记，不涉及真实个人信息。')
    await page.getByLabel(type === 'lost' ? '丢失校区' : '拾获校区').selectOption('东丽校区')
    await page.getByLabel('校区区域').selectOption('北区')
    const location = page.getByLabel(type === 'lost' ? '具体丢失地点' : '具体拾获地点')
    await expect(location).toBeEnabled()
    await expect(location.locator('option')).not.toHaveCount(1)
    await location.selectOption({ index: 1 })
    // 浏览器固定为上海时区，以同一时区生成过去时间，避免 CI 主机时区影响校验。
    const occurredAt = await page.evaluate(() => {
      const date = new Date(Date.now() - 60 * 60_000)
      const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
      return local.toISOString().slice(0, 16)
    })
    await page.getByLabel(type === 'lost' ? '丢失时间' : '拾获时间').fill(occurredAt)
    await page.getByLabel('手机号或邮箱').fill('ci@example.invalid')
    if (type === 'found') {
      await page.getByLabel('保管方式').selectOption('self')
      await page.getByLabel('暂存地点').selectOption({ index: 1 })
      await page.getByLabel('可联系时间或范围').fill('工作日中午')
    }
    await page.getByRole('button', { name: type === 'lost' ? '提交发布' : '提交登记' }).click()
    await expect(page.getByRole('heading', {
      name: type === 'lost' ? '失物发布成功' : '拾物登记成功',
    })).toBeVisible()

    await page.getByRole('link', { name: '返回首页', exact: true }).click()
    await page.getByLabel('搜索物品').fill(title)
    await page.getByRole('button', { name: '搜索', exact: true }).click()
    await page.getByRole('heading', { name: title, exact: true }).click()
    await expect(page).toHaveURL(/\/items\/\d+$/)
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible()

    await page.goto('/my')
    if (type === 'found') await page.getByRole('button', { name: '我的拾物', exact: true }).click()
    const record = page.locator('.profile-record').filter({ hasText: title })
    await record.getByRole('button', { name: '编辑', exact: true }).click()
    const dialog = page.getByRole('dialog', { name: '编辑记录' })
    const editedTitle = `${title}-edited`
    await dialog.getByLabel('名称', { exact: true }).fill(editedTitle)
    await dialog.getByRole('button', { name: '保存', exact: true }).click()
    await expect(dialog).not.toBeVisible()
    const editedRecord = page.locator('.profile-record').filter({ hasText: editedTitle })
    await expect(editedRecord).toContainText('状态：进行中')
    // 刷新后仍能读到修改，证明数据已经落库。
    await page.reload()
    if (type === 'found') await page.getByRole('button', { name: '我的拾物', exact: true }).click()
    await expect(editedRecord).toBeVisible()
    // 关闭操作先确认，再填写处理说明；两次弹窗都需要回应。
    page.on('dialog', dialog => dialog.accept(dialog.type() === 'prompt' ? 'CI 测试关闭' : undefined))
    await editedRecord.getByRole('button', { name: '关闭记录', exact: true }).click()
    await expect(editedRecord).toContainText('状态：已关闭')
    await expect(editedRecord.getByRole('button', { name: '编辑', exact: true })).toHaveCount(0)

    await page.getByRole('button', { name: '退出登录', exact: true }).click()
    await expect(page).toHaveURL('/')
    await page.goto('/my')
    await expect(page).toHaveURL(/\/login\?.*redirect=/)
  })
}
