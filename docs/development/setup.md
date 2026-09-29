# 本地开发环境

> 状态：前端步骤已验证；后端和数据库步骤等待工程初始化。
>
> 最后验证：2026-09-21

本文提供从获取仓库到验证当前可运行部分的完整入口。前端和后端的专项命令分别维护在 [frontend/README.md](../../frontend/README.md) 和 [backend/README.md](../../backend/README.md)。

## 当前可以运行什么

- 可以独立运行 Vue 前端首页原型。
- 前端使用页面内虚构数据，不需要 `.env`、数据库或后端服务。
- 后端目录目前只是结构骨架，不能安装或启动。
- MySQL、Alembic、真实 API 和端到端测试尚未配置。

## 1. 获取项目

```powershell
git clone https://github.com/ainuo-AI/LostLink.git
cd LostLink
```

默认开发分支为 `main`。当前仓库不使用 Git submodule 或 Git LFS。

## 2. 准备前端环境

当前前端使用 Vue 3、TypeScript 和 Vite。项目最后在 Node.js 24.14.1 和 npm 11.11.0 上验证；Vite 6.4.3 支持符合其 `engines` 声明的 Node.js 版本。

先确认本机工具：

```powershell
node --version
npm.cmd --version
```

Windows PowerShell 建议使用 `npm.cmd`，避免本机执行策略阻止 `npm.ps1`。

## 3. 安装并启动前端

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Vite 默认显示类似 `http://127.0.0.1:5173/` 的本地地址。打开页面后应能看到演示记录，并使用关键词、类别、校区、时间和记录类型筛选。

停止服务时在运行终端按 `Ctrl+C`。

## 4. 检查前端

在 `frontend/` 目录执行：

```powershell
npm.cmd run type-check
npm.cmd run build
```

预期结果：

- 类型检查退出码为 0。
- Vite 在 `frontend/dist/` 生成生产构建结果。
- `dist/` 是本地产物，不提交到 Git。

当前没有前端单元测试或端到端测试，因此不能把以上两项检查表述为“测试通过”。

## 5. 后端与本地依赖

后端尚未初始化，目前没有经过验证的 Python 版本、依赖安装、环境变量、数据库 migration 或启动命令。不要根据目录名称自行假设这些能力已经存在。

初始化后端时，应在 `backend/README.md` 中补充并验证：

1. 支持的 Python 版本和依赖管理方式。
2. `.env.example` 中每个变量的用途和非敏感示例。
3. MySQL 或其他本地依赖的启动与健康检查方法。
4. Alembic 升级、查看版本和安全回滚命令。
5. FastAPI 开发服务、健康检查和 OpenAPI 地址。
6. 格式检查、静态检查和测试命令。

完整系统可以宣称“本地搭建完成”前，应验证前端能够访问真实 API、migration 可从空数据库执行、最小测试集通过，并且所有服务停止后可以重新启动。

## 常见问题

### PowerShell 禁止运行脚本

使用 `npm.cmd` 代替 `npm`，无需为项目修改系统执行策略。

### 5173 端口被占用

Vite 可能选择其他端口或报告冲突。以终端实际显示的地址为准；需要固定端口时先停止旧的开发服务。

### 依赖安装失败

先记录 `node --version` 和 `npm.cmd --version`，再检查网络、npm registry 和锁文件是否被意外修改。不要直接删除锁文件来掩盖依赖问题。

## 文档维护要求

- 修改运行时版本、依赖管理、环境变量或启动命令时，同步更新本文和对应子项目 README。
- 根文档只保留完整搭建顺序；专项参数和命令优先维护在离代码最近的 README 中。
- 命令必须在干净环境中验证，不再适用的步骤直接删除。
- 只适用于特定操作系统的步骤应明确标注，并提供其他平台可采用的等价命令。
