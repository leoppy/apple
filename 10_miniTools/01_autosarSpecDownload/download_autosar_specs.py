#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOSAR规范文件深度下载工具
支持递归遍历HTTP目录并保持原始目录结构下载所有文件
"""

import os
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path
import time
from typing import Set


class AutosarDownloader:
    def __init__(self, base_url: str, output_dir: str = None):
        # 确保base_url以斜杠结尾
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'

        # 如果没有指定输出目录，使用脚本所在目录的tempFile
        if output_dir is None:
            script_dir = Path(__file__).parent
            self.output_dir = script_dir / "tempFile"
        else:
            self.output_dir = Path(output_dir)

        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # 统计信息
        self.total_files = 0
        self.downloaded_files = 0
        self.skipped_files = 0
        self.failed_files = 0

    def is_valid_url(self, url: str) -> bool:
        """检查URL是否在基础URL路径下"""
        return url.startswith(self.base_url)

    def get_relative_path(self, url: str) -> str:
        """获取相对于基础URL的路径"""
        if url.startswith(self.base_url):
            relative = url[len(self.base_url):].lstrip('/')
        else:
            parsed_url = urlparse(url)
            relative = parsed_url.path.lstrip('/')

        return unquote(relative)

    def is_directory_listing(self, soup: BeautifulSoup) -> bool:
        """判断是否为目录列表页面"""
        # 常见的目录列表特征
        title = soup.find('title')
        if title and 'Index of' in title.text:
            return True

        # 检查是否有大量链接
        links = soup.find_all('a', href=True)
        return len(links) > 2

    def download_file(self, url: str, local_path: Path):
        """下载单个文件"""
        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"[{self.downloaded_files + 1}] 下载: {local_path.name}")

            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(local_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

            print(f"  [完成] {total_size / 1024 / 1024:.2f} MB\n")
            self.downloaded_files += 1
            return True

        except Exception as e:
            print(f"  [失败]: {e}\n")
            self.failed_files += 1
            return False

    def parse_directory(self, url: str):
        """解析目录页面并递归下载"""
        if url in self.visited_urls:
            return

        self.visited_urls.add(url)

        try:
            print(f"\n扫描目录: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            links = soup.find_all('a', href=True)

            for link in links:
                href = link.get('href')

                # 跳过父目录和当前目录
                if href in ['../', '../', './', '.']:
                    continue

                # 构建完整URL
                full_url = urljoin(url, href)

                # 只处理在基础URL下的链接
                if not self.is_valid_url(full_url):
                    continue

                # 判断是目录还是文件
                if href.endswith('/'):
                    # 这是一个目录，递归处理
                    self.parse_directory(full_url)
                else:
                    # 这是一个文件，下载它
                    relative_path = self.get_relative_path(full_url)
                    local_path = self.output_dir / relative_path

                    # 如果文件已存在且大小相同，跳过
                    if local_path.exists():
                        try:
                            head = self.session.head(full_url, timeout=10)
                            remote_size = int(head.headers.get('content-length', 0))
                            local_size = local_path.stat().st_size

                            if remote_size == local_size:
                                print(f"跳过(已存在): {local_path.name}")
                                self.skipped_files += 1
                                continue
                        except:
                            pass

                    self.download_file(full_url, local_path)
                    time.sleep(0.1)  # 减少等待时间，加快下载速度

        except Exception as e:
            print(f"扫描目录失败 {url}: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """开始下载"""
        print("=" * 70)
        print("AUTOSAR规范文件下载工具")
        print("=" * 70)
        print(f"源地址: {self.base_url}")
        print(f"保存到: {self.output_dir.absolute()}")
        print("=" * 70)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        self.parse_directory(self.base_url)
        elapsed = time.time() - start_time

        print("\n" + "=" * 70)
        print("下载完成!")
        print("=" * 70)
        print(f"总耗时: {elapsed:.1f}秒")
        print(f"已下载: {self.downloaded_files} 个文件")
        print(f"已跳过: {self.skipped_files} 个文件")
        print(f"失败: {self.failed_files} 个文件")
        print(f"文件保存在: {self.output_dir.absolute()}")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='AUTOSAR规范文件深度下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python download_autosar_specs.py
  python download_autosar_specs.py http://example.com/files/
  python download_autosar_specs.py http://example.com/files/ -o ./downloads
  python download_autosar_specs.py -u http://example.com/files/ -o ./downloads
        """
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='要下载的HTTP目录地址 (可选，也可以用-u参数指定)'
    )

    parser.add_argument(
        '-u', '--url',
        dest='url_param',
        help='要下载的HTTP目录地址 (与位置参数二选一)'
    )

    parser.add_argument(
        '-o', '--output',
        default=None,
        help='输出目录 (默认: 脚本所在目录的tempFile文件夹)'
    )

    args = parser.parse_args()

    # 优先使用-u参数，其次使用位置参数
    url = args.url_param or args.url

    if not url:
        print("请输入要下载的HTTP目录地址:")
        url = input("> ").strip()

        if not url:
            print("错误: 未提供URL")
            sys.exit(1)

    # 验证URL
    if not url.startswith(('http://', 'https://')):
        print("错误: URL必须以 http:// 或 https:// 开头")
        sys.exit(1)

    # 处理输出目录
    output_dir = args.output
    if not output_dir:
        # 如果没有通过参数指定，询问用户
        script_dir = Path(__file__).parent
        default_dir = script_dir / "tempFile"
        print(f"\n请输入输出目录 (直接回车使用默认: {default_dir}):")
        user_input = input("> ").strip()

        if user_input:
            output_dir = user_input
        # 如果用户直接回车，output_dir保持为None，会使用默认值

    # 创建下载器并开始
    downloader = AutosarDownloader(url, output_dir)

    try:
        downloader.start()
    except KeyboardInterrupt:
        print("\n\n用户中断下载")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
