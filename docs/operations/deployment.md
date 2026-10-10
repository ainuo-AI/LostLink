# 部署说明

> 状态：上线前规范。前端、后端和 MySQL 已完成当前全部业务模块的本地联调；生产平台、配置、监控、备份尚未完成，不能把当前工程视为可发布的完整系统。

## 环境

建议至少区分：

- `local`：个人开发环境，可使用模拟外部服务。
- `test`：自动测试环境，数据可以重建。
- `staging`：接近生产的验收环境，不使用生产密钥或生产个人数据。
- `production`：正式环境，限制访问和变更权限。

## 发布前检查

- [ ] 目标提交已经过评审，持续集成检查通过
- [ ] 环境变量和依赖服务已经配置，但密钥未写入仓库
- [ ] 数据库已备份，migration 已在代表性数据上验证
- [ ] 已确认发布顺序及前后端兼容窗口
- [ ] 已写明回滚条件、负责人和回滚版本
- [ ] 涉及用户行为的变化已更新需求、API 和变更记录

## 建议发布顺序

1. 记录待发布版本、提交号和负责人。
2. 备份需要保护的数据并验证备份可用。
3. 部署向后兼容的数据库 migration。
4. 部署后端并完成健康检查。
5. 部署前端。
6. 执行核心流程冒烟测试。
7. 观察错误率、延迟和资源使用情况。
8. 记录发布结果；失败时按回滚方案处理。

当前已知前端构建命令为 `npm.cmd run build`，本地产物为 `frontend/dist/`；后端本地健康检查路径为 `/health`。生产部署平台、访问地址、构建发布命令和冒烟测试步骤仍待确认，不能直接把本地命令当作生产发布脚本。

## 回滚原则

- 应用版本优先回滚到最近一个已验证版本。
- 数据库优先采用向前修复；只有确认不会丢失新数据时才执行 downgrade。
- 外部服务异常时优先关闭对应能力或使用降级路径，不反复重试放大故障。
- 回滚后重新执行健康检查和核心流程冒烟测试。

## 环境变量清单

以下变量按当前两个 `.env.example` 核对。示例口令仅供本地开发，不是生产配置；外部服务尚无已确认变量。不得填写真实值。

| 变量 | 用途 | 必需 | 敏感 | 状态 |
| --- | --- | --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy MySQL 连接地址 | 后端本地运行需要 | 是 | `backend/.env.example` 已提供本地示例；生产值待确认 |
| `MYSQL_DATABASE`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD`、`MYSQL_PORT` | 本地 Compose MySQL 初始化与端口 | 使用当前 Compose 时需要 | 密码是 | `backend/.env.example` 已列出本地示例 |
| `APP_NAME`、`APP_VERSION`、`APP_ENV`、`API_V1_PREFIX`、`CORS_ORIGINS` | 后端应用与跨域配置 | 按环境 | 否 | `backend/.env.example` 已列出 |
| `VITE_API_BASE_URL` | 前端 API 基础地址 | 首页、认证和物品管理请求需要 | 否 | `frontend/.env.example` 已列出 |
| `AUTH_SESSION_TTL_HOURS` | Bearer 会话有效小时数 | 后端认证 | 否 | 默认 168 |
| `AUTH_MAX_LOGIN_ATTEMPTS` | 临时锁定前连续失败次数 | 后端认证 | 否 | 默认 5 |
| `AUTH_LOGIN_LOCK_MINUTES` | 登录临时锁定分钟数 | 后端认证 | 否 | 默认 15 |
| `UPLOAD_DIRECTORY` | 本地图片受控存储目录 | 使用图片上传时需要 | 否 | 默认 `var/uploads`；生产应使用持久卷或对象存储 |
| `UPLOAD_MAX_BYTES` | 单张图片最大字节数 | 图片上传 | 否 | 默认 5242880 |

2026-10-07 新增可选的 `MATCHING_AI_ENABLED`、`MATCHING_AI_BASE_URL`、`MATCHING_AI_API_KEY`、`MATCHING_AI_MODEL`、超时、候选数量、融合权重及图片预算配置。只有启用 AI 匹配时需要供应商地址、密钥和模型；密钥为敏感项。完整配置和同步调用限制见 [图文匹配接入说明](../api/multimodal-matching.md)。

`SECRET_KEY` 及地图、对象存储、站外通知变量尚未出现在当前示例配置中；只有对应能力完成设计与实现后才能补充，不能标为当前必需。

## 发布后记录

在 Release 或对应 Issue 中记录版本、时间、负责人、migration revision、验证结果、异常和回滚情况。影响使用者或开发者的变化同步写入 [CHANGELOG.md](../../CHANGELOG.md)。
