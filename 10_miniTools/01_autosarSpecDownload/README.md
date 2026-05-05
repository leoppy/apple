# HTTP 目录递归下载工具

递归扫描 HTTP 目录列表页面，并保持目录结构下载文件。

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 使用

```powershell
python download_autosar_specs.py http://example.com/files/ -o ./downloads
```

如果不传 `-o`，默认保存到脚本目录下的 `tempFile/`。该目录已加入 `.gitignore`。

## 注意

- 只下载给定 URL 路径下的文件。
- 不要提交下载产物。
- 公司内部镜像地址由使用者自行填写。
