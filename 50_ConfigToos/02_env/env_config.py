#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量配置工具
支持 Windows/macOS/Linux，功能：
1. 从 .env 文件读取环境变量配置
2. 支持单个选择、批量选择配置
3. 自动检测当前系统环境变量
4. 支持预览模式和实际配置
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


class EnvConfigTool:
    def __init__(self):
        self.dry_run = False
        self.repo_root = Path(__file__).resolve().parents[2]
        self.env_example_path = self.repo_root / ".env.example"
        self.env_path = self.repo_root / ".env"
        self.system = platform.system()
        self.env_vars = {}
        self.config_summary = []

    def load_env_file(self, file_path):
        """从 .env 文件读取环境变量配置。"""
        env_vars = {}
        if not file_path.exists():
            return env_vars

        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                # 保留注释作为描述
                continue
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # 实时从系统环境变量读取当前值
            current_value = self.get_system_env_value(key)
            env_vars[key] = {
                "example_value": value,
                "current_value": current_value,
                "is_set": bool(current_value),
            }

        return env_vars

    def print_header(self, title):
        """打印标题。"""
        print("\n" + "=" * 60)
        print(f"{title:^60}")
        print("=" * 60)

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

    def prompt_text(self, prompt, default="", allow_empty=False):
        """读取文本输入，支持默认值。"""
        suffix = f" (默认: {default})" if default else ""
        if allow_empty:
            suffix += " [可留空]"

        while True:
            response = input(f"{prompt}{suffix}: ").strip()
            result = response or default
            if result or allow_empty:
                return result
            print("输入不能为空，请重新输入")

    def get_system_env_value(self, key):
        """获取系统环境变量的当前值（持久化配置）。"""
        if self.system == "Windows":
            try:
                # Windows: 从注册表读取用户环境变量（持久化的值）
                result = subprocess.run(
                    ["powershell", "-Command", f"[Environment]::GetEnvironmentVariable('{key}', 'User')"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",  # 忽略编码错误
                )
                value = result.stdout.strip()
                # 如果注册表中没有，尝试从当前进程环境变量读取
                if not value:
                    value = os.environ.get(key, "")
                return value
            except Exception:
                return os.environ.get(key, "")
        else:
            # macOS/Linux: 从配置文件解析
            config_file = "~/.zshrc" if self.system == "Darwin" else "~/.bashrc"
            config_path = Path(config_file).expanduser()

            if not config_path.exists():
                return os.environ.get(key, "")

            # 从配置文件中查找 export KEY=VALUE
            try:
                content = config_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith(f"export {key}="):
                        # 提取值（去掉引号）
                        value = line.split("=", 1)[1].strip().strip('"').strip("'")
                        return value
            except Exception:
                pass

            # 如果配置文件中没有，从当前进程环境变量读取
            return os.environ.get(key, "")

    def set_system_env(self, key, value):
        """设置系统环境变量（持久化）。"""
        if self.dry_run:
            print(f"[DRY RUN] 将设置环境变量: {key}={value}")
            return True

        try:
            if self.system == "Windows":
                # Windows: 使用 setx 设置用户级环境变量
                # 使用 gbk 编码处理中文输出
                result = subprocess.run(
                    ["setx", key, value],
                    capture_output=True,
                    text=True,
                    encoding="gbk",  # Windows 控制台使用 gbk 编码
                    errors="ignore",  # 忽略编码错误
                )
                return result.returncode == 0
            elif self.system == "Darwin":
                # macOS: 写入 ~/.zshrc 或 ~/.bash_profile
                return self._set_unix_env(key, value, "~/.zshrc")
            else:
                # Linux: 写入 ~/.bashrc
                return self._set_unix_env(key, value, "~/.bashrc")
        except Exception as exc:
            print(f"设置环境变量失败: {exc}")
            return False

    def _set_unix_env(self, key, value, config_file):
        """在 Unix 系统上设置环境变量（写入配置文件）。"""
        config_path = Path(config_file).expanduser()
        export_line = f'export {key}="{value}"\n'

        if not config_path.exists():
            config_path.touch()

        content = config_path.read_text(encoding="utf-8")

        # 检查是否已存在该环境变量的配置
        lines = content.splitlines(keepends=True)
        updated = False
        new_lines = []

        for line in lines:
            if line.strip().startswith(f"export {key}="):
                new_lines.append(export_line)
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(export_line)

        config_path.write_text("".join(new_lines), encoding="utf-8")
        print(f"已将配置写入: {config_path}")
        return True

    def show_env_vars(self):
        """显示所有环境变量及其状态。"""
        if not self.env_vars:
            print("未找到环境变量配置")
            return

        print("\n当前环境变量状态：")
        print("-" * 60)
        print(f"{'序号':<4} {'变量名':<25} {'状态':<8} {'当前值'}")
        print("-" * 60)

        for idx, (key, info) in enumerate(self.env_vars.items(), 1):
            status = "✓ 已设置" if info["is_set"] else "✗ 未设置"
            current = info["current_value"][:20] + "..." if len(info["current_value"]) > 20 else info["current_value"]
            if not current:
                current = "(空)"
            print(f"{idx:<4} {key:<25} {status:<8} {current}")

        print("-" * 60)

    def config_single_env(self, key, info):
        """配置单个环境变量。"""
        print(f"\n配置环境变量: {key}")
        print(f"当前值: {info['current_value'] or '(未设置)'}")

        if info["example_value"]:
            print(f"示例值: {info['example_value']}")

        new_value = self.prompt_text(
            "请输入新值",
            default=info["current_value"] or info["example_value"],
            allow_empty=True
        )

        if not new_value:
            print(f"跳过 {key} 的配置")
            return False

        if new_value == info["current_value"]:
            print(f"{key} 的值未变化，跳过")
            return False

        success = self.set_system_env(key, new_value)
        if success:
            print(f"✓ {key} 配置成功")
            self.config_summary.append({
                "key": key,
                "old_value": info["current_value"],
                "new_value": new_value,
                "status": "success"
            })
            return True
        else:
            print(f"✗ {key} 配置失败")
            self.config_summary.append({
                "key": key,
                "old_value": info["current_value"],
                "new_value": new_value,
                "status": "failed"
            })
            return False

    def config_selected_envs(self):
        """配置选中的环境变量。"""
        self.print_header("选择要配置的环境变量")
        self.show_env_vars()

        print("\n输入要配置的序号，多个序号用空格或逗号分隔")
        print("输入 'all' 或 'a' 配置全部")
        print("输入 'unset' 或 'u' 只配置未设置的")

        selection = input("\n请输入: ").strip().lower()

        if not selection:
            print("未选择任何环境变量")
            return

        keys_list = list(self.env_vars.keys())
        selected_keys = []

        if selection in {"all", "a"}:
            selected_keys = keys_list
        elif selection in {"unset", "u"}:
            selected_keys = [k for k in keys_list if not self.env_vars[k]["is_set"]]
        else:
            # 解析序号
            indices = []
            for part in selection.replace(",", " ").split():
                try:
                    idx = int(part)
                    if 1 <= idx <= len(keys_list):
                        indices.append(idx)
                    else:
                        print(f"警告: 序号 {idx} 超出范围，已忽略")
                except ValueError:
                    print(f"警告: 无效输入 '{part}'，已忽略")

            selected_keys = [keys_list[i - 1] for i in indices]

        if not selected_keys:
            print("未选择任何有效的环境变量")
            return

        print(f"\n将配置以下 {len(selected_keys)} 个环境变量:")
        for key in selected_keys:
            status = "✓" if self.env_vars[key]["is_set"] else "✗"
            print(f"  {status} {key}")

        if not self.confirm("确认开始配置？", default=True):
            print("已取消配置")
            return

        print("\n开始配置...")
        for key in selected_keys:
            self.config_single_env(key, self.env_vars[key])

    def config_all_envs(self):
        """配置所有环境变量。"""
        self.print_header("配置所有环境变量")
        self.show_env_vars()

        if not self.confirm("确认要配置所有环境变量？", default=True):
            print("已取消配置")
            return

        print("\n开始配置...")
        for key, info in self.env_vars.items():
            self.config_single_env(key, info)

    def show_current_envs(self):
        """显示当前系统环境变量。"""
        self.print_header("当前系统环境变量")
        self.show_env_vars()

        print("\n说明:")
        if self.system == "Windows":
            print("- Windows 系统使用 setx 命令设置用户级环境变量")
            print("- 配置后需要重启终端或应用程序才能生效")
        elif self.system == "Darwin":
            print("- macOS 系统将配置写入 ~/.zshrc")
            print("- 配置后需要执行 'source ~/.zshrc' 或重启终端")
        else:
            print("- Linux 系统将配置写入 ~/.bashrc")
            print("- 配置后需要执行 'source ~/.bashrc' 或重启终端")

    def show_summary(self):
        """显示配置汇总。"""
        self.print_header("配置完成")

        if not self.config_summary:
            print("\n本次未进行任何配置")
            return

        print("\n配置信息汇总：")
        print("-" * 60)

        success_count = sum(1 for item in self.config_summary if item["status"] == "success")
        failed_count = len(self.config_summary) - success_count

        print(f"总计: {len(self.config_summary)} 个环境变量")
        print(f"成功: {success_count} 个")
        print(f"失败: {failed_count} 个")
        print()

        for item in self.config_summary:
            status_icon = "✓" if item["status"] == "success" else "✗"
            print(f"{status_icon} {item['key']}")
            if item["old_value"]:
                print(f"    旧值: {item['old_value']}")
            print(f"    新值: {item['new_value']}")

        print("-" * 60)

        if self.dry_run:
            print("\n当前为预览模式，以上配置未实际写入。")
        else:
            print("\n配置已保存到系统环境变量。")
            if self.system == "Windows":
                print("请重启终端或应用程序使配置生效。")
            else:
                shell_config = "~/.zshrc" if self.system == "Darwin" else "~/.bashrc"
                print(f"请执行 'source {shell_config}' 或重启终端使配置生效。")

    def show_menu(self):
        """显示主菜单。"""
        self.print_header("环境变量配置工具 v1.0")
        print("\n请选择要进行的操作：")
        print(" [1] 查看当前环境变量状态")
        print(" [2] 选择性配置环境变量")
        print(" [3] 配置所有环境变量")
        print(" [4] 配置未设置的环境变量")
        print(" [5] 退出")
        print()

    def run(self):
        """主运行函数。"""
        self.dry_run = "--dry-run" in sys.argv

        if self.dry_run:
            print("当前运行在预览模式 (DRY RUN)，所有操作都不会实际修改配置。")
            print()

        # 严格模式：要求 .env 文件必须存在
        if not self.env_path.exists():
            print(f"错误: 未找到配置文件 {self.env_path}")
            print()
            if self.env_example_path.exists():
                print(f"提示: 检测到模板文件 {self.env_example_path}")
                print(f"请先复制并配置:")
                print(f"  cp {self.env_example_path} {self.env_path}")
                print(f"  # 然后编辑 {self.env_path} 填写你的配置")
            else:
                print(f"提示: 也未找到模板文件 {self.env_example_path}")
                print(f"请创建 .env 文件，格式示例:")
                print(f"  GITHUB_TOKEN=your_token_here")
                print(f"  JENKINS_URL=https://jenkins.example.com")
            return

        print(f"从配置文件加载: {self.env_path}")
        self.env_vars = self.load_env_file(self.env_path)

        if not self.env_vars:
            print("配置文件中未找到任何环境变量")
            return

        while True:
            self.show_menu()
            choice = input("请输入选项 (1-5): ").strip()

            if choice == "1":
                self.show_current_envs()
            elif choice == "2":
                self.config_selected_envs()
            elif choice == "3":
                self.config_all_envs()
                self.show_summary()
                break
            elif choice == "4":
                unset_keys = [k for k in self.env_vars.keys() if not self.env_vars[k]["is_set"]]
                if not unset_keys:
                    print("\n所有环境变量均已设置")
                else:
                    print(f"\n将配置以下 {len(unset_keys)} 个未设置的环境变量:")
                    for key in unset_keys:
                        print(f"  ✗ {key}")
                    if self.confirm("确认开始配置？", default=True):
                        for key in unset_keys:
                            self.config_single_env(key, self.env_vars[key])
                        self.show_summary()
                        break
            elif choice == "5":
                print("\n已退出环境变量配置工具。")
                break
            else:
                print("\n无效选项，请重新输入。")

            if choice in {"2", "4"}:
                if self.confirm("是否继续其他配置？", default=True):
                    continue
                self.show_summary()
                break

            input("\n按回车键继续...")


if __name__ == "__main__":
    try:
        EnvConfigTool().run()
    except KeyboardInterrupt:
        print("\n\n程序已被中断，退出。")
        sys.exit(0)
