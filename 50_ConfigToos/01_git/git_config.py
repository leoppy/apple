#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 环境快速配置工具
支持 Windows/macOS/Linux，包含：
1. Git 常用别名配置
2. Git 用户名和邮箱配置
3. SSH 密钥生成
4. SSH 公钥配置上传到 GitHub / GitLab
"""

import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


class GitConfigTool:
    def __init__(self):
        self.dry_run = False
        self.repo_root = Path(__file__).resolve().parents[2]
        self.env_path = self.repo_root / ".env"
        self.default_gitlab_url = os.environ.get("GITLAB_URL", "")
        self.env_config = self.load_env_config()
        self.git_aliases = {
            "init-sub": "submodule update --init --recursive",
            "update-sub": "submodule update --remote",
            "rebase-up": "!git fetch && git rebase origin/master",
            "force-reset": "!git reset --hard && git clean -fd",
            "sync": "!git fetch origin && git reset --hard origin/master",
            "f-push": "!f(){ git fetch --all && git rebase && git push; }; f",
        }
        self.git_global_configs = [
            {
                "key": "submodule.recurse",
                "value": "true",
                "description": "默认递归处理 submodule",
            },
        ]
        self.config_summary = {
            "aliases": [],
            "global_configs": [],
            "user_name": None,
            "user_email": None,
            "ssh_key": None,
            "ssh_uploads": [],
        }

    def load_env_config(self):
        """从仓库根目录 .env 和系统环境变量读取配置。"""
        config = {}

        if self.env_path.exists():
            for raw_line in self.env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip('"').strip("'")

        for key in (
            "GITHUB_TOKEN",
            "GITHUB_USERNAME",
            "GITLAB_URL",
            "GITLAB_USERNAME",
            "GITLAB_TOKEN",
        ):
            env_value = os.environ.get(key)
            if env_value:
                config[key] = env_value

        return config

    def run_cmd(self, cmd, capture_output=True):
        """执行命令，支持 dry-run。"""
        if self.dry_run:
            printable = cmd if isinstance(cmd, str) else " ".join(cmd)
            print(f"[DRY RUN] 将执行: {printable}")
            return True, "", ""

        try:
            result = subprocess.run(
                cmd,
                shell=isinstance(cmd, str),
                capture_output=capture_output,
                text=True,
                encoding="utf-8",
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as exc:
            return False, "", str(exc)

    def print_header(self, title):
        """打印标题。"""
        print("\n" + "=" * 50)
        print(f"{title:^50}")
        print("=" * 50)

    def confirm(self, prompt, default=True):
        """用户确认。"""
        default_str = "y" if default else "n"
        while True:
            response = input(f"\n{prompt} (y/n, 默认{default_str}): ").strip().lower()
            if not response:
                return default
            if response in {"y", "yes"}:
                return True
            if response in {"n", "no"}:
                return False
            print("请输入 y 或 n")

    def prompt_text(self, prompt, default=""):
        """读取文本输入，支持默认值。"""
        suffix = f" (默认: {default})" if default else ""
        response = input(f"{prompt}{suffix}: ").strip()
        return response or default

    def prompt_choice(self, prompt, choices, default):
        """读取单选项输入。"""
        options = "/".join(choices)
        while True:
            response = input(f"{prompt} ({options}, 默认{default}): ").strip().lower()
            if not response:
                return default
            if response in choices:
                return response
            print(f"请输入以下选项之一: {options}")

    def check_git_installed(self):
        """检查 Git 是否已安装。"""
        success, _, _ = self.run_cmd(["git", "--version"])
        if not success:
            print("错误：未检测到 Git，请先安装 Git 并加入系统 PATH。")
            return False
        return True

    def config_aliases(self):
        """配置 Git 别名。"""
        self.print_header("配置 Git 常用别名")

        if not self.confirm("是否要配置 Git 别名？", default=True):
            print("跳过 Git 别名配置")
            return

        print("\n将要配置以下别名：")
        for alias, cmd in self.git_aliases.items():
            print(f"  git {alias:<12} -> {cmd}")

        if not self.confirm("确认要配置这些别名吗？", default=True):
            print("跳过 Git 别名配置")
            return

        print("\n正在配置别名...")
        for alias, cmd in self.git_aliases.items():
            success, _, stderr = self.run_cmd(["git", "config", "--global", f"alias.{alias}", cmd])
            if success:
                print(f"  成功: git {alias}")
                self.config_summary["aliases"].append(alias)
            else:
                print(f"  失败: git {alias} -> {stderr.strip()}")

        print("\nGit 别名配置完成")

    def config_global_settings(self):
        """配置可扩展的 Git 全局选项。"""
        self.print_header("配置 Git 全局选项")

        if not self.confirm("是否要配置 Git 全局选项？", default=True):
            print("跳过 Git 全局选项配置")
            return

        print("\n将要配置以下 Git 全局选项：")
        for item in self.git_global_configs:
            print(f"  {item['key']:<24} = {item['value']}  # {item['description']}")

        if not self.confirm("确认要配置这些 Git 全局选项吗？", default=True):
            print("跳过 Git 全局选项配置")
            return

        print("\n正在配置 Git 全局选项...")
        for item in self.git_global_configs:
            success, _, stderr = self.run_cmd(
                ["git", "config", "--global", item["key"], item["value"]]
            )
            if success:
                print(f"  成功: {item['key']} = {item['value']}")
                self.config_summary["global_configs"].append(item["key"])
            else:
                print(f"  失败: {item['key']} -> {stderr.strip()}")

        print("\nGit 全局选项配置完成")

    def config_user_info(self):
        """配置用户名和邮箱。"""
        self.print_header("配置 Git 用户名和邮箱")

        if not self.confirm("是否要配置用户名和邮箱？", default=True):
            print("跳过用户信息配置")
            return

        _, current_name, _ = self.run_cmd(["git", "config", "--global", "user.name"])
        _, current_email, _ = self.run_cmd(["git", "config", "--global", "user.email"])
        current_name = current_name.strip()
        current_email = current_email.strip()

        if current_name:
            print(f"当前用户名: {current_name}")
        if current_email:
            print(f"当前邮箱: {current_email}")

        while True:
            username = self.prompt_text("请输入 Git 用户名", current_name)
            if username:
                break
            print("用户名不能为空")

        while True:
            email = self.prompt_text("请输入 Git 邮箱", current_email)
            if email:
                break
            print("邮箱不能为空")

        print("\n正在配置用户信息...")
        success_name, _, stderr_name = self.run_cmd(["git", "config", "--global", "user.name", username])
        success_email, _, stderr_email = self.run_cmd(["git", "config", "--global", "user.email", email])

        if success_name and success_email:
            print("用户名和邮箱配置成功")
            print(f"  用户名: {username}")
            print(f"  邮箱: {email}")
            self.config_summary["user_name"] = username
            self.config_summary["user_email"] = email
        else:
            if not success_name:
                print(f"配置用户名失败: {stderr_name.strip()}")
            if not success_email:
                print(f"配置邮箱失败: {stderr_email.strip()}")

    def read_public_key(self, ssh_pub_path):
        """读取公钥内容。"""
        return ssh_pub_path.read_text(encoding="utf-8").strip()

    def get_ssh_key_paths(self):
        """返回默认 SSH 私钥和公钥路径。"""
        ssh_dir = Path.home() / ".ssh"
        return ssh_dir, ssh_dir / "id_rsa", ssh_dir / "id_rsa.pub"

    def build_ssh_key_title(self):
        """生成 SSH key 默认标题。"""
        host = platform.node() or os.environ.get("COMPUTERNAME") or "local-machine"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{host}-{timestamp}"

    def api_request(self, url, method="GET", headers=None, payload=None):
        """调用 HTTP API。"""
        headers = headers or {}
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
                if not body:
                    return True, None, ""
                try:
                    return True, json.loads(body), ""
                except json.JSONDecodeError:
                    return True, body, ""
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            return False, None, f"HTTP {exc.code}: {error_body}"
        except Exception as exc:
            return False, None, str(exc)

    def record_upload_summary(self, provider, status, title, message):
        self.config_summary["ssh_uploads"].append(
            {
                "provider": provider,
                "status": status,
                "title": title,
                "message": message,
            }
        )

    def upload_key_to_github(self, public_key, title):
        """上传 SSH 公钥到 GitHub。"""
        token = self.env_config.get("GITHUB_TOKEN")
        github_settings_url = "https://github.com/settings/keys"
        if not token:
            message = "未检测到 GITHUB_TOKEN，跳过 GitHub 上传"
            print(message)
            self.record_upload_summary("GitHub", "skipped", title, message)
            return

        if self.dry_run:
            message = "预览模式：将调用 GitHub API 上传 SSH 公钥"
            print(message)
            self.record_upload_summary("GitHub", "dry-run", title, message)
            return

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "git-config-tool",
        }

        success, keys, error = self.api_request("https://api.github.com/user/keys", headers=headers)
        if not success:
            if "HTTP 403:" in error or "HTTP 404:" in error:
                print(f"GitHub 密钥列表查询失败，将继续尝试直接创建: {error}")
                print("这通常表示当前 Token 没有读取 SSH Keys 的权限。")
            else:
                print(f"GitHub 密钥列表查询失败: {error}")
                self.record_upload_summary("GitHub", "failed", title, error)
                return

        if success:
            for item in keys or []:
                if item.get("key", "").strip() == public_key:
                    message = f"GitHub 已存在相同公钥，标题: {item.get('title', 'unknown')}"
                    print(message)
                    self.record_upload_summary("GitHub", "exists", title, message)
                    return

        payload = {"title": title, "key": public_key}
        success, response, error = self.api_request(
            "https://api.github.com/user/keys",
            method="POST",
            headers=headers,
            payload=payload,
        )

        if success:
            key_id = response.get("id") if isinstance(response, dict) else "unknown"
            message = f"GitHub 上传成功，Key ID: {key_id}"
            print(message)
            self.record_upload_summary("GitHub", "success", title, message)
        else:
            if "HTTP 422:" in error and ("already in use" in error.lower() or "key is already in use" in error.lower()):
                message = "GitHub 已存在相同公钥，创建接口返回重复。"
                print(message)
                self.record_upload_summary("GitHub", "exists", title, message)
                return

            if "HTTP 403:" in error or "HTTP 404:" in error:
                permission_hint = (
                    "GitHub 上传失败。请检查 GITHUB_TOKEN 是否具备以下权限之一："
                    "classic PAT 需要 write:public_key；fine-grained PAT 需要 Git SSH keys (write)。"
                    f"你也可以手动打开 {github_settings_url} 添加。"
                )
                print(permission_hint)
                print(f"接口返回: {error}")
                self.record_upload_summary("GitHub", "failed", title, f"{permission_hint} {error}")
                return

            print(f"GitHub 上传失败: {error}")
            self.record_upload_summary("GitHub", "failed", title, error)

    def upload_key_to_gitlab(self, public_key, title):
        """上传 SSH 公钥到 GitLab。"""
        token = self.env_config.get("GITLAB_TOKEN")
        gitlab_url = self.env_config.get("GITLAB_URL") or self.default_gitlab_url

        if not token:
            message = "未检测到 GITLAB_TOKEN，跳过 GitLab 上传"
            print(message)
            self.record_upload_summary("GitLab", "skipped", title, message)
            return
        if not gitlab_url:
            message = "未配置 GITLAB_URL，跳过 GitLab 上传"
            print(message)
            self.record_upload_summary("GitLab", "skipped", title, message)
            return

        if self.dry_run:
            message = f"预览模式：将调用 {gitlab_url} 的 GitLab API 上传 SSH 公钥"
            print(message)
            self.record_upload_summary("GitLab", "dry-run", title, message)
            return

        headers = {
            "PRIVATE-TOKEN": token,
            "User-Agent": "git-config-tool",
        }
        api_url = f"{gitlab_url}/api/v4/user/keys"

        success, keys, error = self.api_request(api_url, headers=headers)
        if not success:
            print(f"GitLab 密钥列表查询失败: {error}")
            self.record_upload_summary("GitLab", "failed", title, error)
            return

        for item in keys or []:
            if item.get("key", "").strip() == public_key:
                message = f"GitLab 已存在相同公钥，标题: {item.get('title', 'unknown')}"
                print(message)
                self.record_upload_summary("GitLab", "exists", title, message)
                return

        payload = {"title": title, "key": public_key}
        success, response, error = self.api_request(
            api_url,
            method="POST",
            headers=headers,
            payload=payload,
        )

        if success:
            key_id = response.get("id") if isinstance(response, dict) else "unknown"
            message = f"GitLab 上传成功，Key ID: {key_id}"
            print(message)
            self.record_upload_summary("GitLab", "success", title, message)
        else:
            print(f"GitLab 上传失败: {error}")
            self.record_upload_summary("GitLab", "failed", title, error)

    def upload_ssh_key(self, public_key):
        """读取现有公钥并执行上传配置。"""
        gitlab_url = self.env_config.get("GITLAB_URL") or self.default_gitlab_url
        github_ready = bool(self.env_config.get("GITHUB_TOKEN"))
        gitlab_ready = bool(self.env_config.get("GITLAB_TOKEN") and gitlab_url)
        github_settings_url = "https://github.com/settings/keys"
        gitlab_settings_url = f"{gitlab_url.rstrip('/')}/-/user_settings/ssh_keys" if gitlab_url else "未配置 GITLAB_URL"

        if not github_ready and not gitlab_ready:
            print("\n未检测到 GitHub/GitLab Token，跳过自动上传。")
            print(f"如果需要自动上传，请在 {self.env_path} 中配置对应 Token。")
            return

        if not self.confirm("是否继续将 SSH 公钥自动上传到 GitHub/GitLab？", default=True):
            print("跳过 SSH 公钥自动上传")
            return

        print("\n可配置的平台：")
        if github_ready:
            print(f"  [1] GitHub  管理页: {github_settings_url}")
        else:
            print("  [1] GitHub  未配置 GITHUB_TOKEN")

        if gitlab_ready:
            print(f"  [2] GitLab  管理页: {gitlab_settings_url}")
        else:
            print("  [2] GitLab  未配置 GITLAB_TOKEN")

        print("  [3] 同时配置 GitHub 和 GitLab")
        platform_choice = self.prompt_choice("请选择要配置的平台", {"1", "2", "3"}, "3")

        title = self.prompt_text("请输入 SSH Key 标题", self.build_ssh_key_title())

        if platform_choice in {"1", "3"}:
            if github_ready:
                self.upload_key_to_github(public_key, title)
            else:
                self.record_upload_summary("GitHub", "skipped", title, "未配置 GITHUB_TOKEN")

        if platform_choice in {"2", "3"}:
            if gitlab_ready:
                self.upload_key_to_gitlab(public_key, title)
            else:
                self.record_upload_summary("GitLab", "skipped", title, "未配置 GITLAB_TOKEN")

    def generate_ssh_key(self):
        """生成 SSH 密钥。"""
        self.print_header("生成 SSH 密钥")

        if not self.confirm("是否要生成 SSH 密钥？", default=True):
            print("跳过 SSH 密钥生成")
            return

        ssh_dir, ssh_key_path, ssh_pub_path = self.get_ssh_key_paths()

        if ssh_pub_path.exists():
            print(f"\n检测到已有 SSH 公钥: {ssh_pub_path}")
            if not self.confirm("是否覆盖现有密钥？", default=False):
                public_key = self.read_public_key(ssh_pub_path)
                print("\n现有公钥内容：")
                print(public_key)
                self.config_summary["ssh_key"] = str(ssh_pub_path)
                return

        _, current_email, _ = self.run_cmd(["git", "config", "--global", "user.email"])
        current_email = current_email.strip()

        while True:
            email = self.prompt_text("请输入用于 SSH 密钥的邮箱", current_email)
            if email:
                break
            print("邮箱不能为空")

        if not self.dry_run:
            ssh_dir.mkdir(mode=0o700, exist_ok=True)

        print("\n正在生成 SSH 密钥...")
        cmd = [
            "ssh-keygen",
            "-t",
            "rsa",
            "-b",
            "4096",
            "-C",
            email,
            "-f",
            str(ssh_key_path),
            "-N",
            "",
        ]
        success, _, stderr = self.run_cmd(cmd)

        if success:
            print("SSH 密钥生成成功")
            print(f"公钥已保存到: {ssh_pub_path}")

            if ssh_pub_path.exists():
                public_key = self.read_public_key(ssh_pub_path)
                print("\n公钥内容：")
                print(public_key)
                self.config_summary["ssh_key"] = str(ssh_pub_path)
            else:
                print("警告：未找到生成后的公钥文件")
        elif self.dry_run:
            print("预览模式：SSH 密钥生成命令已准备完成")
            self.config_summary["ssh_key"] = str(ssh_pub_path)
        else:
            print(f"SSH 密钥生成失败: {stderr.strip()}")

    def config_ssh_key(self):
        """配置 SSH 公钥上传。"""
        self.print_header("配置 SSH 公钥")

        _, _, ssh_pub_path = self.get_ssh_key_paths()

        if not ssh_pub_path.exists():
            print("未找到 SSH 公钥，请先执行“生成 SSH 密钥”。")
            return

        public_key = self.read_public_key(ssh_pub_path)
        self.config_summary["ssh_key"] = str(ssh_pub_path)

        print(f"检测到 SSH 公钥: {ssh_pub_path}")
        print("\n当前公钥内容：")
        print(public_key)

        if not self.confirm("是否要配置并上传这个 SSH 公钥？", default=True):
            print("跳过 SSH 公钥配置")
            return

        self.upload_ssh_key(public_key)

    def show_summary(self):
        """显示配置汇总。"""
        self.print_header("配置完成")
        print("\n配置信息汇总：")
        print("-" * 50)

        if self.config_summary["aliases"]:
            print(f"Git 别名 ({len(self.config_summary['aliases'])} 个):")
            for alias in self.config_summary["aliases"]:
                print(f"  - git {alias}")
        else:
            print("Git 别名: 本次未配置")

        print("\nGit 全局选项:")
        if self.config_summary["global_configs"]:
            for key in self.config_summary["global_configs"]:
                print(f"  - {key}")
        else:
            print("  本次未配置")

        print("\n用户信息:")
        if self.config_summary["user_name"]:
            print(f"  用户名: {self.config_summary['user_name']}")
        else:
            _, current_name, _ = self.run_cmd(["git", "config", "--global", "user.name"])
            print(f"  用户名: {current_name.strip() or '未配置'}")

        if self.config_summary["user_email"]:
            print(f"  邮箱: {self.config_summary['user_email']}")
        else:
            _, current_email, _ = self.run_cmd(["git", "config", "--global", "user.email"])
            print(f"  邮箱: {current_email.strip() or '未配置'}")

        print("\nSSH 密钥:")
        if self.config_summary["ssh_key"]:
            print(f"  公钥路径: {self.config_summary['ssh_key']}")
        else:
            ssh_pub_path = Path.home() / ".ssh" / "id_rsa.pub"
            if ssh_pub_path.exists():
                print(f"  公钥路径: {ssh_pub_path}")
            else:
                print("  未配置")

        print("\nSSH 公钥上传:")
        if self.config_summary["ssh_uploads"]:
            for item in self.config_summary["ssh_uploads"]:
                print(f"  {item['provider']}: {item['status']} - {item['message']}")
        else:
            print("  本次未执行自动上传")

        print("-" * 50)
        print("\n所有配置流程已结束。")
        if self.dry_run:
            print("当前为预览模式，以上配置未实际写入。")

    def show_menu(self):
        """显示主菜单。"""
        self.print_header("Git 环境快速配置工具 v3.1")
        print("\n请选择要进行的配置操作：")
        print(" [1] 配置 Git 常用别名 (Alias)")
        print(" [2] 配置 Git 全局选项")
        print(" [3] 配置 Git 用户名和邮箱")
        print(" [4] 生成 SSH 密钥")
        print(" [5] 配置 SSH 公钥上传")
        print(" [6] 全部配置")
        print(" [7] 查看当前配置")
        print(" [8] 退出")
        print()

    def show_current_config(self):
        """显示当前 Git 配置。"""
        self.print_header("当前 Git 配置")
        print()

        print("用户信息:")
        _, name, _ = self.run_cmd(["git", "config", "--global", "user.name"])
        _, email, _ = self.run_cmd(["git", "config", "--global", "user.email"])
        print(f"  用户名: {name.strip() or '未配置'}")
        print(f"  邮箱: {email.strip() or '未配置'}")

        print("\nGit 别名:")
        _, aliases, _ = self.run_cmd(["git", "config", "--global", "--get-regexp", "alias"])
        if aliases.strip():
            for line in aliases.strip().splitlines():
                alias_part, cmd = line.split(" ", 1)
                alias_name = alias_part.replace("alias.", "")
                print(f"  git {alias_name:<12} -> {cmd}")
        else:
            print("  未配置任何别名")

        print("\nGit 全局选项:")
        for item in self.git_global_configs:
            _, value, _ = self.run_cmd(["git", "config", "--global", item["key"]])
            print(f"  {item['key']:<24} = {value.strip() or '未配置'}")

        print("\nSSH 密钥:")
        ssh_pub_path = Path.home() / ".ssh" / "id_rsa.pub"
        if ssh_pub_path.exists():
            print(f"  公钥存在: {ssh_pub_path}")
            public_key = self.read_public_key(ssh_pub_path)
            preview = public_key[:80] + "..." if len(public_key) > 80 else public_key
            print(f"  公钥内容: {preview}")
        else:
            print("  未找到 SSH 公钥")

        print("\n自动上传配置:")
        print(f"  GitHub Token: {'已检测到' if self.env_config.get('GITHUB_TOKEN') else '未配置'}")
        print(f"  GitLab Token: {'已检测到' if self.env_config.get('GITLAB_TOKEN') else '未配置'}")
        print("  GitHub SSH 设置页: https://github.com/settings/keys")
        print(f"  GitLab SSH 设置页: {self.default_gitlab_url}/-/user_settings/ssh_keys")

        print()

    def run(self):
        """主运行函数。"""
        self.dry_run = "--dry-run" in sys.argv

        if self.dry_run:
            print("当前运行在预览模式 (DRY RUN)，所有操作都不会实际修改配置。")
            print()

        if not self.check_git_installed():
            return

        while True:
            self.show_menu()
            choice = input("请输入选项 (1-8): ").strip()

            if choice == "1":
                self.config_aliases()
            elif choice == "2":
                self.config_global_settings()
            elif choice == "3":
                self.config_user_info()
            elif choice == "4":
                self.generate_ssh_key()
            elif choice == "5":
                self.config_ssh_key()
            elif choice == "6":
                self.config_aliases()
                self.config_global_settings()
                self.config_user_info()
                self.generate_ssh_key()
                self.config_ssh_key()
                self.show_summary()
                break
            elif choice == "7":
                self.show_current_config()
            elif choice == "8":
                print("\n已退出 Git 环境快速配置工具。")
                break
            else:
                print("\n无效选项，请重新输入。")

            if choice in {"1", "2", "3", "4", "5"}:
                if self.confirm("是否继续其他配置？", default=True):
                    continue
                self.show_summary()
                break

            input("\n按回车键继续...")


if __name__ == "__main__":
    try:
        GitConfigTool().run()
    except KeyboardInterrupt:
        print("\n\n程序已被中断，退出。")
        sys.exit(0)
