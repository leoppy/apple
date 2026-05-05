from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ENV_CANDIDATES = (
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parents[1] / ".env",
)
BACKUP_DIR = Path(__file__).resolve().parent / "backups"
DEFAULT_GUARD_PARAMS = ("system_prompt",)


def load_env_file() -> None:
    path = next((item for item in ENV_CANDIDATES if item.exists()), None)
    if path is None:
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"缺少环境变量: {name}")
    return value


def build_job_path(job_name: str) -> str:
    parts = [quote(part, safe="") for part in job_name.split("/") if part.strip()]
    if not parts:
        raise ValueError("job 名称不能为空")
    return "/".join(f"job/{part}" for part in parts)


def build_auth_header(username: str, token: str) -> dict[str, str]:
    auth = b64encode(f"{username}:{token}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {auth}"}


def request_text(
    url: str,
    headers: dict[str, str],
    *,
    method: str = "GET",
    data: bytes | None = None,
) -> str:
    request = Request(url, headers=headers, method=method, data=data)
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Jenkins API 返回 HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"无法连接 Jenkins: {exc}") from exc


def fetch_config_xml(base_url: str, job_name: str, headers: dict[str, str]) -> str:
    job_path = build_job_path(job_name)
    return request_text(f"{base_url.rstrip('/')}/{job_path}/config.xml", headers)


def fetch_crumb_headers(base_url: str, headers: dict[str, str]) -> dict[str, str]:
    crumb_url = f"{base_url.rstrip('/')}/crumbIssuer/api/json"
    try:
        payload = request_text(crumb_url, headers)
    except RuntimeError as exc:
        message = str(exc)
        if "HTTP 404" in message or "HTTP 403" in message:
            return dict(headers)
        raise

    crumb_info = json.loads(payload)
    merged_headers = dict(headers)
    merged_headers[crumb_info["crumbRequestField"]] = crumb_info["crumb"]
    return merged_headers


def backup_config(job_name: str, xml_text: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    safe_job_name = job_name.replace("/", "__")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{safe_job_name}_{timestamp}.config.xml"
    backup_path.write_text(xml_text, encoding="utf-8")
    return backup_path


def parameter_definitions_node(root: ET.Element) -> ET.Element:
    params = root.find("properties/hudson.model.ParametersDefinitionProperty/parameterDefinitions")
    if params is None:
        raise ValueError("未找到 Jenkins 参数定义节点")
    return params


def list_parameter_definitions(root: ET.Element) -> list[ET.Element]:
    return list(parameter_definitions_node(root))


def serialize_parameter(param: ET.Element) -> dict[str, str]:
    return {
        "type": param.tag,
        "name": (param.findtext("name", default="") or "").strip(),
        "value": param.findtext("defaultValue", default="") or "",
        "description": param.findtext("description", default="") or "",
    }


def find_parameter_definition(root: ET.Element, parameter_name: str) -> ET.Element:
    for param in list_parameter_definitions(root):
        name = (param.findtext("name", default="") or "").strip()
        if name == parameter_name:
            return param
    raise ValueError(f"未找到参数: {parameter_name}")


def parameter_exists(root: ET.Element, parameter_name: str) -> bool:
    try:
        find_parameter_definition(root, parameter_name)
        return True
    except ValueError:
        return False


def get_or_create_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
    return child


def get_parameter_field(root: ET.Element, parameter_name: str, field_name: str) -> str:
    param = find_parameter_definition(root, parameter_name)
    return param.findtext(field_name, default="") or ""


def contains_mojibake(text: str) -> bool:
    markers = ("Ã", "â", "æ", "å", "ç", "ï", "ð", "é", "è", "ê", "¤", "½", "¿", "�")
    return any(marker in text for marker in markers)


def build_guard_parameter_names(
    current_name: str,
    new_name: str | None,
    extra_guards: list[str],
) -> list[str]:
    names = {current_name, *(name for name in DEFAULT_GUARD_PARAMS if name)}
    if new_name:
        names.add(new_name)
    names.update(extra_guards)
    return sorted(name for name in names if name)


def verify_no_mojibake(root: ET.Element, guard_parameter_names: list[str]) -> None:
    for guard_name in guard_parameter_names:
        if not parameter_exists(root, guard_name):
            continue
        for guarded_field in ("name", "defaultValue", "description"):
            value = get_parameter_field(root, guard_name, guarded_field)
            if contains_mojibake(value):
                raise RuntimeError(
                    f"保护校验失败: {guard_name}.{guarded_field} 出现疑似乱码"
                )


def verify_parameter_values(
    root: ET.Element,
    *,
    parameter_name: str,
    expected_name: str | None = None,
    expected_value: str | None = None,
    expected_description: str | None = None,
) -> None:
    param = find_parameter_definition(root, parameter_name)
    actual = serialize_parameter(param)

    if expected_name is not None and actual["name"] != expected_name:
        raise RuntimeError("字段校验失败: name 实际值与预期不一致")
    if expected_value is not None and actual["value"] != expected_value:
        raise RuntimeError("字段校验失败: value 实际值与预期不一致")
    if expected_description is not None and actual["description"] != expected_description:
        raise RuntimeError("字段校验失败: description 实际值与预期不一致")


def set_parameter_fields(
    root: ET.Element,
    *,
    current_name: str,
    new_name: str | None,
    new_value: str | None,
    new_description: str | None,
) -> dict[str, dict[str, str]]:
    if new_name is None and new_value is None and new_description is None:
        raise ValueError("至少要提供一个修改项: --new-name / --new-value / --new-description")

    param = find_parameter_definition(root, current_name)
    changes: dict[str, dict[str, str]] = {}

    if new_name is not None and new_name != current_name and parameter_exists(root, new_name):
        raise ValueError(f"目标参数名已存在: {new_name}")

    if new_name is not None:
        field = get_or_create_child(param, "name")
        old = field.text or ""
        field.text = new_name
        changes["name"] = {"old": old, "new": new_name}

    if new_value is not None:
        field = get_or_create_child(param, "defaultValue")
        old = field.text or ""
        field.text = new_value
        changes["value"] = {"old": old, "new": new_value}

    if new_description is not None:
        field = get_or_create_child(param, "description")
        old = field.text or ""
        field.text = new_description
        changes["description"] = {"old": old, "new": new_description}

    return changes


def post_config_xml(base_url: str, job_name: str, headers: dict[str, str], xml_text: str) -> None:
    job_path = build_job_path(job_name)
    post_headers = dict(headers)
    post_headers["Content-Type"] = "application/xml; charset=utf-8"
    request_text(
        f"{base_url.rstrip('/')}/{job_path}/config.xml",
        post_headers,
        method="POST",
        data=xml_text.encode("utf-8"),
    )


def rollback_config(base_url: str, job_name: str, headers: dict[str, str], backup_xml: str) -> None:
    post_config_xml(base_url, job_name, headers, backup_xml)


def write_stdout(text: str) -> None:
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def emit_result(payload: dict[str, object], output_format: str) -> None:
    if output_format == "json":
        write_stdout(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    for key, value in payload.items():
        write_stdout(f"{key}: {value}")


def normalize_cli_args(argv: list[str]) -> list[str]:
    if argv and argv[0].startswith("--"):
        return ["set", *argv]
    return argv


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    normalized_argv = normalize_cli_args(list(argv if argv is not None else sys.argv[1:]))

    parser = argparse.ArgumentParser(
        description="Jenkins 参数安全管理工具，支持查询参数、读取单个参数、修改 name/value/description"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="列出指定 job 的全部参数")
    list_parser.add_argument("--job", required=True, help="Jenkins job 名称，支持 folder/job 形式")
    list_parser.add_argument("--output", choices=["json", "text"], default="json")

    get_parser = subparsers.add_parser("get", help="读取指定参数的当前配置")
    get_parser.add_argument("--job", required=True, help="Jenkins job 名称，支持 folder/job 形式")
    get_parser.add_argument("--param-name", required=True, help="参数名")
    get_parser.add_argument("--output", choices=["json", "text"], default="json")

    set_parser = subparsers.add_parser("set", help="安全修改参数的名字、值、描述")
    set_parser.add_argument("--job", required=True, help="Jenkins job 名称，支持 folder/job 形式")
    set_parser.add_argument("--param-name", required=True, help="当前参数名")
    set_parser.add_argument("--new-name", help="新的参数名")
    set_parser.add_argument("--new-value", help="新的默认值，对应 defaultValue")
    set_parser.add_argument("--new-description", help="新的描述")
    set_parser.add_argument(
        "--guard-param",
        action="append",
        default=[],
        help="额外保护参数名，可重复传入；会检查 name/defaultValue/description 是否出现乱码",
    )
    set_parser.add_argument("--dry-run", action="store_true", help="仅展示变更和备份，不提交 Jenkins")
    set_parser.add_argument("--output", choices=["json", "text"], default="json")

    # 兼容旧接口：--field/--value
    set_parser.add_argument(
        "--field",
        choices=["name", "defaultValue", "description"],
        help="兼容旧接口，仅用于单字段更新",
    )
    set_parser.add_argument("--value", help="兼容旧接口，与 --field 搭配使用")

    args = parser.parse_args(normalized_argv)

    if args.command == "set":
        if args.field or args.value:
            if not args.field or args.value is None:
                raise ValueError("兼容旧接口时，--field 和 --value 必须同时提供")
            if args.field == "name":
                args.new_name = args.value
            elif args.field == "defaultValue":
                args.new_value = args.value
            elif args.field == "description":
                args.new_description = args.value

        if args.new_name is None and args.new_value is None and args.new_description is None:
            raise ValueError("set 命令至少要提供一个修改项")

    return args


def handle_list(args: argparse.Namespace, base_url: str, headers: dict[str, str]) -> int:
    root = ET.fromstring(fetch_config_xml(base_url, args.job, headers))
    parameters = [serialize_parameter(param) for param in list_parameter_definitions(root)]
    emit_result(
        {
            "job": args.job,
            "count": len(parameters),
            "parameters": parameters,
        },
        args.output,
    )
    return 0


def handle_get(args: argparse.Namespace, base_url: str, headers: dict[str, str]) -> int:
    root = ET.fromstring(fetch_config_xml(base_url, args.job, headers))
    parameter = serialize_parameter(find_parameter_definition(root, args.param_name))
    emit_result(
        {
            "job": args.job,
            "parameter": parameter,
        },
        args.output,
    )
    return 0


def handle_set(args: argparse.Namespace, base_url: str, headers: dict[str, str]) -> int:
    current_xml = fetch_config_xml(base_url, args.job, headers)
    backup_path = backup_config(args.job, current_xml)
    root = ET.fromstring(current_xml)

    changes = set_parameter_fields(
        root,
        current_name=args.param_name,
        new_name=args.new_name,
        new_value=args.new_value,
        new_description=args.new_description,
    )

    final_name = args.new_name or args.param_name
    guard_parameter_names = build_guard_parameter_names(
        current_name=args.param_name,
        new_name=args.new_name,
        extra_guards=args.guard_param,
    )

    result: dict[str, object] = {
        "job": args.job,
        "backup_path": str(backup_path),
        "target_parameter": args.param_name,
        "final_parameter": final_name,
        "changes": changes,
        "dry_run": args.dry_run,
    }

    if args.dry_run:
        emit_result(result, args.output)
        return 0

    updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
    crumb_headers = fetch_crumb_headers(base_url, headers)

    try:
        post_config_xml(base_url, args.job, crumb_headers, updated_xml)
        verified_root = ET.fromstring(fetch_config_xml(base_url, args.job, headers))
        verify_parameter_values(
            verified_root,
            parameter_name=final_name,
            expected_name=final_name if args.new_name is not None else None,
            expected_value=args.new_value,
            expected_description=args.new_description,
        )
        verify_no_mojibake(verified_root, guard_parameter_names)
    except Exception:
        rollback_config(base_url, args.job, crumb_headers, current_xml)
        raise

    result["status"] = "updated"
    emit_result(result, args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    load_env_file()
    base_url = require_env("JENKINS_URL")
    username = require_env("JENKINS_USER")
    token = require_env("JENKINS_TOKEN")
    headers = build_auth_header(username, token)

    if args.command == "list":
        return handle_list(args, base_url, headers)
    if args.command == "get":
        return handle_get(args, base_url, headers)
    if args.command == "set":
        return handle_set(args, base_url, headers)

    raise ValueError(f"未知命令: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
