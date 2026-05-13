from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict

import yaml

from modules.confluence_client import ConfluenceClient
from modules.coverage_analyzer import CoverageAnalyzer
from modules.report_generator import ReportGenerator
from modules.requirement_loader import RequirementLoader
from modules.testcase_loader import TestCaseLoader
from modules.tracer import Tracer


def _project_root_from_config(config: Dict) -> Path:
    root = config.get("_project_root")
    if root:
        return Path(root).resolve()
    return Path(__file__).resolve().parent


def load_config(config_path: str) -> Dict:
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg["_project_root"] = str(path.parent)

    test_mode = cfg.get("test_mode", {})
    if test_mode.get("enabled"):
        cfg["r4j_projects"] = test_mode.get("r4j_projects", cfg.get("r4j_projects", []))
        cfg["confluence_testcases"] = test_mode.get("confluence_testcases", cfg.get("confluence_testcases", []))
    return cfg


def setup_logging(config: Dict, verbose: bool = False, log_file: str | None = None) -> None:
    log_cfg = config.get("logging", {})
    level_name = "DEBUG" if verbose else log_cfg.get("level", "INFO")
    level = getattr(logging, str(level_name).upper(), logging.INFO)
    fmt = log_cfg.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handlers = [logging.StreamHandler()]
    if log_file:
        project_root = _project_root_from_config(config)
        log_dir = project_root / "tempFile" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_name = Path(log_file).name
        handlers.append(logging.FileHandler(log_dir / log_name, encoding="utf-8"))

    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)


def run(args: argparse.Namespace) -> Path:
    config = load_config(args.config)
    setup_logging(config, verbose=args.verbose, log_file=args.log)
    logger = logging.getLogger("v_model_tracer")
    project_root = _project_root_from_config(config)

    logger.info("开始加载需求数据")
    requirement_loader = RequirementLoader(config=config, use_cache=not args.no_cache)
    requirements = requirement_loader.load_all_projects(project_filter=args.project)
    logger.info("需求加载完成: %s", len(requirements))

    logger.info("开始加载测试用例")
    api_cfg = config.get("api", {})
    confluence_client = ConfluenceClient.from_env(
        timeout=int(api_cfg.get("timeout", 30)),
        retry_times=int(api_cfg.get("retry_times", 3)),
    )
    testcase_loader = TestCaseLoader(config=config, client=confluence_client, use_cache=not args.no_cache)
    testcases = testcase_loader.load_all_testcases()
    logger.info("测试用例加载完成: %s", len(testcases))

    tracer = Tracer(v_model_mapping=config.get("v_model_mapping", {}))
    if args.coverage_only:
        issues = []
        logger.info("覆盖率模式：跳过问题检查")
    else:
        logger.info("开始执行追溯检查")
        issues = tracer.run_full_check(testcases=testcases, requirements=requirements)
        summary = tracer.issue_summary(issues)
        logger.info("追溯检查完成: %s", summary)

    analyzer = CoverageAnalyzer(requirements=requirements, testcases=testcases)
    coverage_rows = analyzer.calculate_requirement_coverage()
    pass_rate_rows = analyzer.calculate_test_pass_rate()

    report_generator = ReportGenerator(
        output_cfg=config.get("output", {}),
        project_root=project_root,
        testcases=testcases,
        requirements=requirements,
        issues=issues,
        coverage_rows=coverage_rows,
        pass_rate_rows=pass_rate_rows,
    )
    output_path = report_generator.generate_report(output_filename=args.output)
    logger.info("报告生成完成: %s", output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="V 模型用例-需求双向追溯检查工具")
    parser.add_argument("--config", "-c", default="config.yaml", help="配置文件路径")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存并强制刷新")
    parser.add_argument("--project", "-p", help="按项目名过滤（模糊匹配）")
    parser.add_argument("--coverage-only", action="store_true", help="只生成覆盖率/通过率统计")
    parser.add_argument("--verbose", "-v", action="store_true", help="启用调试日志")
    parser.add_argument("--output", "-o", help="输出文件名（仅文件名，不含目录）")
    parser.add_argument("--log", help="日志文件路径")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()
