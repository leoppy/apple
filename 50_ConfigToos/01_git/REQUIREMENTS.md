# Git 环境快速配置工具 — 需求规格

## 基本信息

| 项目 | 说明 |
|------|------|
| 语言 | Python 3（无第三方依赖，仅标准库） |
| 平台 | Windows / macOS / Linux |
| 运行方式 | `python git_config.py` 或 `python git_config.py --dry-run` |

---

## 功能模块

### 1. Git 别名配置

通过 `git config --global alias.<name> <command>` 设置以下别名（硬编码即可，不需要用户自定义）：

| 别名 | 对应命令 |
|------|----------|
| `init-sub` | `submodule update --init --recursive` |
| `update-sub` | `submodule update --remote` |
| `rebase-up` | `!git fetch && git rebase origin/master` |
| `force-reset` | `!git reset --hard && git clean -fd` |
| `sync` | `!git fetch origin && git reset --hard origin/master` |
| `f-push` | `!f(){ git fetch --all && git rebase && git push; }; f` |

交互流程：展示别名列表 → 用户确认 → 逐条执行

### 2. Git 全局选项配置

通过 `git config --global <key> <value>` 设置。配置项列表应可扩展（定义在类属性中）：

| Key | Value | 说明 |
|-----|-------|------|
| `submodule.recurse` | `true` | 默认递归处理 submodule |

交互流程：展示配置列表 → 用户确认 → 逐条执行

### 3. 用户名和邮箱配置

- 读取当前已配置的 `user.name` / `user.email` 作为默认值
- 提示用户输入（不允许为空）
- 写入 `git config --global user.name` 和 `user.email`

### 4. SSH 密钥生成

- 检测 `~/.ssh/id_rsa.pub` 是否存在：
  - **存在**：询问是否覆盖（默认否），不覆盖则显示现有公钥
  - **不存在/覆盖**：提示输入邮箱（默认用 git 已配置的邮箱）
- 执行命令：`ssh-keygen -t rsa -b 4096 -C <email> -f <key_path> -N ""`
- 生成后显示公钥内容

### 5. SSH 公钥上传到 GitHub / GitLab

**配置来源**：从系统环境变量或 `.env` 文件读取（优先级：环境变量 > `.env`）：

| 变量名 | 必须 | 用途 |
|--------|------|------|
| `GITHUB_TOKEN` | 否 | GitHub Personal Access Token |
| `GITHUB_USERNAME` | 否 | 预留字段，当前未使用 |
| `GITLAB_URL` | 否 | GitLab 实例 URL（如 `https://gitlab.example.com`） |
| `GITLAB_TOKEN` | 否 | GitLab Personal Access Token |
| `GITLAB_USERNAME` | 否 | 预留字段，当前未使用 |

**GitHub 上传逻辑**：

1. GET `https://api.github.com/user/keys` 查重
2. 已存在相同公钥 → 跳过
3. POST `https://api.github.com/user/keys` 创建新 key（body: `{title, key}`）
4. 错误处理：422 已有 → 跳过；403/404 → 提示 Token 权限不足

**GitLab 上传逻辑**：

1. GET `{GITLAB_URL}/api/v4/user/keys` 查重
2. 已存在相同公钥 → 跳过
3. POST `{GITLAB_URL}/api/v4/user/keys` 创建新 key（body: `{title, key}`）

**用户交互**：

- 展示可用的平台（根据 Token 是否配置）
- 允许选择：仅 GitHub / 仅 GitLab / 同时配置
- 提示输入 Key 标题（默认：`{主机名}-{时间戳}`）

---

## 交互流程

### 主菜单（循环模式）

```
[1] 配置 Git 常用别名 (Alias)
[2] 配置 Git 全局选项
[3] 配置 Git 用户名和邮箱
[4] 生成 SSH 密钥
[5] 配置 SSH 公钥上传
[6] 全部配置（顺序执行 1→2→3→4→5，完成后退出）
[7] 查看当前配置
[8] 退出
```

- 选项 1-5 执行完毕后询问"是否继续其他配置？"，继续则回主菜单，否则显示汇总并退出
- 选项 7 展示后再按回车回到主菜单

### 全局交互模式

每个步骤都遵循：**展示标题 → 询问是否执行（y/n）→ 展示详情 → 二次确认 → 执行 → 逐条打印结果**

---

## 预览模式（`--dry-run`）

- 启动时打印"预览模式，不实际修改"
- 所有 `git config` / `ssh-keygen` / API 调用均不执行，仅打印 `[DRY RUN] 将执行: <命令>`
- 最后的汇总面板提示"以上配置未实际写入"

---

## 健壮性要求

| 场景 | 处理方式 |
|------|----------|
| Git 未安装 | 报错退出 |
| `Ctrl+C` 中断 | 捕获 `KeyboardInterrupt`，友好退出 |
| 用户名/邮箱为空 | 要求重新输入，不允许跳过 |
| 确认输入非法 | 只接受 y/yes/n/no，否则提示重新输入 |
| SSH 密钥已存在 | 提示是否覆盖（默认否） |
| API 网络错误 | 捕获异常，显示错误信息，不中断流程 |
| Token 未配置 | 提示跳过，不报错 |

---

## 输出规范

- 每个模块执行完毕后，有一个**配置汇总面板**，展示：
  - 配置了哪些别名
  - 配置了哪些全局选项
  - 用户名 / 邮箱
  - SSH 密钥路径
  - SSH 上传结果（平台、状态、详情）
- 所有标题用 `=` 分隔线包裹，居中对齐

---

## 不需要实现的内容

- 不需要 Web UI / GUI
- 不需要持久化配置历史或日志文件
- 不需要多语言 / i18n
- 不需要别名或全局配置的用户自定义编辑功能（直接修改代码中的数据结构即可）
- 不需要 Windows 弹窗或图形界面
