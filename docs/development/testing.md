# 测试策略

> 状态：已配置 GitHub Actions、Vitest、pytest、MySQL 集成测试和 Playwright Chromium 浏览器测试。前端现有 7 个文件、22 个测试，后端有 95 个默认测试、3 个 MySQL 集成测试；浏览器包含 3 条核心流程。
>
> 前端、后端与 MySQL 集成测试最后验证：2026-10-06。

2026-10-07 图文匹配改动验证：后端 55 个测试通过、3 个 MySQL 测试未启用，Ruff 与前端类型检查/生产构建通过。新增供应商模拟测试覆盖图文请求、融合分数、候选上限、输出校验及失败降级；未调用真实模型。上述 2026-10-06 MySQL 和前端单元测试记录保留为上次验证结果。

2026-10-21 CI 接入本地验证：前端 22 个测试、后端 95 个默认测试、3 个真实 MySQL 测试和 3 个 Chromium 流程通过；Ruff、浏览器测试类型检查、生产构建、actionlint 工作流检查及迁移的部分/完整回滚再升级通过。前端使用 `npm ci` 验证锁文件安装；本地 Node.js 为 25，CI 固定为 22。GitHub 上是否通过以对应提交的 Actions 记录为准。

## 测试目标

- 证明需求验收条件已经满足。
- 尽早发现业务规则、权限、接口契约和数据库变化中的回归。
- 让测试失败能够指出具体问题，而不是依赖一次性人工演示。

## 测试分层

| 层级 | 关注内容 | 建议位置 |
| --- | --- | --- |
| 后端单元测试 | Service、匹配规则、校准规则和工具函数 | `backend/tests/` |
| 后端集成测试 | API、权限、Repository、数据库 migration | `backend/tests/` |
| 前端单元测试 | 接口转换、举报/匹配 API、表单校验和通知状态 | `frontend/src/**/*.test.ts` |
| 契约测试 | 请求、响应、状态码和错误格式与 OpenAPI 一致 | 前后端测试目录 |
| 端到端测试 | 认证、失物/拾物发布、搜索、编辑和关闭流程 | `frontend/e2e/`（Playwright） |

## CI 流水线

配置文件为 `.github/workflows/ci.yml`，在 PR、推送到 `main` 或手动运行时触发。使用 Node.js 22、Python 3.12、锁文件安装依赖，不需要配置生产密钥。

1. `Frontend checks`：Vitest、浏览器测试 TypeScript 检查、Vue 类型检查和生产构建。
2. `Backend checks`：Ruff 与 `pytest -m 'not mysql'`，使用内存仓储。
3. `MySQL and browser tests`：前两项成功后创建一次性 MySQL 8.4；验证迁移的部分回滚/再升级、完整回滚/再升级，导入演示数据，执行全部 MySQL 测试，再启动前后端运行 Playwright。
4. `CI passed`：只有前三项全部成功才通过；失败、取消或被跳过都不能视为通过。

JUnit XML、Playwright HTML 报告和失败截图/视频/trace 作为 Actions artifacts 保留 7 天。报告可能包含测试会话信息，使用合成账号和测试数据，不上传 `.env` 或真实业务资料。可在本地执行 `npm run test:e2e:report` 打开浏览器报告。

管理员可在 GitHub `Settings → Rules → Rulesets` 或分支保护中，将 `CI passed` 设为 `main` 的必需检查并要求 PR 合并。工作流文件本身不会修改仓库保护规则；首次在 GitHub 运行成功后再选择检查项。修改代码后也需要重新通过 CI。

## 本地复现完整测试

默认单元与快速接口测试无需数据库：

```bash
# 在 frontend/ 执行
npm ci
npm test
npm run type-check:e2e
npm run build

# 在 backend/ 执行
uv sync --locked
uv run --frozen ruff check .
uv run --frozen pytest -m 'not mysql'
```

完整集成测试使用 `backend/compose.test.yaml`，项目名为 `lostlink-test`，默认端口 `13306`，不挂载开发数据库卷。可用 `MYSQL_TEST_PORT` 覆盖端口，并同步修改下方连接地址。以下迁移回滚命令仅允许用于该一次性测试库。

在 macOS/Linux 的 `backend/` 目录执行：

```bash
docker compose -f compose.test.yaml up -d --wait
export DATABASE_URL='mysql+pymysql://lostlink_test:lostlink_test@127.0.0.1:13306/lostlink_test?charset=utf8mb4'
export TEST_DATABASE_URL="$DATABASE_URL"
export E2E_DATABASE_URL="$DATABASE_URL"
export APP_ENV=test
export MATCHING_AI_ENABLED=false
uv sync --locked
uv run --frozen alembic upgrade head
uv run --frozen alembic downgrade 20261006_0004
uv run --frozen alembic upgrade head
uv run --frozen alembic downgrade 20260930_0001
uv run --frozen alembic upgrade head
uv run --frozen alembic downgrade base
uv run --frozen alembic upgrade head
uv run --frozen python -m scripts.seed_items
uv run --frozen pytest -m mysql
```

Windows PowerShell 使用相同命令，但用下面方式设置环境变量：

```powershell
$env:DATABASE_URL = 'mysql+pymysql://lostlink_test:lostlink_test@127.0.0.1:13306/lostlink_test?charset=utf8mb4'
$env:TEST_DATABASE_URL = $env:DATABASE_URL
$env:E2E_DATABASE_URL = $env:DATABASE_URL
$env:APP_ENV = 'test'
$env:MATCHING_AI_ENABLED = 'false'
```

然后在同一终端切换到 `frontend/`：

```bash
npm ci
npx playwright install chromium
npm run test:e2e
```

PowerShell 使用 `npm.cmd`、`npx.cmd`，无需改变系统执行策略。Linux 若缺少浏览器系统依赖，使用 `npx playwright install --with-deps chromium`。

Playwright 强制要求 `E2E_DATABASE_URL` 指向本机 `lostlink_test`，不会复用开发服务。后端端口为 `18000`，生产构建预览端口为 `4173`；配置负责启动、等待就绪和停止这两个服务。外部 AI 调用关闭，上传目录单独使用 `backend/var/e2e-uploads/`。

每个浏览器用例使用随机的新账号和物品名称，不依赖其他用例的执行顺序。测试数据保留到容器销毁，以便排查失败；测试结束后在 `backend/` 执行以下命令清理容器和测试数据：

```bash
docker compose -f compose.test.yaml down -v
```

浏览器用例覆盖未登录跳转、错误密码、注册登录，以及失物和拾物的发布、搜索、详情、编辑落库、关闭和退出。图片浏览器交互、匹配反馈、管理员 UI 和跨浏览器兼容性仍需后续补充；已有后端测试不能代替这些浏览器验收。

## 当前前端测试

在 `frontend/` 目录执行：

```powershell
npm.cmd test
npm.cmd run type-check
npm.cmd run build
```

Vitest 当前覆盖认证请求与 Bearer 请求头、物品查询/发布/个人列表/状态请求、FastAPI 错误转换、数据转换、时间显示、举报与匹配 API、草稿隔离、表单与图片规则。2026-10-06 的执行结果为 17/17 通过，类型检查和生产构建通过。类型检查与构建不能代替浏览器端端到端测试；Vue 组件交互、路由守卫、图片实际选择与预览尚未纳入自动化测试。

## 当前后端测试

在 `backend/` 目录执行：

```bash
uv run pytest
```

默认测试使用 FastAPI 测试客户端和内存仓储，不连接个人数据库，也不会调用外部服务。测试覆盖认证与权限、物品边界、图片上传关联、举报审核、候选生成与反馈、用户限制和校准版本生命周期。设置 `TEST_DATABASE_URL` 后执行 `uv run pytest -m mysql`，可以在已迁移的隔离 MySQL 验证查询、用户会话以及物品写入与状态审计。2026-10-06 执行结果为 33 个默认测试和 3 个 MySQL 集成测试通过。

Alembic migration 还需要在一次性数据库中验证 `upgrade head → downgrade base → upgrade head`。不得使用包含有效数据的共享数据库执行破坏性回滚测试。

## 每个功能至少验证

- 一条正常路径。
- 必填项为空、格式错误和边界值。
- 未登录、无权限和资源不存在。
- 重复提交、依赖服务失败或超时。
- 与本次修改相关的历史行为没有回归。

涉及匹配策略时，使用固定数据集验证排序、阈值和解释字段，避免测试依赖实时外部 AI 输出。

## 测试数据

- 测试数据由 fixture 或工厂创建，不依赖个人本地数据库。
- 自动测试不得调用真实付费服务或向真实用户发送通知。
- 示例账号、图片和位置不得包含真实个人信息。
- 每个测试独立清理状态，不能依赖执行顺序。

## Pull Request 验证记录

作者应在 Pull Request 中写明：

- 执行过的自动检查及结果。
- 未执行的检查及原因。
- 需要评审者手工验证的步骤。
- 涉及界面时的关键状态截图或录屏。

## 合并门槛

- 与改动相关的自动测试通过。
- 新增业务规则具有对应测试。
- 修复缺陷时，优先增加能够复现该缺陷的回归测试。
- 暂时跳过的测试必须关联 Issue，并说明恢复条件。
- 不以降低断言质量或删除有效测试来换取通过。

覆盖率可用于发现测试空白，但不能单独代表质量。团队应在工程初始化和首批测试稳定后，再确定合理的覆盖率门槛。
