#!/usr/bin/env python3
"""
SQA-AI - Smart Software Quality Analyzer (CLI)

Exit Codes:
    0   - Success / Quality gate passed
    1   - Quality gate failed (only when --fail-on-high-risk is used)
    2   - General error
    130 - Ctrl+C interrupted
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))


class ExitCode:
    SUCCESS = 0
    QUALITY_GATE_FAILED = 1
    GENERAL_ERROR = 2
    KEYBOARD_INTERRUPT = 130


@dataclass
class CriticalFileInfo:
    file_path: str
    relative_path: str
    ddi_score: float
    risk_level: str
    top_issue: str


def check_dependencies(required: Dict[str, str]) -> Tuple[bool, List[str]]:
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    return (len(missing) == 0), missing


IMPORTS_OK = False
logger = None

try:
    from core.parser import CodeParser
    from core.ddi_calculator import DDICalculator
    from core.recommendation_engine import RecommendationEngine
    from core.git_analyzer import GitAnalyzer
    from database.db_manager import DBManager
    from database.models import MetricRecord, DDIRecord, RecommendationRecord
    from utils.logger import get_logger

    IMPORTS_OK = True
    logger = get_logger("SQA-AI")
except ImportError as e:
    print(f"Import error: {e}")
    print("Run: pip install -r requirements.txt")


DEFAULT_EXTENSIONS = [
    ".py", ".pyw", ".pyi",
    ".js", ".jsx", ".mjs",
    ".ts", ".tsx",
    ".java",
]


def parse_extensions_arg(value: Optional[str]) -> List[str]:
    if not value:
        return DEFAULT_EXTENSIONS[:]
    parts = [p.strip() for p in value.split(",") if p.strip()]
    out = []
    for p in parts:
        if not p.startswith("."):
            p = "." + p
        out.append(p.lower())
    return sorted(set(out))


def _get_git_factors(git_analyzer, fm, rel_path: str) -> Dict[str, Any]:
    git_factors = None

    if git_analyzer is not None:
        try:
            factors = git_analyzer.get_ddi_factors(rel_path)
            if factors and factors.get("found"):
                git_factors = factors
                git_factors["file_path"] = fm.file_path
        except Exception as e:
            if logger:
                logger.debug(f"GitAnalyzer factors failed for {rel_path}: {e}")

    if git_factors is None:
        cc = float(getattr(fm, "cyclomatic_complexity", 0) or 0)
        max_cc = float(getattr(fm, "max_complexity", 0) or 0)
        sloc = int(getattr(fm, "sloc", 0) or 0)
        import_count = int(getattr(fm, "import_count", 0) or 0)

        commit_frequency = min(10.0, 1.0 + (cc / 20.0))
        avg_gap = 30.0 / commit_frequency if commit_frequency > 0 else 30.0

        git_factors = {
            "file_path": fm.file_path,
            "contributor_count": 1,
            "total_commits": 1,
            "age_days": 30,
            "days_since_last_change": 1,
            "contributor_entropy": min(1.0, import_count / 30.0),
            "commit_frequency": commit_frequency,
            "avg_commit_gap_days": avg_gap,
            "commit_gap_variance": max(0.0, max_cc * 10.0),
            "total_churn": sloc,
            "found": False,
        }

    return git_factors


def _get_top_issue(fm, ddi_result: Any) -> str:
    issues = []
    cc = getattr(fm, "cyclomatic_complexity", 0) or 0
    mi = getattr(fm, "maintainability_index", 100) or 100
    sloc = getattr(fm, "sloc", 0) or 0

    if cc > 20:
        issues.append(f"Very high complexity (CC={cc})")
    elif cc > 15:
        issues.append(f"High complexity (CC={cc})")

    if mi < 40:
        issues.append(f"Poor maintainability (MI={mi:.1f})")
    elif mi < 50:
        issues.append(f"Low maintainability (MI={mi:.1f})")

    if sloc > 500:
        issues.append(f"Large file ({sloc} lines)")

    if not issues:
        issues.append("Multiple factors contributing to high DDI")

    return "; ".join(issues[:2])


def attach_file_level_locations(recommendations: list, fm) -> None:
    """
    Make file-level recommendations actionable by attaching the worst function location.
    Minimal behavior change: only applies when rec has no location already.
    """
    if not getattr(fm, "functions", None):
        return

    worst_by_complexity = max(fm.functions, key=lambda f: getattr(f, "complexity", 0))
    worst_by_length = max(fm.functions, key=lambda f: getattr(f, "lines", 0))

    for rec in recommendations:
        if getattr(rec, "line_start", None) or getattr(rec, "function_name", None):
            continue

        metric = str(getattr(rec, "metric_name", "") or "").lower()
        chosen = worst_by_length if ("length" in metric or "sloc" in metric or "size" in metric) else worst_by_complexity

        rec.function_name = chosen.name
        rec.line_start = chosen.line_start
        rec.line_end = chosen.line_end
        if getattr(chosen, "class_name", None):
            rec.class_name = chosen.class_name


def _log_recommendation_with_context(rec, file_path: str, verbose: bool) -> None:
    if not logger:
        return

    severity = rec.severity.value if hasattr(rec.severity, "value") else str(rec.severity)

    location_parts = []
    if getattr(rec, "function_name", None):
        location_parts.append(f"Function: {rec.function_name}")
    if getattr(rec, "class_name", None):
        location_parts.append(f"Class: {rec.class_name}")
    if getattr(rec, "line_start", None):
        if getattr(rec, "line_end", None) and rec.line_end != rec.line_start:
            location_parts.append(f"Lines {rec.line_start}-{rec.line_end}")
        else:
            location_parts.append(f"Line {rec.line_start}")

    location_str = " | ".join(location_parts) if location_parts else "File-level"
    issue = rec.message if hasattr(rec, "message") else str(rec)
    suggestion = rec.action if hasattr(rec, "action") else "Review and refactor"

    if verbose or severity.lower() in ("critical", "high"):
        logger.recommendation_logged(
            severity=severity,
            file_path=file_path,
            location=location_str,
            issue=issue,
            suggestion=suggestion,
        )


def _calculate_summary(
    successful: int,
    failed: int,
    total_sloc: int,
    total_complexity: int,
    total_mi: int,
    all_ddi_scores: List[float],
    all_recommendations: List[Tuple],
) -> Dict[str, Any]:
    if successful > 0:
        avg_mi = total_mi / successful
        avg_cc = total_complexity / successful
        avg_ddi = sum(all_ddi_scores) / len(all_ddi_scores) if all_ddi_scores else 0.0
    else:
        avg_mi = avg_cc = avg_ddi = 0.0

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for rec, _ in all_recommendations:
        sev = rec.severity.value if hasattr(rec.severity, "value") else str(rec.severity)
        sev_lower = sev.lower()
        if sev_lower in severity_counts:
            severity_counts[sev_lower] += 1

    # DDI-driven health score (consistent + industry-friendly)
    health_score = 100.0 - float(avg_ddi)
    health_score = max(0.0, min(100.0, health_score))

    if health_score >= 80:
        status = "good"
    elif health_score >= 60:
        status = "moderate"
    elif health_score >= 40:
        status = "concerning"
    else:
        status = "critical"

    return {
        "avg_mi": avg_mi,
        "avg_cc": avg_cc,
        "avg_ddi": avg_ddi,
        "total_sloc": total_sloc,
        "health_score": health_score,
        "status": status,
        "severity_counts": severity_counts,
    }


def _update_analysis_record(db, analysis_id: int, stats: Dict, duration: float) -> None:
    with db._get_connection() as conn:
        conn.execute(
            """UPDATE analyses SET 
               total_sloc = ?, avg_maintainability_index = ?, avg_complexity = ?,
               avg_ddi_score = ?, overall_health_score = ?, overall_status = ?,
               critical_issues = ?, high_issues = ?, medium_issues = ?, low_issues = ?,
               run_duration_seconds = ?
               WHERE analysis_id = ?""",
            (
                stats["total_sloc"], stats["avg_mi"], stats["avg_cc"],
                stats["avg_ddi"], stats["health_score"], stats["status"],
                stats["severity_counts"]["critical"], stats["severity_counts"]["high"],
                stats["severity_counts"]["medium"], stats["severity_counts"]["low"],
                duration, analysis_id
            )
        )


def scan_project(
    path: str,
    name: str,
    db_path: str = "sqa.db",
    fail_on_high_risk: bool = False,
    threshold: int = 75,
    verbose: bool = False,
    extensions: Optional[List[str]] = None,
) -> int:
    start_time = time.time()
    critical_files: List[CriticalFileInfo] = []

    project_path = Path(path).resolve()
    if not project_path.exists() or not project_path.is_dir():
        print(f"Invalid path: {path}")
        return ExitCode.GENERAL_ERROR

    extensions = extensions or DEFAULT_EXTENSIONS

    if logger:
        logger.scan_start(str(project_path))
        if fail_on_high_risk:
            logger.info(f"CI/CD Quality Gate enabled with threshold: {threshold}")

    db = DBManager(db_path)
    parser = CodeParser()
    ddi_calculator = DDICalculator()
    recommendation_engine = RecommendationEngine()

    git_analyzer = None
    try:
        git_analyzer = GitAnalyzer(str(project_path))
        if logger:
            logger.info("GitAnalyzer enabled (using real git history for DDI)")
    except Exception as e:
        if logger:
            logger.info(f"GitAnalyzer disabled (using stub factors). Reason: {e}")

    project_id = db.get_or_create_project(name, str(project_path))
    print(f"Project ID: {project_id}")

    file_metrics = parser.parse_directory(str(project_path), extensions=extensions)
    if not file_metrics:
        print("No supported source files found.")
        return ExitCode.SUCCESS

    analysis_id = db.create_analysis(project_id=project_id, total_files=len(file_metrics), analyzer_version="1.0.0")

    successful = failed = skipped = 0
    total_sloc = total_complexity = total_mi = 0
    all_ddi_scores: List[float] = []
    all_recommendations: List[Tuple] = []

    for fm in file_metrics:
        try:
            if not fm.parse_success:
                failed += 1
                continue

            rel_path = str(Path(fm.file_path).relative_to(project_path))
            file_id = db.create_or_update_file(
                project_id=project_id,
                path=fm.file_path,
                relative_path=rel_path,
                filename=Path(fm.file_path).name,
                language=fm.language,
            )

            metric_record = MetricRecord.from_parser_result(file_id, fm.to_dict())
            db.save_metrics(metric_record, analysis_id)

            git_factors = _get_git_factors(git_analyzer, fm, rel_path)
            ddi_result = ddi_calculator.calculate_ddi(git_factors, fm.to_dict())
            ddi_record = DDIRecord.from_ddi_result(file_id, ddi_result)
            db.save_ddi(ddi_record, analysis_id)
            all_ddi_scores.append(ddi_record.ddi_score)

            if ddi_record.ddi_score >= threshold:
                critical_files.append(CriticalFileInfo(
                    file_path=fm.file_path,
                    relative_path=rel_path,
                    ddi_score=ddi_record.ddi_score,
                    risk_level=ddi_record.risk_level,
                    top_issue=_get_top_issue(fm, ddi_result),
                ))

            recommendations = recommendation_engine.analyze_file(
                fm.file_path,
                fm.to_dict(),
                ddi_result,
                [f.to_dict() for f in fm.functions],
                [c.to_dict() for c in fm.classes],
            )

            # Attach exact location for file-level recs
            attach_file_level_locations(recommendations, fm)

            for rec in recommendations:
                rec_record = RecommendationRecord.from_recommendation(analysis_id, rec, file_id)
                db.save_recommendation(rec_record)
                all_recommendations.append((rec, rel_path))
                _log_recommendation_with_context(rec, rel_path, verbose)

            db.save_snapshot_from_metrics(file_id, metric_record, ddi_record)

            total_sloc += fm.sloc
            total_complexity += fm.cyclomatic_complexity
            total_mi += fm.maintainability_index
            successful += 1

        except Exception as e:
            failed += 1
            if logger:
                logger.error_with_context("Unexpected error processing file", file_path=fm.file_path, exception=e)

    duration = time.time() - start_time
    stats = _calculate_summary(successful, failed, total_sloc, total_complexity, total_mi, all_ddi_scores, all_recommendations)
    _update_analysis_record(db, analysis_id, stats, duration)

    print(f"\nHealth Score: {stats['health_score']:.0f}/100 ({stats['status'].upper()})")
    print(f"Avg DDI: {stats['avg_ddi']:.1f} | Avg MI: {stats['avg_mi']:.1f} | Avg CC: {stats['avg_cc']:.1f}")
    print(f"Recommendations: {len(all_recommendations)}")

    if fail_on_high_risk and critical_files:
        if logger:
            logger.cicd_gate_result(passed=False, critical_count=len(critical_files), threshold=threshold)
        print("CI/CD QUALITY GATE: FAILED")
        return ExitCode.QUALITY_GATE_FAILED

    if fail_on_high_risk:
        if logger:
            logger.cicd_gate_result(passed=True, critical_count=0, threshold=threshold)
        print("CI/CD QUALITY GATE: PASSED")

    return ExitCode.SUCCESS


def generate_report(project_id: int, output: Optional[str], fmt: str, db_path: str) -> int:
    from utils.report_generator import ReportGenerator, ReportConfig

    db = DBManager(db_path)
    project = db.get_project(project_id)
    if not project:
        print("Project not found")
        return ExitCode.GENERAL_ERROR

    summary = db.get_project_summary(project_id)
    latest = summary.get("latest_analysis") or {}

    # Trend history (full table)
    history = db.get_analysis_history(project_id, limit=50)
    history_dicts = [h.to_dict() for h in history] if history else []

    # Delta vs previous
    delta = {}
    if history and len(history) >= 2:
        latest_a = history[0]
        prev_a = history[1]
        delta = {
            "run_at_prev": prev_a.run_at.isoformat() if prev_a.run_at else None,
            "health_score": latest_a.overall_health_score - prev_a.overall_health_score,
            "avg_ddi": latest_a.avg_ddi_score - prev_a.avg_ddi_score,
            "avg_mi": latest_a.avg_maintainability_index - prev_a.avg_maintainability_index,
            "avg_cc": latest_a.avg_complexity - prev_a.avg_complexity,
            "total_sloc": latest_a.total_sloc - prev_a.total_sloc,
            "total_files": latest_a.total_files - prev_a.total_files,
        }

    report_summary = {
        "health_score": latest.get("overall_health_score", 0),
        "status": latest.get("overall_status", "unknown"),
        "files_analyzed": summary.get("file_count", 0),
        "total_sloc": latest.get("total_sloc", 0),
        "avg_ddi": latest.get("avg_ddi_score", 0),
        "avg_mi": latest.get("avg_maintainability_index", 0),
        "avg_cc": latest.get("avg_complexity", 0),
        "severity_counts": {
            "critical": latest.get("critical_issues", 0),
            "high": latest.get("high_issues", 0),
            "medium": latest.get("medium_issues", 0),
            "low": latest.get("low_issues", 0),
        },
        "delta_vs_previous": delta,
    }

    files = db.get_project_files_with_metrics(project_id)
    recs = db.get_project_recommendations(project_id)

    if not output:
        Path("exports").mkdir(parents=True, exist_ok=True)
        output = f"exports/report_project_{project_id}.{fmt}"

    generator = ReportGenerator(ReportConfig(title=f"SQA-AI Report: {project.name}"))
    out_path = generator.generate(
        output_path=output,
        project_name=project.name,
        project_path=project.path,
        summary=report_summary,
        files=files,
        recommendations=recs,
        format=fmt,
        trends=history_dicts,
    )
    print(f"Report generated: {out_path}")
    return ExitCode.SUCCESS


def create_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sqa-ai", description="SQA-AI CLI")
    sp = p.add_subparsers(dest="command")

    s = sp.add_parser("scan")
    s.add_argument("--path", "-p", required=True)
    s.add_argument("--name", "-n", required=True)
    s.add_argument("--db", default="sqa.db")
    s.add_argument("--fail-on-high-risk", "-f", action="store_true")
    s.add_argument("--threshold", "-t", type=int, default=75)
    s.add_argument("--verbose", "-v", action="store_true")
    s.add_argument("--extensions", "-e", default=None)

    r = sp.add_parser("report")
    r.add_argument("--project-id", "-id", type=int, required=True)
    r.add_argument("--output", "-o", default=None)
    r.add_argument("--format", "-f", choices=["txt", "json", "html", "pdf"], default="html")
    r.add_argument("--db", default="sqa.db")

    sp.add_parser("dashboard")
    l = sp.add_parser("list")
    l.add_argument("--db", default="sqa.db")
    return p


def main() -> int:
    if not IMPORTS_OK:
        return ExitCode.GENERAL_ERROR

    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.command == "scan":
            ok, missing = check_dependencies({"radon": "radon", "yaml": "pyyaml"})
            if not ok:
                print(f"Missing: {missing}")
                return ExitCode.GENERAL_ERROR
            exts = parse_extensions_arg(args.extensions)
            return scan_project(
                path=args.path,
                name=args.name,
                db_path=args.db,
                fail_on_high_risk=args.fail_on_high_risk,
                threshold=args.threshold,
                verbose=args.verbose,
                extensions=exts,
            )

        if args.command == "report":
            ok, missing = check_dependencies({"yaml": "pyyaml"})
            if not ok:
                print(f"Missing: {missing}")
                return ExitCode.GENERAL_ERROR
            return generate_report(args.project_id, args.output, args.format, args.db)

        if args.command == "list":
            db = DBManager(args.db)
            for pr in db.get_all_projects():
                print(f"[{pr.project_id}] {pr.name} - {pr.path}")
            return ExitCode.SUCCESS

        if args.command == "dashboard":
            import subprocess
            dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
            return subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_path)]).returncode

        parser.print_help()
        return ExitCode.SUCCESS

    except KeyboardInterrupt:
        return ExitCode.KEYBOARD_INTERRUPT
    except Exception as e:
        if logger:
            logger.critical(f"Fatal error: {e}", exc_info=True)
        return ExitCode.GENERAL_ERROR


if __name__ == "__main__":
    sys.exit(main())
    