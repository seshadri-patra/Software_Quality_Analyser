"""
Database Manager for SQA-AI
Handles all database operations using SQLite
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

from .models import (
    Project, FileRecord, MetricRecord,
    AnalysisRecord, RecommendationRecord, DDIRecord
)


class DBManager:
    """
    Manages SQLite database operations for SQA-AI
    """

    def __init__(self, db_path: str = "sqa.db"):
        self.db_path = Path(db_path)
        self._logger = None
        self._init_logger()
        self._initialize_database()

    def _init_logger(self) -> None:
        try:
            from utils.logger import get_logger
            self._logger = get_logger(__name__)
        except ImportError:
            self._logger = None

    def _log(self, level: str, message: str) -> None:
        if self._logger:
            getattr(self._logger, level)(message)

    @contextmanager
    def _get_connection(self):
        # check_same_thread=False makes Streamlit re-runs safer
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self._log("error", f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _initialize_database(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"

        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = f.read()
            with self._get_connection() as conn:
                conn.executescript(schema)
            self._log("info", f"Database initialized at {self.db_path}")
        else:
            # Fallback schema must remain compatible with create_analysis/create_project/etc.
            self._create_minimal_schema()

    def _create_minimal_schema(self) -> None:
        """
        Complete fallback schema (compatible with schema.sql fields used by DBManager).
        """
        minimal_schema = """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            description TEXT,
            language TEXT DEFAULT 'python',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS analyses (
            analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,

            total_files INTEGER DEFAULT 0,
            total_sloc INTEGER DEFAULT 0,
            avg_maintainability_index REAL DEFAULT 0.0,
            avg_complexity REAL DEFAULT 0.0,
            avg_ddi_score REAL DEFAULT 0.0,

            overall_health_score REAL DEFAULT 100.0,
            overall_status TEXT DEFAULT 'good',

            critical_issues INTEGER DEFAULT 0,
            high_issues INTEGER DEFAULT 0,
            medium_issues INTEGER DEFAULT 0,
            low_issues INTEGER DEFAULT 0,

            analyzer_version TEXT DEFAULT '1.0.0',
            run_duration_seconds REAL DEFAULT 0.0,
            notes TEXT,
            run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        );

        CREATE TABLE IF NOT EXISTS files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            path TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            language TEXT DEFAULT 'python',
            content_hash TEXT,
            last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            UNIQUE(project_id, relative_path)
        );

        CREATE TABLE IF NOT EXISTS metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            analysis_id INTEGER,

            loc INTEGER DEFAULT 0,
            sloc INTEGER DEFAULT 0,
            blank_lines INTEGER DEFAULT 0,
            comment_lines INTEGER DEFAULT 0,
            comment_density REAL DEFAULT 0,

            cyclomatic_complexity REAL DEFAULT 0,
            max_complexity INTEGER DEFAULT 0,
            avg_complexity REAL DEFAULT 0,
            complexity_rank TEXT DEFAULT 'A',

            maintainability_index REAL DEFAULT 100,
            mi_rank TEXT DEFAULT 'A',

            halstead_volume REAL DEFAULT 0,
            halstead_difficulty REAL DEFAULT 0,
            halstead_effort REAL DEFAULT 0,
            halstead_bugs REAL DEFAULT 0,

            function_count INTEGER DEFAULT 0,
            class_count INTEGER DEFAULT 0,
            import_count INTEGER DEFAULT 0,
            avg_function_length REAL DEFAULT 0,
            max_function_length INTEGER DEFAULT 0,

            docstring_coverage REAL DEFAULT 0,

            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(file_id),
            FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id)
        );

        CREATE TABLE IF NOT EXISTS ddi_records (
            ddi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            analysis_id INTEGER,

            ddi_score REAL DEFAULT 0,
            risk_level TEXT DEFAULT 'low',

            decay_rate_score REAL DEFAULT 0,
            entropy_score REAL DEFAULT 0,
            volatility_score REAL DEFAULT 0,
            frequency_score REAL DEFAULT 0,

            decay_rate REAL DEFAULT 0,
            contributor_entropy REAL DEFAULT 0,
            volatility REAL DEFAULT 0,
            commit_frequency REAL DEFAULT 0,

            contributor_count INTEGER DEFAULT 0,
            total_commits INTEGER DEFAULT 0,
            age_days INTEGER DEFAULT 0,
            days_since_last_change INTEGER DEFAULT 0,

            confidence REAL DEFAULT 0,
            predicted_issue_probability REAL DEFAULT 0,
            recommended_action TEXT,

            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(file_id),
            FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id)
        );

        CREATE TABLE IF NOT EXISTS recommendations (
            rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            file_id INTEGER,

            title TEXT NOT NULL,
            message TEXT,
            severity TEXT DEFAULT 'medium',
            category TEXT DEFAULT 'general',

            metric_name TEXT,
            metric_value REAL,
            threshold REAL,

            action TEXT,
            effort_estimate TEXT DEFAULT 'medium',
            impact TEXT DEFAULT 'medium',
            priority_score REAL DEFAULT 0,

            line_start INTEGER,
            line_end INTEGER,
            function_name TEXT,
            class_name TEXT,

            status TEXT DEFAULT 'open',
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id),
            FOREIGN KEY (file_id) REFERENCES files(file_id)
        );

        CREATE TABLE IF NOT EXISTS metric_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            maintainability_index REAL,
            cyclomatic_complexity REAL,
            sloc INTEGER,
            comment_density REAL,
            ddi_score REAL,
            snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(file_id)
        );
        """
        with self._get_connection() as conn:
            conn.executescript(minimal_schema)

        self._log("info", "Fallback database schema created")

    # ==========================================
    # PROJECT OPERATIONS
    # ==========================================

    def create_project(self, name: str, path: str, language: str = "python", description: str = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO projects (name, path, language, description)
                   VALUES (?, ?, ?, ?)""",
                (name, path, language, description),
            )
            project_id = cursor.lastrowid
            self._log("info", f"Created project: {name} (ID: {project_id})")
            return project_id

    def get_project(self, project_id: int) -> Optional[Project]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return Project.from_row(tuple(row), columns)
        return None

    def get_project_by_path(self, path: str) -> Optional[Project]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE path = ?", (path,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return Project.from_row(tuple(row), columns)
        return None

    def get_all_projects(self) -> List[Project]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM projects WHERE is_active = 1 ORDER BY name")
            columns = [desc[0] for desc in cursor.description]
            return [Project.from_row(tuple(row), columns) for row in cursor.fetchall()]

    def update_project(self, project_id: int, **kwargs) -> bool:
        allowed_fields = {"name", "description", "language", "is_active"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [project_id]

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE projects SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE project_id = ?",
                values,
            )
        return True

    def delete_project(self, project_id: int) -> bool:
        return self.update_project(project_id, is_active=0)

    def get_or_create_project(self, name: str, path: str, **kwargs) -> int:
        project = self.get_project_by_path(path)
        if project:
            return project.project_id
        return self.create_project(name, path, **kwargs)

    # ==========================================
    # FILE OPERATIONS
    # ==========================================

    def create_or_update_file(
        self,
        project_id: int,
        path: str,
        relative_path: str,
        filename: str,
        language: str = "python",
        content_hash: str = None,
    ) -> int:
        existing = self.get_file_by_path(project_id, relative_path)
        if existing:
            with self._get_connection() as conn:
                conn.execute(
                    """UPDATE files
                       SET path = ?, filename = ?, language = ?, content_hash = ?,
                           last_scanned = CURRENT_TIMESTAMP, is_active = 1
                       WHERE file_id = ?""",
                    (path, filename, language, content_hash, existing.file_id),
                )
            return existing.file_id

        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO files (project_id, path, relative_path, filename, language, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_id, path, relative_path, filename, language, content_hash),
            )
            return cursor.lastrowid

    def get_file(self, file_id: int) -> Optional[FileRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return FileRecord.from_row(tuple(row), columns)
        return None

    def get_file_by_path(self, project_id: int, relative_path: str) -> Optional[FileRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM files WHERE project_id = ? AND relative_path = ?",
                (project_id, relative_path),
            )
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return FileRecord.from_row(tuple(row), columns)
        return None

    def get_project_files(self, project_id: int) -> List[FileRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM files WHERE project_id = ? AND is_active = 1",
                (project_id,),
            )
            columns = [desc[0] for desc in cursor.description]
            return [FileRecord.from_row(tuple(row), columns) for row in cursor.fetchall()]

    # ==========================================
    # METRICS OPERATIONS
    # ==========================================

    def save_metrics(self, metrics: MetricRecord, analysis_id: int = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO metrics (
                    file_id, analysis_id, loc, sloc, blank_lines, comment_lines,
                    comment_density, cyclomatic_complexity, max_complexity,
                    avg_complexity, complexity_rank, maintainability_index,
                    mi_rank, halstead_volume, halstead_difficulty, halstead_effort,
                    halstead_bugs, function_count, class_count, import_count,
                    avg_function_length, max_function_length, docstring_coverage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    metrics.file_id, analysis_id, metrics.loc, metrics.sloc,
                    metrics.blank_lines, metrics.comment_lines, metrics.comment_density,
                    metrics.cyclomatic_complexity, metrics.max_complexity,
                    metrics.avg_complexity, metrics.complexity_rank,
                    metrics.maintainability_index, metrics.mi_rank,
                    metrics.halstead_volume, metrics.halstead_difficulty,
                    metrics.halstead_effort, metrics.halstead_bugs,
                    metrics.function_count, metrics.class_count, metrics.import_count,
                    metrics.avg_function_length, metrics.max_function_length,
                    metrics.docstring_coverage
                ),
            )
            return cursor.lastrowid

    def get_latest_metrics(self, file_id: int) -> Optional[MetricRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM metrics WHERE file_id = ?
                   ORDER BY computed_at DESC, metric_id DESC LIMIT 1""",
                (file_id,),
            )
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return MetricRecord.from_row(tuple(row), columns)
        return None

    # ==========================================
    # DDI OPERATIONS
    # ==========================================

    def save_ddi(self, ddi: DDIRecord, analysis_id: int = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO ddi_records (
                    file_id, analysis_id, ddi_score, risk_level,
                    decay_rate_score, entropy_score, volatility_score, frequency_score,
                    decay_rate, contributor_entropy, volatility, commit_frequency,
                    contributor_count, total_commits, age_days, days_since_last_change,
                    confidence, predicted_issue_probability, recommended_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ddi.file_id, analysis_id, ddi.ddi_score, ddi.risk_level,
                    ddi.decay_rate_score, ddi.entropy_score, ddi.volatility_score,
                    ddi.frequency_score, ddi.decay_rate, ddi.contributor_entropy,
                    ddi.volatility, ddi.commit_frequency, ddi.contributor_count,
                    ddi.total_commits, ddi.age_days, ddi.days_since_last_change,
                    ddi.confidence, ddi.predicted_issue_probability, ddi.recommended_action
                ),
            )
            return cursor.lastrowid

    def get_latest_ddi(self, file_id: int) -> Optional[DDIRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM ddi_records WHERE file_id = ?
                   ORDER BY computed_at DESC, ddi_id DESC LIMIT 1""",
                (file_id,),
            )
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return DDIRecord.from_row(tuple(row), columns)
        return None

    def get_high_risk_files(self, project_id: int, min_score: float = 75.0) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT f.file_id, f.relative_path, f.filename,
                          d.ddi_score, d.risk_level, d.recommended_action
                   FROM files f
                   JOIN ddi_records d ON f.file_id = d.file_id
                   WHERE f.project_id = ? AND d.ddi_score >= ?
                   AND d.ddi_id = (SELECT MAX(d2.ddi_id) FROM ddi_records d2 WHERE d2.file_id = f.file_id)
                   ORDER BY d.ddi_score DESC""",
                (project_id, min_score),
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==========================================
    # ANALYSIS OPERATIONS
    # ==========================================

    def create_analysis(self, project_id: int, **kwargs) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO analyses (
                    project_id, total_files, total_sloc, avg_maintainability_index,
                    avg_complexity, avg_ddi_score, overall_health_score, overall_status,
                    critical_issues, high_issues, medium_issues, low_issues,
                    analyzer_version, run_duration_seconds, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project_id,
                    kwargs.get("total_files", 0),
                    kwargs.get("total_sloc", 0),
                    kwargs.get("avg_maintainability_index", 0.0),
                    kwargs.get("avg_complexity", 0.0),
                    kwargs.get("avg_ddi_score", 0.0),
                    kwargs.get("overall_health_score", 100.0),
                    kwargs.get("overall_status", "good"),
                    kwargs.get("critical_issues", 0),
                    kwargs.get("high_issues", 0),
                    kwargs.get("medium_issues", 0),
                    kwargs.get("low_issues", 0),
                    kwargs.get("analyzer_version", "1.0.0"),
                    kwargs.get("run_duration_seconds", 0.0),
                    kwargs.get("notes"),
                ),
            )
            return cursor.lastrowid

    def get_analysis(self, analysis_id: int) -> Optional[AnalysisRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM analyses WHERE analysis_id = ?", (analysis_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return AnalysisRecord.from_row(tuple(row), columns)
        return None

    def get_latest_analysis(self, project_id: int) -> Optional[AnalysisRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM analyses WHERE project_id = ?
                   ORDER BY run_at DESC, analysis_id DESC LIMIT 1""",
                (project_id,),
            )
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return AnalysisRecord.from_row(tuple(row), columns)
        return None

    def get_analysis_history(self, project_id: int, limit: int = 10) -> List[AnalysisRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM analyses WHERE project_id = ?
                   ORDER BY run_at DESC, analysis_id DESC LIMIT ?""",
                (project_id, limit),
            )
            columns = [desc[0] for desc in cursor.description]
            return [AnalysisRecord.from_row(tuple(row), columns) for row in cursor.fetchall()]

    # ==========================================
    # RECOMMENDATION OPERATIONS
    # ==========================================

    def save_recommendation(self, rec: RecommendationRecord) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO recommendations (
                    analysis_id, file_id, title, message, severity, category,
                    metric_name, metric_value, threshold, action, effort_estimate,
                    impact, priority_score, line_start, line_end, function_name, class_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    rec.analysis_id, rec.file_id, rec.title, rec.message,
                    rec.severity, rec.category, rec.metric_name, rec.metric_value,
                    rec.threshold, rec.action, rec.effort_estimate, rec.impact,
                    rec.priority_score, rec.line_start, rec.line_end,
                    rec.function_name, rec.class_name
                ),
            )
            return cursor.lastrowid

    def get_recommendations(self, analysis_id: int) -> List[RecommendationRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM recommendations WHERE analysis_id = ?
                   ORDER BY priority_score DESC""",
                (analysis_id,),
            )
            columns = [desc[0] for desc in cursor.description]
            return [RecommendationRecord.from_row(tuple(row), columns) for row in cursor.fetchall()]

    # ===== NEW: join recommendations with files (fix “where is it?” problem) =====

    def get_recommendations_with_file_info(self, analysis_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    r.rec_id, r.analysis_id, r.file_id,
                    r.title, r.message, r.severity, r.category,
                    r.metric_name, r.metric_value, r.threshold,
                    r.action, r.effort_estimate, r.impact, r.priority_score,
                    r.line_start, r.line_end, r.function_name, r.class_name,
                    r.status, r.created_at,
                    f.filename, f.relative_path
                FROM recommendations r
                LEFT JOIN files f ON f.file_id = r.file_id
                WHERE r.analysis_id = ?
                ORDER BY r.priority_score DESC, r.rec_id DESC
                LIMIT ?
                """,
                (analysis_id, limit),
            )
            out = []
            for row in cursor.fetchall():
                d = dict(row)
                # normalize: dashboard prefers file_path or filename
                if d.get("relative_path"):
                    d["file_path"] = d["relative_path"]
                out.append(d)
            return out

    # ==========================================
    # METRIC HISTORY OPERATIONS
    # ==========================================

    def save_metric_history(
        self,
        file_id: int,
        maintainability_index: float = None,
        cyclomatic_complexity: float = None,
        sloc: int = None,
        comment_density: float = None,
        ddi_score: float = None,
    ) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO metric_history (
                    file_id, maintainability_index, cyclomatic_complexity,
                    sloc, comment_density, ddi_score
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                (file_id, maintainability_index, cyclomatic_complexity, sloc, comment_density, ddi_score),
            )
            return cursor.lastrowid

    def get_metric_history_for_file(self, file_id: int, limit: int = 30) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT * FROM metric_history
                   WHERE file_id = ?
                   ORDER BY snapshot_at DESC
                   LIMIT ?""",
                (file_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def save_snapshot_from_metrics(self, file_id: int, metrics: MetricRecord, ddi: DDIRecord = None) -> int:
        return self.save_metric_history(
            file_id=file_id,
            maintainability_index=metrics.maintainability_index,
            cyclomatic_complexity=metrics.cyclomatic_complexity,
            sloc=metrics.sloc,
            comment_density=metrics.comment_density,
            ddi_score=ddi.ddi_score if ddi else None,
        )

    # ==========================================
    # STATISTICS & QUERIES
    # ==========================================

    def get_project_summary(self, project_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM files WHERE project_id = ? AND is_active = 1",
                (project_id,),
            )
            file_count = cursor.fetchone()[0]

            latest = self.get_latest_analysis(project_id)

            cursor = conn.execute(
                """SELECT risk_level, COUNT(*) as count
                   FROM ddi_records d
                   JOIN files f ON d.file_id = f.file_id
                   WHERE f.project_id = ?
                   AND d.ddi_id = (SELECT MAX(d2.ddi_id) FROM ddi_records d2 WHERE d2.file_id = d.file_id)
                   GROUP BY risk_level""",
                (project_id,),
            )
            risk_distribution = {row["risk_level"]: row["count"] for row in cursor.fetchall()}

            return {
                "project_id": project_id,
                "file_count": file_count,
                "latest_analysis": latest.to_dict() if latest else None,
                "risk_distribution": risk_distribution,
            }

    def get_dashboard_data(self, project_id: int) -> Dict[str, Any]:
        project = self.get_project(project_id)
        summary = self.get_project_summary(project_id)
        files = self.get_project_files(project_id)
        high_risk = self.get_high_risk_files(project_id)

        latest_analysis = self.get_latest_analysis(project_id)
        recommendations: List[Dict[str, Any]] = []
        if latest_analysis:
            # FIX: include file info so user can see where the recommendation applies
            recommendations = self.get_recommendations_with_file_info(latest_analysis.analysis_id, limit=20)

        file_metrics = []
        for f in files:
            metrics = self.get_latest_metrics(f.file_id)
            ddi = self.get_latest_ddi(f.file_id)
            file_metrics.append({
                "file": f.to_dict(),
                "metrics": metrics.to_dict() if metrics else None,
                "ddi": ddi.to_dict() if ddi else None,
            })

        return {
            "project": project.to_dict() if project else None,
            "summary": summary,
            "files": file_metrics,
            "high_risk_files": high_risk,
            "recommendations": recommendations,
        }

    # ==========================================
    # REPORT HELPERS (NEW - required by main.py report)
    # ==========================================

    def get_project_files_with_metrics(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Used by main.py -> generate_report().
        Returns file + latest metrics + latest ddi in a single list of dicts.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    f.file_id,
                    f.relative_path,
                    f.filename,
                    f.language,

                    m.loc, m.sloc, m.blank_lines, m.comment_lines, m.comment_density,
                    m.cyclomatic_complexity, m.max_complexity, m.avg_complexity, m.complexity_rank,
                    m.maintainability_index, m.mi_rank,
                    m.halstead_volume, m.halstead_difficulty, m.halstead_effort, m.halstead_bugs,
                    m.function_count, m.class_count, m.import_count,
                    m.avg_function_length, m.max_function_length, m.docstring_coverage,

                    d.ddi_score, d.risk_level,
                    d.decay_rate_score, d.entropy_score, d.volatility_score, d.frequency_score,
                    d.contributor_count, d.total_commits, d.age_days, d.days_since_last_change,
                    d.confidence, d.predicted_issue_probability, d.recommended_action

                FROM files f
                LEFT JOIN metrics m
                  ON m.file_id = f.file_id
                 AND m.metric_id = (SELECT MAX(m2.metric_id) FROM metrics m2 WHERE m2.file_id = f.file_id)

                LEFT JOIN ddi_records d
                  ON d.file_id = f.file_id
                 AND d.ddi_id = (SELECT MAX(d2.ddi_id) FROM ddi_records d2 WHERE d2.file_id = f.file_id)

                WHERE f.project_id = ? AND f.is_active = 1
                ORDER BY (d.ddi_score IS NULL) ASC, d.ddi_score DESC
                """,
                (project_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_project_recommendations(self, project_id: int, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Used by main.py -> generate_report().
        Returns recommendations for the latest analysis of the project with file info.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    r.rec_id, r.analysis_id, r.file_id,
                    r.title, r.message, r.severity, r.category,
                    r.metric_name, r.metric_value, r.threshold,
                    r.action, r.effort_estimate, r.impact, r.priority_score,
                    r.line_start, r.line_end, r.function_name, r.class_name,
                    r.status, r.created_at,
                    f.filename, f.relative_path
                FROM recommendations r
                JOIN analyses a ON a.analysis_id = r.analysis_id
                LEFT JOIN files f ON f.file_id = r.file_id
                WHERE a.project_id = ?
                  AND a.analysis_id = (SELECT MAX(a2.analysis_id) FROM analyses a2 WHERE a2.project_id = ?)
                ORDER BY r.priority_score DESC, r.rec_id DESC
                LIMIT ?
                """,
                (project_id, project_id, limit),
            )

            out = []
            for row in cursor.fetchall():
                d = dict(row)
                if d.get("relative_path"):
                    d["file_path"] = d["relative_path"]
                out.append(d)
            return out

    # ==========================================
    # MAINTENANCE
    # ==========================================

    def vacuum(self) -> None:
        with self._get_connection() as conn:
            conn.execute("VACUUM")
        self._log("info", "Database vacuumed")

    def get_database_stats(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            stats = {}
            tables = ["projects", "files", "metrics", "ddi_records", "analyses", "recommendations", "metric_history"]
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                except Exception:
                    stats[table] = 0
        return stats

    def __repr__(self) -> str:
        return f"DBManager(db_path='{self.db_path}')"
        