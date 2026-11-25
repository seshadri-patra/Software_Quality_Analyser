"""
Data Models for SQA-AI Database
Provides type-safe data classes for database records
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any, Union


def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Try common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def safe_get(data: Dict, key: str, default: Any = None, cast_type: type = None) -> Any:
    """Safely get value from dictionary with optional type casting"""
    value = data.get(key, default)
    if value is None:
        return default
    if cast_type is not None:
        try:
            return cast_type(value)
        except (TypeError, ValueError):
            return default
    return value


@dataclass
class Project:
    """Project record"""
    name: str
    path: str
    description: Optional[str] = None
    language: str = 'python'
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        if data['updated_at']:
            data['updated_at'] = data['updated_at'].isoformat()
        return data
    
    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> 'Project':
        """Create Project from database row"""
        data = dict(zip(columns, row))
        return cls(
            project_id=safe_get(data, 'project_id', cast_type=int),
            name=safe_get(data, 'name', ''),
            path=safe_get(data, 'path', ''),
            description=safe_get(data, 'description'),
            language=safe_get(data, 'language', 'python'),
            created_at=parse_datetime(data.get('created_at')),
            updated_at=parse_datetime(data.get('updated_at')),
            is_active=bool(safe_get(data, 'is_active', 1))
        )


@dataclass
class FileRecord:
    """File record"""
    project_id: int
    path: str
    relative_path: str
    filename: str
    language: str = 'python'
    file_id: Optional[int] = None
    content_hash: Optional[str] = None
    last_scanned: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data['last_scanned']:
            data['last_scanned'] = data['last_scanned'].isoformat()
        return data
    
    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> 'FileRecord':
        """Create FileRecord from database row"""
        data = dict(zip(columns, row))
        return cls(
            file_id=safe_get(data, 'file_id', cast_type=int),
            project_id=safe_get(data, 'project_id', 0, int),
            path=safe_get(data, 'path', ''),
            relative_path=safe_get(data, 'relative_path', ''),
            filename=safe_get(data, 'filename', ''),
            language=safe_get(data, 'language', 'python'),
            content_hash=safe_get(data, 'content_hash'),
            last_scanned=parse_datetime(data.get('last_scanned')),
            is_active=bool(safe_get(data, 'is_active', 1))
        )


@dataclass
class MetricRecord:
    """Metrics record for a file"""
    file_id: int
    
    # Size metrics
    loc: int = 0
    sloc: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    comment_density: float = 0.0
    
    # Complexity
    cyclomatic_complexity: float = 0.0
    max_complexity: int = 0
    avg_complexity: float = 0.0
    complexity_rank: str = 'A'
    
    # Maintainability
    maintainability_index: float = 100.0
    mi_rank: str = 'A'
    
    # Halstead
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    halstead_bugs: float = 0.0
    
    # Structure
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    avg_function_length: float = 0.0
    max_function_length: int = 0
    
    # Documentation
    docstring_coverage: float = 0.0
    
    # Metadata
    metric_id: Optional[int] = None
    analysis_id: Optional[int] = None
    computed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data['computed_at']:
            data['computed_at'] = data['computed_at'].isoformat()
        return data
    
    @classmethod
    def from_parser_result(cls, file_id: int, metrics: Dict[str, Any]) -> 'MetricRecord':
        """Create MetricRecord from parser output"""
        return cls(
            file_id=file_id,
            loc=safe_get(metrics, 'loc', 0, int),
            sloc=safe_get(metrics, 'sloc', 0, int),
            blank_lines=safe_get(metrics, 'blank_lines', 0, int),
            comment_lines=safe_get(metrics, 'comment_lines', 0, int),
            comment_density=safe_get(metrics, 'comment_density', 0.0, float),
            cyclomatic_complexity=safe_get(metrics, 'cyclomatic_complexity', 0.0, float),
            max_complexity=safe_get(metrics, 'max_complexity', 0, int),
            avg_complexity=safe_get(metrics, 'avg_complexity', 0.0, float),
            complexity_rank=safe_get(metrics, 'complexity_rank', 'A'),
            maintainability_index=safe_get(metrics, 'maintainability_index', 100.0, float),
            mi_rank=safe_get(metrics, 'mi_rank', 'A'),
            halstead_volume=safe_get(metrics, 'halstead_volume', 0.0, float),
            halstead_difficulty=safe_get(metrics, 'halstead_difficulty', 0.0, float),
            halstead_effort=safe_get(metrics, 'halstead_effort', 0.0, float),
            halstead_bugs=safe_get(metrics, 'halstead_bugs', 0.0, float),
            function_count=safe_get(metrics, 'function_count', 0, int),
            class_count=safe_get(metrics, 'class_count', 0, int),
            import_count=safe_get(metrics, 'import_count', 0, int),
            avg_function_length=safe_get(metrics, 'avg_function_length', 0.0, float),
            max_function_length=safe_get(metrics, 'max_function_length', 0, int),
            docstring_coverage=safe_get(metrics, 'docstring_coverage', 0.0, float)
        )
    
    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> 'MetricRecord':
        """Create MetricRecord from database row"""
        data = dict(zip(columns, row))
        return cls(
            metric_id=safe_get(data, 'metric_id', cast_type=int),
            file_id=safe_get(data, 'file_id', 0, int),
            analysis_id=safe_get(data, 'analysis_id', cast_type=int),
            loc=safe_get(data, 'loc', 0, int),
            sloc=safe_get(data, 'sloc', 0, int),
            blank_lines=safe_get(data, 'blank_lines', 0, int),
            comment_lines=safe_get(data, 'comment_lines', 0, int),
            comment_density=safe_get(data, 'comment_density', 0.0, float),
            cyclomatic_complexity=safe_get(data, 'cyclomatic_complexity', 0.0, float),
            max_complexity=safe_get(data, 'max_complexity', 0, int),
            avg_complexity=safe_get(data, 'avg_complexity', 0.0, float),
            complexity_rank=safe_get(data, 'complexity_rank', 'A'),
            maintainability_index=safe_get(data, 'maintainability_index', 100.0, float),
            mi_rank=safe_get(data, 'mi_rank', 'A'),
            halstead_volume=safe_get(data, 'halstead_volume', 0.0, float),
            halstead_difficulty=safe_get(data, 'halstead_difficulty', 0.0, float),
            halstead_effort=safe_get(data, 'halstead_effort', 0.0, float),
            halstead_bugs=safe_get(data, 'halstead_bugs', 0.0, float),
            function_count=safe_get(data, 'function_count', 0, int),
            class_count=safe_get(data, 'class_count', 0, int),
            import_count=safe_get(data, 'import_count', 0, int),
            avg_function_length=safe_get(data, 'avg_function_length', 0.0, float),
            max_function_length=safe_get(data, 'max_function_length', 0, int),
            docstring_coverage=safe_get(data, 'docstring_coverage', 0.0, float),
            computed_at=parse_datetime(data.get('computed_at'))
        )


@dataclass
class DDIRecord:
    """DDI calculation record"""
    file_id: int
    
    # DDI Score
    ddi_score: float = 0.0
    risk_level: str = 'low'
    
    # Component scores
    decay_rate_score: float = 0.0
    entropy_score: float = 0.0
    volatility_score: float = 0.0
    frequency_score: float = 0.0
    
    # Raw values
    decay_rate: float = 0.0
    contributor_entropy: float = 0.0
    volatility: float = 0.0
    commit_frequency: float = 0.0
    
    # Context
    contributor_count: int = 0
    total_commits: int = 0
    age_days: int = 0
    days_since_last_change: int = 0
    
    # Prediction
    confidence: float = 0.0
    predicted_issue_probability: float = 0.0
    recommended_action: Optional[str] = None
    
    # Metadata
    ddi_id: Optional[int] = None
    analysis_id: Optional[int] = None
    computed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data['computed_at']:
            data['computed_at'] = data['computed_at'].isoformat()
        return data
    
    @classmethod
    def from_ddi_result(cls, file_id: int, result: Any) -> 'DDIRecord':
        """Create DDIRecord from DDICalculator result"""
        if hasattr(result, 'ddi_score'):
            # DDIResult object
            risk = result.risk_level
            if hasattr(risk, 'value'):
                risk = risk.value
            return cls(
                file_id=file_id,
                ddi_score=float(result.ddi_score),
                risk_level=str(risk),
                decay_rate_score=float(result.decay_rate_score),
                entropy_score=float(result.entropy_score),
                volatility_score=float(result.volatility_score),
                frequency_score=float(result.frequency_score),
                decay_rate=float(result.decay_rate),
                contributor_entropy=float(result.contributor_entropy),
                volatility=float(result.volatility),
                commit_frequency=float(result.commit_frequency),
                contributor_count=int(result.contributor_count),
                total_commits=int(result.total_commits),
                age_days=int(result.age_days),
                days_since_last_change=int(result.days_since_last_change),
                confidence=float(result.confidence),
                predicted_issue_probability=float(result.predicted_issue_probability),
                recommended_action=str(result.recommended_action) if result.recommended_action else None
            )
        elif isinstance(result, dict):
            return cls(
                file_id=file_id,
                ddi_score=safe_get(result, 'ddi_score', 0.0, float),
                risk_level=safe_get(result, 'risk_level', 'low'),
                decay_rate_score=safe_get(result, 'decay_rate_score', 0.0, float),
                entropy_score=safe_get(result, 'entropy_score', 0.0, float),
                volatility_score=safe_get(result, 'volatility_score', 0.0, float),
                frequency_score=safe_get(result, 'frequency_score', 0.0, float),
                decay_rate=safe_get(result, 'decay_rate', 0.0, float),
                contributor_entropy=safe_get(result, 'contributor_entropy', 0.0, float),
                volatility=safe_get(result, 'volatility', 0.0, float),
                commit_frequency=safe_get(result, 'commit_frequency', 0.0, float),
                contributor_count=safe_get(result, 'contributor_count', 0, int),
                total_commits=safe_get(result, 'total_commits', 0, int),
                age_days=safe_get(result, 'age_days', 0, int),
                days_since_last_change=safe_get(result, 'days_since_last_change', 0, int),
                confidence=safe_get(result, 'confidence', 0.0, float),
                predicted_issue_probability=safe_get(result, 'predicted_issue_probability', 0.0, float),
                recommended_action=safe_get(result, 'recommended_action')
            )
        else:
            return cls(file_id=file_id)
    
    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> 'DDIRecord':
        """Create DDIRecord from database row"""
        data = dict(zip(columns, row))
        return cls(
            ddi_id=safe_get(data, 'ddi_id', cast_type=int),
            file_id=safe_get(data, 'file_id', 0, int),
            analysis_id=safe_get(data, 'analysis_id', cast_type=int),
            ddi_score=safe_get(data, 'ddi_score', 0.0, float),
            risk_level=safe_get(data, 'risk_level', 'low'),
            decay_rate_score=safe_get(data, 'decay_rate_score', 0.0, float),
            entropy_score=safe_get(data, 'entropy_score', 0.0, float),
            volatility_score=safe_get(data, 'volatility_score', 0.0, float),
            frequency_score=safe_get(data, 'frequency_score', 0.0, float),
            decay_rate=safe_get(data, 'decay_rate', 0.0, float),
            contributor_entropy=safe_get(data, 'contributor_entropy', 0.0, float),
            volatility=safe_get(data, 'volatility', 0.0, float),
            commit_frequency=safe_get(data, 'commit_frequency', 0.0, float),
            contributor_count=safe_get(data, 'contributor_count', 0, int),
            total_commits=safe_get(data, 'total_commits', 0, int),
            age_days=safe_get(data, 'age_days', 0, int),
            days_since_last_change=safe_get(data, 'days_since_last_change', 0, int),
            confidence=safe_get(data, 'confidence', 0.0, float),
            predicted_issue_probability=safe_get(data, 'predicted_issue_probability', 0.0, float),
            recommended_action=safe_get(data, 'recommended_action'),
            computed_at=parse_datetime(data.get('computed_at'))
        )


@dataclass
class AnalysisRecord:
    """Analysis run record"""
    project_id: int
    
    # Summary metrics
    total_files: int = 0
    total_sloc: int = 0
    avg_maintainability_index: float = 0.0
    avg_complexity: float = 0.0
    avg_ddi_score: float = 0.0
    
    # Health
    overall_health_score: float = 100.0
    overall_status: str = 'good'
    
    # Issue counts
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    
    # Metadata
    analysis_id: Optional[int] = None
    analyzer_version: str = '1.0.0'
    run_duration_seconds: float = 0.0
    notes: Optional[str] = None
    run_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data['run_at']:
            data['run_at'] = data['run_at'].isoformat()
        return data
    
    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> 'AnalysisRecord':
        """Create AnalysisRecord from database row"""
        data = dict(zip(columns, row))
        return cls(
            analysis_id=safe_get(data, 'analysis_id', cast_type=int),
            project_id=safe_get(data, 'project_id', 0, int),
            total_files=safe_get(data, 'total_files', 0, int),
            total_sloc=safe_get(data, 'total_sloc', 0, int),
            avg_maintainability_index=safe_get(data, 'avg_maintainability_index', 0.0, float),
            avg_complexity=safe_get(data, 'avg_complexity', 0.0, float),
            avg_ddi_score=safe_get(data, 'avg_ddi_score', 0.0, float),
            overall_health_score=safe_get(data, 'overall_health_score', 100.0, float),
            overall_status=safe_get(data, 'overall_status', 'good'),
            critical_issues=safe_get(data, 'critical_issues', 0, int),
            high_issues=safe_get(data, 'high_issues', 0, int),
            medium_issues=safe_get(data, 'medium_issues', 0, int),
            low_issues=safe_get(data, 'low_issues', 0, int),
            analyzer_version=safe_get(data, 'analyzer_version', '1.0.0'),
            run_duration_seconds=safe_get(data, 'run_duration_seconds', 0.0, float),
            notes=safe_get(data, 'notes'),
            run_at=parse_datetime(data.get('run_at'))
        )


@dataclass
class RecommendationRecord:
    """Recommendation record"""
    analysis_id: int
    title: str
    
    # Details
    message: Optional[str] = None
    severity: str = 'medium'
    category: str = 'general'
    
    # Context
    file_id: Optional[int] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    
    # Action
    action: Optional[str] = None
    effort_estimate: str = 'medium'
    impact: str = 'medium'
    priority_score: float = 0.0
    
    # Location
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    
    # Status
    status: str = 'open'
    resolved_at: Optional[datetime] = None
    
    # Metadata
    rec_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data['created_at']:
            data['created_at'] = data['created_at'].isoformat()
        if data['resolved_at']:
            data['resolved_at'] = data['resolved_at'].isoformat()
        return data
    
    @classmethod
    def from_recommendation(cls, analysis_id: int, rec: Any, file_id: Optional[int] = None) -> 'RecommendationRecord':
        """Create from Recommendation object"""
        if hasattr(rec, 'title'):
            severity = rec.severity
            if hasattr(severity, 'value'):
                severity = severity.value
            category = rec.category
            if hasattr(category, 'value'):
                category = category.value
            
            return cls(
                analysis_id=analysis_id,
                file_id=file_id,
                title=str(rec.title),
                message=str(rec.message) if rec.message else None,
                severity=str(severity),
                category=str(category),
                metric_name=str(rec.metric_name) if rec.metric_name else None,
                metric_value=float(rec.metric_value) if rec.metric_value is not None else None,
                threshold=float(rec.threshold) if rec.threshold is not None else None,
                action=str(rec.action) if rec.action else None,
                effort_estimate=str(rec.effort_estimate),
                impact=str(rec.impact),
                priority_score=float(rec.priority_score),
                line_start=int(rec.line_start) if rec.line_start else None,
                line_end=int(rec.line_end) if rec.line_end else None,
                function_name=str(rec.function_name) if rec.function_name else None,
                class_name=str(rec.class_name) if rec.class_name else None
            )
        elif isinstance(rec, dict):
            return cls(
                analysis_id=analysis_id,
                file_id=file_id or safe_get(rec, 'file_id', cast_type=int),
                title=safe_get(rec, 'title', ''),
                message=safe_get(rec, 'message'),
                severity=safe_get(rec, 'severity', 'medium'),
                category=safe_get(rec, 'category', 'general'),
                metric_name=safe_get(rec, 'metric_name'),
                metric_value=safe_get(rec, 'metric_value', cast_type=float),
                threshold=safe_get(rec, 'threshold', cast_type=float),
                action=safe_get(rec, 'action'),
                effort_estimate=safe_get(rec, 'effort_estimate', 'medium'),
                impact=safe_get(rec, 'impact', 'medium'),
                priority_score=safe_get(rec, 'priority_score', 0.0, float),
                line_start=safe_get(rec, 'line_start', cast_type=int),
                line_end=safe_get(rec, 'line_end', cast_type=int),
                function_name=safe_get(rec, 'function_name'),
                class_name=safe_get(rec, 'class_name')
            )
        else:
            return cls(analysis_id=analysis_id, title='Unknown')
    
    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> 'RecommendationRecord':
        """Create from database row"""
        data = dict(zip(columns, row))
        return cls(
            rec_id=safe_get(data, 'rec_id', cast_type=int),
            analysis_id=safe_get(data, 'analysis_id', 0, int),
            file_id=safe_get(data, 'file_id', cast_type=int),
            title=safe_get(data, 'title', ''),
            message=safe_get(data, 'message'),
            severity=safe_get(data, 'severity', 'medium'),
            category=safe_get(data, 'category', 'general'),
            metric_name=safe_get(data, 'metric_name'),
            metric_value=safe_get(data, 'metric_value', cast_type=float),
            threshold=safe_get(data, 'threshold', cast_type=float),
            action=safe_get(data, 'action'),
            effort_estimate=safe_get(data, 'effort_estimate', 'medium'),
            impact=safe_get(data, 'impact', 'medium'),
            priority_score=safe_get(data, 'priority_score', 0.0, float),
            line_start=safe_get(data, 'line_start', cast_type=int),
            line_end=safe_get(data, 'line_end', cast_type=int),
            function_name=safe_get(data, 'function_name'),
            class_name=safe_get(data, 'class_name'),
            status=safe_get(data, 'status', 'open'),
            resolved_at=parse_datetime(data.get('resolved_at')),
            created_at=parse_datetime(data.get('created_at'))
        )


@dataclass
class MetricHistoryRecord:
    """Historical metric snapshot for trend analysis"""
    file_id: int
    maintainability_index: Optional[float] = None
    cyclomatic_complexity: Optional[float] = None
    sloc: Optional[int] = None
    comment_density: Optional[float] = None
    ddi_score: Optional[float] = None
    history_id: Optional[int] = None
    snapshot_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data['snapshot_at']:
            data['snapshot_at'] = data['snapshot_at'].isoformat()
        return data
    
    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> 'MetricHistoryRecord':
        """Create from database row"""
        data = dict(zip(columns, row))
        return cls(
            history_id=safe_get(data, 'history_id', cast_type=int),
            file_id=safe_get(data, 'file_id', 0, int),
            maintainability_index=safe_get(data, 'maintainability_index', cast_type=float),
            cyclomatic_complexity=safe_get(data, 'cyclomatic_complexity', cast_type=float),
            sloc=safe_get(data, 'sloc', cast_type=int),
            comment_density=safe_get(data, 'comment_density', cast_type=float),
            ddi_score=safe_get(data, 'ddi_score', cast_type=float),
            snapshot_at=parse_datetime(data.get('snapshot_at'))
        )