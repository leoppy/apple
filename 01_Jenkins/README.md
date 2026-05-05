# Jenkins 工具

## 配置

复制 `.env.example` 为 `.env`，或使用仓库根目录的 `.env`。

```dotenv
JENKINS_URL=
JENKINS_USER=
JENKINS_TOKEN=
```

## 查询 Job

```powershell
python check_pipeline.py folder/job-name
```

## 查看参数

```powershell
python safe_update_job_param.py list --job folder/job-name
python safe_update_job_param.py get --job folder/job-name --param-name PARAM_NAME
```

## 修改参数

先使用 `--dry-run` 检查结果：

```powershell
python safe_update_job_param.py set --job folder/job-name --param-name PARAM_NAME --new-value VALUE --dry-run
```

确认后去掉 `--dry-run`。
