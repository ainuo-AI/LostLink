# 参与 LostLink 开发

## 基本流程

1. 从 `main` 创建短期功能分支。
2. 一个分支只处理一个明确任务。
3. 开发前先写清需求、影响范围和验收条件。
4. 提交前完成本模块的检查与测试。
5. 通过 Pull Request 合并，避免直接向 `main` 提交。

## 分支命名

- `feature/<name>`：新增功能
- `fix/<name>`：缺陷修复
- `docs/<name>`：文档修改
- `refactor/<name>`：不改变行为的重构
- `chore/<name>`：工程配置与杂项

## 提交信息

建议使用：

```text
<type>(<scope>): <summary>
```

例如：

```text
docs(readme): add project structure guide
```

## Pull Request 要求

- 说明修改目的，而不只是罗列文件。
- 标明修改范围和验证方式。
- 不提交密钥、个人配置、运行日志或生成文件。
- 业务功能与无关格式化修改应拆分提交。
- 接口或数据结构变化必须同步更新文档。
