"""
DDI (Developer-Centric Decay Index) Calculator for SQA-AI

DDI = (DecayRate × W1) + (Entropy × W2) + (Volatility × W3) + (Complexity × W4)

FIXES APPLIED:
- Changed 4th component from Frequency to Cyclomatic Complexity (per paper)
- Kept frequency as secondary indicator
- Updated volatility to use std_dev from git_analyzer
- Fixed indentation in _calculate_decay_rate method
"""

import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricSnapshot:
    timestamp: datetime
    maintainability_index: float
    cyclomatic_complexity: float
    comment_density: float
    loc: int

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'maintainability_index': self.maintainability_index,
            'cyclomatic_complexity': self.cyclomatic_complexity,
            'comment_density': self.comment_density,
            'loc': self.loc
        }


@dataclass
class DDIResult:
    file_path: str
    ddi_score: float
    risk_level: RiskLevel

    # Component scores (all 0-100)
    decay_rate_score: float
    entropy_score: float
    volatility_score: float
    complexity_score: float  # FIXED: renamed from frequency_score

    # Raw values
    decay_rate: float
    contributor_entropy: float
    volatility: float
    cyclomatic_complexity: float  # FIXED: added
    commit_frequency: float  # Kept as secondary metric

    # Context
    contributor_count: int
    total_commits: int
    age_days: int
    days_since_last_change: int

    # Prediction
    confidence: float
    predicted_issue_probability: float
    recommended_action: str

    # Legacy support - keep frequency_score as alias
    @property
    def frequency_score(self) -> float:
        return self.complexity_score

    calculated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'file_path': self.file_path,
            'ddi_score': round(self.ddi_score, 2),
            'risk_level': self.risk_level.value,
            'components': {
                'decay_rate_score': round(self.decay_rate_score, 2),
                'entropy_score': round(self.entropy_score, 2),
                'volatility_score': round(self.volatility_score, 2),
                'complexity_score': round(self.complexity_score, 2),
                # Legacy support
                'frequency_score': round(self.complexity_score, 2),
            },
            'raw_values': {
                'decay_rate': round(self.decay_rate, 4),
                'contributor_entropy': round(self.contributor_entropy, 4),
                'volatility': round(self.volatility, 4),
                'cyclomatic_complexity': round(self.cyclomatic_complexity, 4),
                'commit_frequency': round(self.commit_frequency, 4),
            },
            'context': {
                'contributor_count': self.contributor_count,
                'total_commits': self.total_commits,
                'age_days': self.age_days,
                'days_since_last_change': self.days_since_last_change,
            },
            'prediction': {
                'confidence': round(self.confidence, 2),
                'issue_probability': round(self.predicted_issue_probability, 2),
                'recommended_action': self.recommended_action,
            },
            'calculated_at': self.calculated_at.isoformat(),
        }

    def get_summary(self) -> str:
        return (
            f"{self.file_path}: DDI={self.ddi_score:.1f} ({self.risk_level.value.upper()}) - "
            f"{self.contributor_count} contributors, {self.total_commits} commits, "
            f"{self.predicted_issue_probability:.0f}% issue probability"
        )


class DDICalculator:
    """
    DDI Calculator with paper-compliant formula
    
    DDI = (Decay × 0.35) + (Entropy × 0.30) + (Volatility × 0.20) + (CC × 0.15)
    """
    
    # FIXED: Updated weights to match paper (CC instead of frequency)
    DEFAULT_WEIGHTS = {
        'decay_rate': 0.35,
        'entropy': 0.30,
        'volatility': 0.20,
        'complexity': 0.15  # FIXED: was 'frequency'
    }

    RISK_THRESHOLDS = {
        'low': 25,
        'medium': 50,
        'high': 75,
        'critical': 90
    }

    MAX_HISTORY_PER_FILE = 100

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        risk_thresholds: Optional[Dict[str, int]] = None
    ):
        self.weights = self._validate_weights(weights or self.DEFAULT_WEIGHTS.copy())
        self.risk_thresholds = risk_thresholds or self.RISK_THRESHOLDS.copy()

        self._logger = None
        self._init_logger()

        self._metric_history: Dict[str, List[MetricSnapshot]] = {}

    def _validate_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        required_keys = {'decay_rate', 'entropy', 'volatility', 'complexity'}
        
        # Support legacy 'frequency' key
        if 'frequency' in weights and 'complexity' not in weights:
            weights['complexity'] = weights.pop('frequency')

        for key in required_keys:
            if key not in weights:
                weights[key] = self.DEFAULT_WEIGHTS.get(key, 0.25)

        for key in weights:
            if weights[key] < 0:
                weights[key] = 0.0

        weight_sum = sum(weights.values())
        if weight_sum <= 0:
            return self.DEFAULT_WEIGHTS.copy()

        if not 0.99 <= weight_sum <= 1.01:
            for key in weights:
                weights[key] /= weight_sum

        return weights

    def _init_logger(self) -> None:
        try:
            from utils.logger import get_logger
            self._logger = get_logger(__name__)
        except ImportError:
            self._logger = None

    def _log(self, level: str, message: str) -> None:
        if self._logger:
            getattr(self._logger, level)(message)

    def _safe_value(self, value: Any, default: float = 0.0, min_val: Optional[float] = None, max_val: Optional[float] = None) -> float:
        if value is None:
            return default
        try:
            f = float(value)
            if math.isnan(f) or math.isinf(f):
                return default
            if min_val is not None:
                f = max(min_val, f)
            if max_val is not None:
                f = min(max_val, f)
            return f
        except (TypeError, ValueError):
            return default

    def _safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        if denominator == 0:
            return default
        result = numerator / denominator
        if math.isnan(result) or math.isinf(result):
            return default
        return result

    def calculate_ddi(
        self,
        git_factors: Dict[str, Any],
        current_metrics: Optional[Dict[str, Any]] = None,
        historical_metrics: Optional[List[MetricSnapshot]] = None
    ) -> DDIResult:
        """
        Calculate DDI score using paper formula:
        DDI = (Decay × 0.35) + (Entropy × 0.30) + (Volatility × 0.20) + (CC × 0.15)
        """
        file_path = git_factors.get('file_path', 'unknown')

        # Extract git factors
        contributor_count = max(1, int(self._safe_value(git_factors.get('contributor_count'), 1)))
        total_commits = max(1, int(self._safe_value(git_factors.get('total_commits'), 1)))
        age_days = max(0, int(self._safe_value(git_factors.get('age_days'), 0)))
        days_since_last_change = max(0, int(self._safe_value(git_factors.get('days_since_last_change'), 0)))
        contributor_entropy = self._safe_value(git_factors.get('contributor_entropy'), 0, 0)
        commit_frequency = self._safe_value(git_factors.get('commit_frequency'), 0, 0)
        total_churn = max(0, int(self._safe_value(git_factors.get('total_churn'), 0)))
        
        # FIXED: Use std_dev if available, fall back to sqrt of variance
        volatility_raw = self._safe_value(git_factors.get('commit_gap_std_dev'), 0, 0)
        if volatility_raw == 0:
            variance = self._safe_value(git_factors.get('commit_gap_variance'), 0, 0)
            volatility_raw = math.sqrt(variance) if variance > 0 else 0

        # Calculate component scores
        decay_rate, decay_score = self._calculate_decay_rate(
            file_path, current_metrics, historical_metrics, total_churn, age_days
        )

        entropy_score = self._calculate_entropy_score(
            contributor_entropy, contributor_count, total_commits
        )

        volatility_score = self._calculate_volatility_score(
            volatility_raw, days_since_last_change
        )

        # FIXED: Calculate complexity score from CC (not frequency)
        complexity_score, cc_raw = self._calculate_complexity_score(current_metrics)

        # Clamp all scores
        decay_score = self._safe_value(decay_score, 0, 0, 100)
        entropy_score = self._safe_value(entropy_score, 0, 0, 100)
        volatility_score = self._safe_value(volatility_score, 0, 0, 100)
        complexity_score = self._safe_value(complexity_score, 0, 0, 100)

        # FIXED: DDI formula now uses complexity (CC) instead of frequency
        ddi_score = (
            decay_score * self.weights['decay_rate'] +
            entropy_score * self.weights['entropy'] +
            volatility_score * self.weights['volatility'] +
            complexity_score * self.weights['complexity']
        )
        ddi_score = max(0, min(100, ddi_score))

        risk_level = self._get_risk_level(ddi_score)

        confidence = self._calculate_confidence(
            total_commits, age_days, historical_metrics
        )

        issue_probability = self._predict_issue_probability(
            ddi_score, confidence, days_since_last_change
        )

        recommendation = self._generate_recommendation(
            ddi_score, risk_level, decay_score, entropy_score,
            volatility_score, complexity_score
        )

        result = DDIResult(
            file_path=file_path,
            ddi_score=ddi_score,
            risk_level=risk_level,

            decay_rate_score=decay_score,
            entropy_score=entropy_score,
            volatility_score=volatility_score,
            complexity_score=complexity_score,

            decay_rate=decay_rate,
            contributor_entropy=contributor_entropy,
            volatility=volatility_raw,
            cyclomatic_complexity=cc_raw,
            commit_frequency=commit_frequency,

            contributor_count=contributor_count,
            total_commits=total_commits,
            age_days=age_days,
            days_since_last_change=days_since_last_change,

            confidence=confidence,
            predicted_issue_probability=issue_probability,
            recommended_action=recommendation
        )

        self._log('debug', f"DDI calculated: {result.get_summary()}")
        return result

    def _calculate_decay_rate(
        self,
        file_path: str,
        current_metrics: Optional[Dict[str, Any]],
        historical_metrics: Optional[List[MetricSnapshot]],
        total_churn: int,
        age_days: int
    ) -> Tuple[float, float]:
        """Calculate decay rate from historical MI changes or estimate from current state."""
        
        # If we have historical metrics, calculate actual decay
        if historical_metrics and len(historical_metrics) >= 2:
            sorted_metrics = sorted(historical_metrics, key=lambda m: m.timestamp)
            first = sorted_metrics[0]
            last = sorted_metrics[-1]

            mi_change = first.maintainability_index - last.maintainability_index
            time_delta = (last.timestamp - first.timestamp).days
            time_span_months = max(time_delta / 30.0, 1.0)

            decay_rate = self._safe_divide(mi_change, time_span_months, 0)
            # Only positive decay (quality dropping) counts
            if decay_rate <= 0:
                return 0.0, 0.0
            decay_score = min(100, max(0, decay_rate * 10))
            return decay_rate, decay_score

        # No historical data - use conservative static estimate
        mi_now = 65.0  # Assume decent quality by default
        cc_now = 10.0  # Assume moderate complexity
        
        if current_metrics:
            mi_now = self._safe_value(current_metrics.get('maintainability_index'), 65, 0, 100)
            cc_now = self._safe_value(
                current_metrics.get('avg_complexity', current_metrics.get('cyclomatic_complexity')),
                10, 0
            )

        # Calculate static quality penalty (less aggressive)
        decay_score = 0.0
        
        # MI penalty: only if MI < 50 (truly poor)
        if mi_now < 50:
            mi_penalty = ((50.0 - mi_now) / 50.0) * 40.0  # Max 40 points
            decay_score += mi_penalty
        elif mi_now < 65:
            mi_penalty = ((65.0 - mi_now) / 65.0) * 15.0  # Max 15 points
            decay_score += mi_penalty
        
        # CC penalty: only if CC > 15 (truly complex)
        if cc_now > 25:
            cc_penalty = min(30, (cc_now - 25) * 1.5)  # Max 30 points
            decay_score += cc_penalty
        elif cc_now > 15:
            cc_penalty = min(15, (cc_now - 15) * 1.0)  # Max 15 points
            decay_score += cc_penalty

        # Churn penalty: only for very high churn
        if age_days > 30 and total_churn > 500:
            months = max(age_days / 30.0, 1.0)
            churn_rate = total_churn / months
            churn_penalty = min(20, churn_rate / 50.0)  # Max 20 points
            decay_score += churn_penalty

        # Cap at 70 for files without historical data
        decay_score = min(70, decay_score)
        decay_rate = decay_score / 100.0

        return decay_rate, max(0.0, decay_score)

    def _calculate_entropy_score(
        self,
        contributor_entropy: float,
        contributor_count: int,
        total_commits: int
    ) -> float:
        """
        Calculate entropy score from Shannon entropy
        
        Shannon entropy is in bits (0 to ~4 for typical projects)
        We normalize to 0-100 scale
        """
        # Shannon entropy typically ranges 0-4 bits for code files
        # 0 = single author, ~2.5 = well-distributed, 4+ = chaotic
        
        # Normalize: entropy of 2.5 bits = score of 50
        entropy_score = (contributor_entropy / 2.5) * 50
        
        # Add penalty for high contributor count
        if contributor_count > 5:
            contributor_penalty = min(30, (contributor_count - 5) * 5)
            entropy_score += contributor_penalty

        # Reduce score if very few commits (not enough data)
        if total_commits < 5:
            entropy_score *= 0.5

        return max(0, min(100, entropy_score))

    def _calculate_volatility_score(
        self,
        volatility_std_dev: float,
        days_since_last_change: int
    ) -> float:
        """
        Calculate volatility score from std deviation of commit gaps
        
        FIXED: Now expects std_dev (not variance)
        """
        # Normalize std_dev: 30 days std_dev = score of 50
        volatility_score = (volatility_std_dev / 30.0) * 50
        
        # Add penalty for stale files
        if days_since_last_change > 180:
            stale_penalty = min(30, self._safe_divide(days_since_last_change - 180, 180, 0) * 30)
            volatility_score += stale_penalty
        elif days_since_last_change > 90:
            stale_penalty = min(15, self._safe_divide(days_since_last_change - 90, 90, 0) * 15)
            volatility_score += stale_penalty

        return max(0, min(100, volatility_score))

    def _calculate_complexity_score(
        self,
        current_metrics: Optional[Dict[str, Any]]
    ) -> Tuple[float, float]:
        """
        FIXED: Calculate complexity score from Cyclomatic Complexity
        
        This replaces the old frequency_score calculation.
        CC is normalized to 0-100 scale where higher CC = higher risk
        """
        if not current_metrics:
            return 50.0, 0.0  # Default middle score, 0 CC
        
        # Get CC from metrics (prefer avg, fall back to total)
        cc = self._safe_value(
            current_metrics.get('avg_complexity',
            current_metrics.get('cyclomatic_complexity')), 
            1, 0
        )
        
        # Normalize CC to 0-100 scale
        # CC 1-5 = Low risk (0-25)
        # CC 5-15 = Medium risk (25-75)  
        # CC 15+ = High risk (75-100)
        if cc <= 5:
            complexity_score = cc * 5  # 0-25
        elif cc <= 15:
            complexity_score = 25 + (cc - 5) * 5  # 25-75
        else:
            complexity_score = min(100, 75 + (cc - 15) * 2.5)  # 75-100
        
        return complexity_score, cc

    def _get_risk_level(self, ddi_score: float) -> RiskLevel:
        if ddi_score >= self.risk_thresholds['critical']:
            return RiskLevel.CRITICAL
        elif ddi_score >= self.risk_thresholds['high']:
            return RiskLevel.HIGH
        elif ddi_score >= self.risk_thresholds['medium']:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _calculate_confidence(
        self,
        total_commits: int,
        age_days: int,
        historical_metrics: Optional[List[MetricSnapshot]]
    ) -> float:
        confidence = 40.0

        if total_commits >= 50:
            confidence += 25
        elif total_commits >= 20:
            confidence += 20
        elif total_commits >= 10:
            confidence += 10
        elif total_commits >= 5:
            confidence += 5
        elif total_commits < 3:
            confidence -= 15

        if age_days >= 365:
            confidence += 20
        elif age_days >= 180:
            confidence += 15
        elif age_days >= 90:
            confidence += 10
        elif age_days >= 30:
            confidence += 5
        elif age_days < 14:
            confidence -= 10

        if historical_metrics:
            if len(historical_metrics) >= 10:
                confidence += 15
            elif len(historical_metrics) >= 5:
                confidence += 10
            elif len(historical_metrics) >= 2:
                confidence += 5

        return max(0, min(100, confidence))

    def _predict_issue_probability(
        self,
        ddi_score: float,
        confidence: float,
        days_since_last_change: int
    ) -> float:
        base_probability = ddi_score * 0.85

        if days_since_last_change > 180:
            base_probability = min(100, base_probability + 10)
        elif days_since_last_change > 90:
            base_probability = min(100, base_probability + 5)

        baseline = 30.0
        confidence_factor = confidence / 100.0
        adjusted = (base_probability * confidence_factor) + (baseline * (1 - confidence_factor))
        return max(0, min(100, adjusted))

    def _generate_recommendation(
        self,
        ddi_score: float,
        risk_level: RiskLevel,
        decay_score: float,
        entropy_score: float,
        volatility_score: float,
        complexity_score: float
    ) -> str:
        if risk_level == RiskLevel.LOW:
            return "No immediate action required. Continue regular maintenance."

        scores = {
            'decay': decay_score,
            'entropy': entropy_score,
            'volatility': volatility_score,
            'complexity': complexity_score
        }
        primary_issue = max(scores, key=scores.get)

        recommendations = {
            'decay': "Quality declining. Refactor to improve maintainability and reduce complexity.",
            'entropy': "Too many contributors. Assign clear ownership to reduce chaos.",
            'volatility': "Inconsistent maintenance. Establish regular review schedule.",
            'complexity': "High code complexity. Break down complex functions and simplify logic."
        }
        base = recommendations[primary_issue]

        if risk_level == RiskLevel.CRITICAL:
            return f"URGENT: {base} Immediate intervention recommended."
        elif risk_level == RiskLevel.HIGH:
            return f"HIGH PRIORITY: {base} Schedule remediation this sprint."
        else:
            return f"MODERATE: {base} Plan for upcoming maintenance."

    def record_metric_snapshot(
        self,
        file_path: str,
        metrics: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> None:
        if timestamp is None:
            timestamp = datetime.now()

        snapshot = MetricSnapshot(
            timestamp=timestamp,
            maintainability_index=self._safe_value(metrics.get('maintainability_index'), 50, 0, 100),
            cyclomatic_complexity=self._safe_value(metrics.get('cyclomatic_complexity'), 1, 0),
            comment_density=self._safe_value(metrics.get('comment_density'), 0, 0, 1),
            loc=max(0, int(self._safe_value(metrics.get('sloc', metrics.get('loc')), 0)))
        )

        if file_path not in self._metric_history:
            self._metric_history[file_path] = []

        self._metric_history[file_path].append(snapshot)

        if len(self._metric_history[file_path]) > self.MAX_HISTORY_PER_FILE:
            self._metric_history[file_path] = self._metric_history[file_path][-self.MAX_HISTORY_PER_FILE:]

    def get_metric_history(self, file_path: str) -> List[MetricSnapshot]:
        return self._metric_history.get(file_path, [])

    def __repr__(self) -> str:
        return f"DDICalculator(weights={self.weights})"
    