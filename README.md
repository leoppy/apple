# company-dev-tools

公司内部开发辅助工具集合。

## 内容

| 目录 | 说明 |
|---|---|
| `01_Jenkins/` | Jenkins job 查询和参数安全更新工具 |
| `10_miniTools/01_autosarSpecDownload/` | HTTP 目录递归下载工具 |
| `50_ConfigToos/01_git/` | Git 环境快速配置工具 |

## 使用前配置

复制 `.env.example` 为 `.env`，按需填写自己的配置。`.env` 已加入 `.gitignore`，不要提交个人 token、账号密码或本机路径。

```powershell
Copy-Item .env.example .env
```

## 安全约定

- 不提交 `.env`、下载产物、缓存文件、Jenkins 备份文件。
- 每个同事使用自己的 Token 和账号。
- 推送前建议执行一次敏感信息扫描：

```powershell
rg -n -i "token|password|secret|authorization|private-token|192\.168\.|D:\\|C:\\Users" .
```

# test workflow fix
