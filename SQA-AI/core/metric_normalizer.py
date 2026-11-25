"""
Metric Normalizer for SQA-AI
Normalizes raw metrics to 0-1 scale for consistent scoring
Supports multiple normalization strategies

Normalization Methods:
- Min-Max: Scale to [0, 1] based on observed range
- Z-Score: Standardize based on mean and std deviation
- Percentile: Rank-based normalization
- Threshold: Binary/stepped based on configured thresholds
"""

import math
import json
from collections import deque
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class NormalizationMethod(Enum):
    """Available normalization methods"""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    PERCENTILE = "percentile"
    THRESHOLD = "threshold"
    INVERSE = "inverse"


@dataclass
class MetricBounds:
    """Define bounds for a metric"""
    min_value: float
    max_value: float
    ideal_value: Optional[float] = None
    is_inverse: bool = False
    
    def __post_init__(self):
        if self.ideal_value is None:
            self.ideal_value = self.min_value if self.is_inverse else self.max_value
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MetricBounds':
        return cls(**data)


class MetricNormalizer:
    """
    Normalizes code quality metrics to consistent 0-1 scale
    Higher normalized value = better quality
    """
    
    # Maximum observations to keep per metric
    MAX_OBSERVATIONS = 1000
    
    # Default bounds for common metrics
    DEFAULT_BOUNDS: Dict[str, MetricBounds] = {
        # Complexity metrics (lower is better)
        'cyclomatic_complexity': MetricBounds(1, 50, 5, is_inverse=True),
        'avg_complexity': MetricBounds(1, 30, 5, is_inverse=True),
        'max_complexity': MetricBounds(1, 50, 10, is_inverse=True),
        
        # Maintainability (higher is better)
        'maintainability_index': MetricBounds(0, 100, 80, is_inverse=False),
        
        # Size metrics (moderate is often better)
        'loc': MetricBounds(1, 1000, 200, is_inverse=True),
        'sloc': MetricBounds(1, 800, 150, is_inverse=True),
        'function_count': MetricBounds(0, 50, 10, is_inverse=True),
        'class_count': MetricBounds(0, 20, 5, is_inverse=True),
        'avg_function_length': MetricBounds(1, 100, 20, is_inverse=True),
        'max_function_length': MetricBounds(1, 200, 30, is_inverse=True),
        'min_function_length': MetricBounds(1, 50, 5, is_inverse=False),
        
        # Documentation (higher is better)
        'comment_density': MetricBounds(0, 0.5, 0.2, is_inverse=False),
        'comment_lines': MetricBounds(0, 200, 50, is_inverse=False),
        'docstring_coverage': MetricBounds(0, 1, 0.8, is_inverse=False),
        
        # Halstead (lower is better for effort/bugs)
        'halstead_volume': MetricBounds(0, 10000, 500, is_inverse=True),
        'halstead_difficulty': MetricBounds(0, 50, 10, is_inverse=True),
        'halstead_effort': MetricBounds(0, 500000, 10000, is_inverse=True),
        'halstead_bugs': MetricBounds(0, 10, 0.5, is_inverse=True),
        'halstead_time': MetricBounds(0, 50000, 1000, is_inverse=True),
        
        # Coupling (lower is better)
        'import_count': MetricBounds(0, 30, 10, is_inverse=True),
        'coupling': MetricBounds(0, 20, 5, is_inverse=True),
        'cbo': MetricBounds(0, 20, 5, is_inverse=True),
        
        # Cohesion (lower LCOM is better)
        'lcom': MetricBounds(0, 1, 0.2, is_inverse=True),
        
        # Inheritance (lower is often better)
        'depth_of_inheritance': MetricBounds(0, 10, 2, is_inverse=True),
        
        # DDI components
        'decay_rate': MetricBounds(0, 100, 0, is_inverse=True),
        'entropy': MetricBounds(0, 1, 0.1, is_inverse=True),
        'volatility': MetricBounds(0, 100, 10, is_inverse=True),
        'ddi_score': MetricBounds(0, 100, 0, is_inverse=True),
        'contributor_count': MetricBounds(1, 20, 3, is_inverse=True),
        'commit_frequency': MetricBounds(0, 10, 1, is_inverse=True),
    }
    
    def __init__(self, custom_bounds: Optional[Dict[str, MetricBounds]] = None):
        """
        Initialize normalizer with optional custom bounds
        
        Args:
            custom_bounds: Override default bounds for specific metrics
        """
        self.bounds = {k: v for k, v in self.DEFAULT_BOUNDS.items()}
        if custom_bounds:
            self.bounds.update(custom_bounds)
        
        # Use deque for efficient fixed-size observation storage
        self._observed_values: Dict[str, deque] = {}
        self._logger = None
        self._init_logger()
    
    def _init_logger(self) -> None:
        """Initialize logger lazily"""
        try:
            from utils.logger import get_logger
            self._logger = get_logger(__name__)
        except ImportError:
            self._logger = None
    
    def _log(self, level: str, message: str) -> None:
        """Log message if logger available"""
        if self._logger:
            getattr(self._logger, level)(message)
    
    def _is_valid_number(self, value: Any) -> bool:
        """Check if value is a valid number (not None, NaN, or Inf)"""
        if value is None:
            return False
        if not isinstance(value, (int, float)):
            return False
        if isinstance(value, bool):
            return False
        if math.isnan(value) or math.isinf(value):
            return False
        return True
    
    def _sanitize_value(self, value: Any) -> float:
        """Convert value to valid float, returning 0 for invalid inputs"""
        if not self._is_valid_number(value):
            return 0.0
        return float(value)
    
    def normalize(
        self, 
        metric_name: str, 
        value: Any,
        method: NormalizationMethod = NormalizationMethod.MIN_MAX
    ) -> float:
        """
        Normalize a single metric value to 0-1 scale
        
        Args:
            metric_name: Name of the metric
            value: Raw metric value
            method: Normalization method to use
        
        Returns:
            Normalized value between 0 and 1
        """
        # Sanitize input
        value = self._sanitize_value(value)
        
        bounds = self.bounds.get(metric_name)
        
        if bounds is None:
            self._log('debug', f"Unknown metric: {metric_name}, using default normalization")
            return self._clamp(value / 100, 0, 1) if value <= 100 else 0.0
        
        if method == NormalizationMethod.MIN_MAX:
            normalized = self._min_max_normalize(value, bounds)
        elif method == NormalizationMethod.THRESHOLD:
            normalized = self._threshold_normalize(value, bounds)
        elif method == NormalizationMethod.PERCENTILE:
            normalized = self._percentile_normalize(metric_name, value, bounds)
        elif method == NormalizationMethod.Z_SCORE:
            normalized = self._z_score_normalize(metric_name, value, bounds)
        else:
            normalized = self._min_max_normalize(value, bounds)
        
        return self._clamp(normalized, 0.0, 1.0)
    
    def _min_max_normalize(self, value: float, bounds: MetricBounds) -> float:
        """
        Min-Max normalization to [0, 1]
        For inverse metrics, flips the scale so higher = better
        """
        min_val = bounds.min_value
        max_val = bounds.max_value
        
        # Clamp value to bounds
        value = self._clamp(value, min_val, max_val)
        
        # Normalize to 0-1
        if max_val == min_val:
            normalized = 1.0
        else:
            normalized = (value - min_val) / (max_val - min_val)
        
        # Inverse if lower is better
        if bounds.is_inverse:
            normalized = 1.0 - normalized
        
        return normalized
    
    def _threshold_normalize(self, value: float, bounds: MetricBounds) -> float:
        """
        Threshold-based normalization
        Returns score based on how close to ideal
        """
        ideal = bounds.ideal_value
        min_val = bounds.min_value
        max_val = bounds.max_value
        
        if bounds.is_inverse:
            if value <= ideal:
                return 1.0
            elif value >= max_val:
                return 0.0
            else:
                range_val = max_val - ideal
                if range_val == 0:
                    return 0.5
                return 1.0 - (value - ideal) / range_val
        else:
            if value >= ideal:
                return 1.0
            elif value <= min_val:
                return 0.0
            else:
                range_val = ideal - min_val
                if range_val == 0:
                    return 0.5
                return (value - min_val) / range_val
    
    def _percentile_normalize(
        self, 
        metric_name: str, 
        value: float, 
        bounds: MetricBounds
    ) -> float:
        """
        Percentile-based normalization using observed values
        Requires prior observations via record_observation()
        """
        observations = self._observed_values.get(metric_name)
        
        if observations is None or len(observations) < 10:
            return self._min_max_normalize(value, bounds)
        
        obs_list = list(observations)
        sorted_obs = sorted(obs_list)
        rank = sum(1 for v in sorted_obs if v <= value)
        percentile = rank / len(sorted_obs)
        
        if bounds.is_inverse:
            percentile = 1.0 - percentile
        
        return percentile
    
    def _z_score_normalize(
        self, 
        metric_name: str, 
        value: float, 
        bounds: MetricBounds
    ) -> float:
        """
        Z-score normalization using observed statistics
        Converts to 0-1 using sigmoid transformation
        """
        observations = self._observed_values.get(metric_name)
        
        if observations is None or len(observations) < 10:
            return self._min_max_normalize(value, bounds)
        
        obs_list = list(observations)
        n = len(obs_list)
        mean = sum(obs_list) / n
        variance = sum((x - mean) ** 2 for x in obs_list) / n
        std = math.sqrt(variance) if variance > 0 else 1.0
        
        if std == 0:
            return 0.5
        
        z_score = (value - mean) / std
        
        # Clamp z-score to prevent overflow in sigmoid
        z_score = self._clamp(z_score, -10, 10)
        
        # Convert z-score to 0-1 using sigmoid
        try:
            normalized = 1 / (1 + math.exp(-z_score))
        except OverflowError:
            normalized = 0.0 if z_score < 0 else 1.0
        
        if bounds.is_inverse:
            normalized = 1.0 - normalized
        
        return normalized
    
    def record_observation(self, metric_name: str, value: Any) -> None:
        """
        Record an observed value for percentile/z-score calculations
        
        Args:
            metric_name: Name of the metric
            value: Observed value
        """
        if not self._is_valid_number(value):
            return
        
        value = float(value)
        
        if metric_name not in self._observed_values:
            self._observed_values[metric_name] = deque(maxlen=self.MAX_OBSERVATIONS)
        
        self._observed_values[metric_name].append(value)
    
    def record_file_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Record all metrics from a file analysis
        
        Args:
            metrics: Dictionary of metric name -> value
        """
        for name, value in metrics.items():
            if self._is_valid_number(value):
                self.record_observation(name, value)
    
    def normalize_file_metrics(
        self, 
        metrics: Dict[str, Any],
        method: NormalizationMethod = NormalizationMethod.MIN_MAX
    ) -> Dict[str, float]:
        """
        Normalize all metrics from a file analysis
        
        Args:
            metrics: Dictionary of metric name -> raw value
            method: Normalization method to use
        
        Returns:
            Dictionary of metric name -> normalized value
        """
        normalized = {}
        
        for name, value in metrics.items():
            if self._is_valid_number(value):
                normalized[name] = self.normalize(name, value, method)
        
        return normalized
    
    def calculate_quality_score(
        self,
        normalized_metrics: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate weighted quality score from normalized metrics
        
        Args:
            normalized_metrics: Dict of metric name -> normalized value (0-1)
            weights: Optional custom weights
        
        Returns:
            Quality score from 0-100
        """
        if weights is None:
            weights = self._get_default_weights()
        
        # Validate weights
        weight_sum = sum(weights.values())
        if weight_sum <= 0:
            self._log('warning', "Invalid weights: sum is zero or negative")
            return 0.0
        
        score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in normalized_metrics:
                metric_value = normalized_metrics[metric]
                if self._is_valid_number(metric_value):
                    score += metric_value * weight
                    total_weight += weight
        
        if total_weight <= 0:
            return 0.0
        
        # Normalize by actual weights used
        score = score / total_weight
        
        return round(self._clamp(score * 100, 0, 100), 2)
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default weights for quality scoring"""
        return {
            'maintainability_index': 0.30,
            'avg_complexity': 0.20,
            'comment_density': 0.10,
            'avg_function_length': 0.10,
            'import_count': 0.10,
            'halstead_bugs': 0.10,
            'max_complexity': 0.10
        }
    
    def get_metric_grade(self, metric_name: str, value: Any) -> str:
        """
        Get letter grade for a metric value
        
        Args:
            metric_name: Name of the metric
            value: Raw metric value
        
        Returns:
            Letter grade A-F
        """
        if not self._is_valid_number(value):
            return 'N/A'
        
        normalized = self.normalize(metric_name, value)
        
        if normalized >= 0.9:
            return 'A'
        elif normalized >= 0.75:
            return 'B'
        elif normalized >= 0.5:
            return 'C'
        elif normalized >= 0.25:
            return 'D'
        else:
            return 'F'
    
    def get_metric_status(self, metric_name: str, value: Any) -> str:
        """
        Get status label for a metric value
        
        Args:
            metric_name: Name of the metric
            value: Raw metric value
        
        Returns:
            Status string: 'good', 'moderate', 'poor', 'critical', or 'unknown'
        """
        if not self._is_valid_number(value):
            return 'unknown'
        
        normalized = self.normalize(metric_name, value)
        
        if normalized >= 0.75:
            return 'good'
        elif normalized >= 0.5:
            return 'moderate'
        elif normalized >= 0.25:
            return 'poor'
        else:
            return 'critical'
    
    def compare_to_baseline(
        self,
        current: Dict[str, float],
        baseline: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare current metrics to a baseline
        
        Args:
            current: Current normalized metrics
            baseline: Baseline normalized metrics to compare against
        
        Returns:
            Comparison results with delta and direction
        """
        comparison = {}
        
        for metric in set(current.keys()) | set(baseline.keys()):
            curr_val = current.get(metric, 0)
            base_val = baseline.get(metric, 0)
            
            if not self._is_valid_number(curr_val):
                curr_val = 0
            if not self._is_valid_number(base_val):
                base_val = 0
            
            delta = curr_val - base_val
            
            if delta > 0.05:
                direction = 'improved'
            elif delta < -0.05:
                direction = 'degraded'
            else:
                direction = 'stable'
            
            comparison[metric] = {
                'current': round(curr_val, 4),
                'baseline': round(base_val, 4),
                'delta': round(delta, 4),
                'delta_percent': round(delta * 100, 2),
                'direction': direction
            }
        
        return comparison
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value to range"""
        if not self._is_valid_number(value):
            return min_val
        return max(min_val, min(max_val, value))
    
    def get_bounds(self, metric_name: str) -> Optional[MetricBounds]:
        """Get bounds for a metric"""
        return self.bounds.get(metric_name)
    
    def set_bounds(self, metric_name: str, bounds: MetricBounds) -> None:
        """Set custom bounds for a metric"""
        self.bounds[metric_name] = bounds
    
    def reset_observations(self) -> None:
        """Clear all recorded observations"""
        self._observed_values.clear()
    
    def get_statistics(self, metric_name: str) -> Optional[Dict[str, float]]:
        """
        Get statistics for observed values of a metric
        
        Returns:
            Dict with mean, std, min, max, count or None if no observations
        """
        observations = self._observed_values.get(metric_name)
        
        if not observations:
            return None
        
        obs_list = list(observations)
        n = len(obs_list)
        mean = sum(obs_list) / n
        variance = sum((x - mean) ** 2 for x in obs_list) / n
        std = math.sqrt(variance)
        
        return {
            'mean': round(mean, 4),
            'std': round(std, 4),
            'min': round(min(obs_list), 4),
            'max': round(max(obs_list), 4),
            'count': n
        }
    
    def export_observations(self, file_path: str) -> bool:
        """
        Export observations to JSON file for persistence
        
        Args:
            file_path: Path to save observations
        
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                name: list(values) 
                for name, values in self._observed_values.items()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self._log('info', f"Exported observations to {file_path}")
            return True
        except Exception as e:
            self._log('error', f"Failed to export observations: {e}")
            return False
    
    def import_observations(self, file_path: str) -> bool:
        """
        Import observations from JSON file
        
        Args:
            file_path: Path to load observations from
        
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self._log('warning', f"Observations file not found: {file_path}")
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, values in data.items():
                if name not in self._observed_values:
                    self._observed_values[name] = deque(maxlen=self.MAX_OBSERVATIONS)
                
                for value in values:
                    if self._is_valid_number(value):
                        self._observed_values[name].append(float(value))
            
            self._log('info', f"Imported observations from {file_path}")
            return True
        except Exception as e:
            self._log('error', f"Failed to import observations: {e}")
            return False
    
    def get_all_bounds(self) -> Dict[str, Dict]:
        """Get all metric bounds as dictionary"""
        return {name: bounds.to_dict() for name, bounds in self.bounds.items()}
    
    def __repr__(self) -> str:
        obs_count = sum(len(v) for v in self._observed_values.values())
        return f"MetricNormalizer(metrics={len(self.bounds)}, observations={obs_count})"


# Convenience functions
def normalize_metric(metric_name: str, value: Any) -> float:
    """Quick normalize a single metric"""
    normalizer = MetricNormalizer()
    return normalizer.normalize(metric_name, value)


def get_metric_grade(metric_name: str, value: Any) -> str:
    """Quick get grade for a metric"""
    normalizer = MetricNormalizer()
    return normalizer.get_metric_grade(metric_name, value)


def get_metric_status(metric_name: str, value: Any) -> str:
    """Quick get status for a metric"""
    normalizer = MetricNormalizer()
    return normalizer.get_metric_status(metric_name, value)