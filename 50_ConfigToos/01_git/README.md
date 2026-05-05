# Git 环境快速配置工具

交互式配置 Git 常用别名、全局选项、用户名邮箱和 SSH key 上传。

## 使用

```powershell
python git_config.py
```

预览模式：

```powershell
python git_config.py --dry-run
```

## 可扩展全局配置

在 `git_config.py` 的 `self.git_global_configs` 中追加配置：

```python
{
    "key": "pull.rebase",
    "value": "true",
    "description": "默认使用 rebase 拉取",
}
```

## SSH key 自动上传

如需上传到 GitHub/GitLab，复制 `.env.example` 到仓库根目录 `.env` 并填写自己的值：

```dotenv
GITHUB_TOKEN=
GITLAB_URL=
GITLAB_TOKEN=
```
