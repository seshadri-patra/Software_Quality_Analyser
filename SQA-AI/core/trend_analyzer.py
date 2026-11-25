"""
Trend Analyzer for SQA-AI
Predicts future DDI scores using historical data

Features:
- Linear regression for trend slope
- Exponential smoothing for noise reduction
- 30-day prediction
- Days until critical estimation
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


class TrendAnalyzer:
    """
    Analyzes DDI trends and predicts future scores
    
    Uses formulas from the paper:
    - Linear regression: slope = Σ((ti - t̄)(si - s̄)) / Σ((ti - t̄)²)
    - Exponential smoothing: smoothed_t = α × score_t + (1-α) × smoothed_t-1
    """
    
    def __init__(self, alpha: float = 0.3):
        """
        Initialize trend analyzer
        
        Args:
            alpha: Smoothing factor for exponential smoothing (0-1)
                   Higher = more weight on recent values
        """
        self.alpha = max(0.0, min(1.0, alpha))
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
    
    def calculate_slope(self, timestamps: List[float], scores: List[float]) -> float:
        """
        Calculate linear regression slope
        
        Formula: slope = Σ((ti - t̄)(si - s̄)) / Σ((ti - t̄)²)
        
        Args:
            timestamps: List of timestamps (as days or numeric values)
            scores: List of corresponding DDI scores
        
        Returns:
            Slope (DDI change per day)
        """
        if len(timestamps) < 2 or len(timestamps) != len(scores):
            return 0.0
        
        n = len(timestamps)
        
        # Calculate means
        t_mean = sum(timestamps) / n
        s_mean = sum(scores) / n
        
        # Calculate slope using least squares
        numerator = sum((t - t_mean) * (s - s_mean) for t, s in zip(timestamps, scores))
        denominator = sum((t - t_mean) ** 2 for t in timestamps)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def exponential_smoothing(self, scores: List[float]) -> List[float]:
        """
        Apply exponential smoothing to reduce noise
        
        Formula: smoothed_t = α × score_t + (1-α) × smoothed_t-1
        
        Args:
            scores: List of DDI scores (oldest to newest)
        
        Returns:
            List of smoothed scores
        """
        if not scores:
            return []
        
        if len(scores) == 1:
            return scores.copy()
        
        smoothed = [scores[0]]
        
        for i in range(1, len(scores)):
            new_val = self.alpha * scores[i] + (1 - self.alpha) * smoothed[i-1]
            smoothed.append(new_val)
        
        return smoothed
    
    def predict_future(
        self, 
        current_ddi: float, 
        slope: float, 
        days_ahead: int = 30
    ) -> float:
        """
        Predict DDI score N days ahead
        
        Formula: predicted = current + (slope × days)
        
        Args:
            current_ddi: Current DDI score
            slope: Daily change rate
            days_ahead: Number of days to predict
        
        Returns:
            Predicted DDI score (clamped to 0-100)
        """
        predicted = current_ddi + (slope * days_ahead)
        return max(0, min(100, predicted))
    
    def days_until_critical(
        self, 
        current_ddi: float, 
        slope: float, 
        critical_threshold: float = 75
    ) -> int:
        """
        Calculate days until DDI reaches critical level
        
        Args:
            current_ddi: Current DDI score
            slope: Daily change rate
            critical_threshold: DDI score considered critical
        
        Returns:
            Days until critical (-1 if not degrading or already critical)
        """
        if slope <= 0:
            return -1  # Not degrading or improving
        
        if current_ddi >= critical_threshold:
            return 0  # Already critical
        
        days = (critical_threshold - current_ddi) / slope
        return max(0, int(days))
    
    def days_until_threshold(
        self,
        current_ddi: float,
        slope: float,
        threshold: float
    ) -> int:
        """
        Calculate days until DDI reaches any threshold
        
        Args:
            current_ddi: Current DDI score
            slope: Daily change rate
            threshold: Target DDI threshold
        
        Returns:
            Days until threshold (-1 if won't reach)
        """
        if slope == 0:
            return -1
        
        if slope > 0 and current_ddi >= threshold:
            return 0  # Already past threshold (degrading direction)
        
        if slope < 0 and current_ddi <= threshold:
            return 0  # Already past threshold (improving direction)
        
        days = (threshold - current_ddi) / slope
        
        if days < 0:
            return -1  # Wrong direction
        
        return max(0, int(days))
    
    def analyze_history(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Complete trend analysis from metric_history records
        
        Args:
            history: List of dicts with 'run_at'/'snapshot_at' and 'ddi_score'/'avg_ddi_score'
                     Expected to be sorted newest-to-oldest or oldest-to-newest
        
        Returns:
            Complete trend analysis results
        """
        if not history or len(history) < 2:
            return {
                'has_sufficient_data': False,
                'data_points': len(history) if history else 0,
                'slope': 0.0,
                'slope_per_week': 0.0,
                'slope_per_month': 0.0,
                'trend': 'insufficient_data',
                'current_ddi': history[0].get('avg_ddi_score', history[0].get('ddi_score', 0)) if history else 0,
                'predicted_7d': None,
                'predicted_30d': None,
                'predicted_90d': None,
                'days_until_critical': -1,
                'days_until_high': -1,
                'days_until_medium': -1,
                'smoothed_scores': [],
                'confidence': 0.0,
                'recommendation': 'Need more data points for trend analysis.'
            }
        
        # Sort history oldest to newest
        sorted_history = sorted(
            history, 
            key=lambda h: h.get('run_at', h.get('snapshot_at', '')),
            reverse=False
        )
        
        # Extract timestamps and scores
        base_time = None
        timestamps = []
        scores = []
        seen_dates = set()
        base_time = None
        timestamps = []
        scores = []

        for h in sorted_history:
            # Get timestamp (support both run_at and snapshot_at)
            snapshot_at = h.get('run_at', h.get('snapshot_at'))
            # Get DDI score (support both avg_ddi_score and ddi_score)
            ddi_score = h.get('avg_ddi_score', h.get('ddi_score'))
            
            if snapshot_at is None or ddi_score is None:
                continue
            
            # Parse timestamp
            if isinstance(snapshot_at, str):
                try:
                    dt = datetime.fromisoformat(snapshot_at.replace('Z', '+00:00'))
                    # Remove timezone info for comparison
                    if dt.tzinfo is not None:
                        dt = dt.replace(tzinfo=None)
                except ValueError:
                    continue
            elif isinstance(snapshot_at, datetime):
                dt = snapshot_at
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
            else:
                continue
            
            # ✅ NEW: Only keep ONE scan per day (first one)
            date_key = dt.date()  # Extract just the date (no time)
            
            if date_key in seen_dates:
                continue  # Skip - we already have a scan from this day
            
            seen_dates.add(date_key)
            
            # Now process this scan
            if base_time is None:
                base_time = dt
            
            days = (dt - base_time).total_seconds() / 86400  # Days since first snapshot
            timestamps.append(days)
            scores.append(float(ddi_score))
                
        
        if len(timestamps) < 2:
            return {
                'has_sufficient_data': False,
                'data_points': len(timestamps),
                'slope': 0.0,
                'slope_per_week': 0.0,
                'slope_per_month': 0.0,
                'trend': 'insufficient_data',
                'current_ddi': scores[-1] if scores else 0,
                'predicted_30d': None,
                'days_until_critical': -1,
                'smoothed_scores': scores,
                'confidence': 0.0,
                'recommendation': 'Need more data points for trend analysis.'
            }
        
        # Calculate slope (per day)
        slope = self.calculate_slope(timestamps, scores)
        
        # Current DDI (most recent)
        current_ddi = scores[-1]
        
        # Predictions
        predicted_7d = self.predict_future(current_ddi, slope, 7)
        predicted_30d = self.predict_future(current_ddi, slope, 30)
        predicted_90d = self.predict_future(current_ddi, slope, 90)
        
        # Days until thresholds
        days_critical = self.days_until_critical(current_ddi, slope, 75)
        days_high = self.days_until_threshold(current_ddi, slope, 50)
        days_medium = self.days_until_threshold(current_ddi, slope, 25)
        
        # Determine trend direction
        if slope > 0.1:
            trend = 'degrading'
        elif slope > 0.02:
            trend = 'slowly_degrading'
        elif slope < -0.1:
            trend = 'improving'
        elif slope < -0.02:
            trend = 'slowly_improving'
        else:
            trend = 'stable'
        
        # Apply exponential smoothing
        smoothed_scores = self.exponential_smoothing(scores)
        
        # Calculate confidence based on data points and time span
        time_span_days = timestamps[-1] - timestamps[0] if timestamps else 0
        confidence = self._calculate_trend_confidence(len(timestamps), time_span_days)
        
        # Generate recommendation
        recommendation = self._generate_trend_recommendation(
            trend, current_ddi, slope, days_critical, confidence
        )
        
        return {
            'has_sufficient_data': True,
            'data_points': len(timestamps),
            'time_span_days': round(time_span_days, 1),
            
            'slope': round(slope, 4),
            'slope_per_week': round(slope * 7, 2),
            'slope_per_month': round(slope * 30, 2),
            'trend': trend,
            
            'current_ddi': round(current_ddi, 2),
            'predicted_7d': round(predicted_7d, 2),
            'predicted_30d': round(predicted_30d, 2),
            'predicted_90d': round(predicted_90d, 2),
            
            'days_until_critical': days_critical,
            'days_until_high': days_high,
            'days_until_medium': days_medium,
            
            'raw_scores': scores,
            'smoothed_scores': [round(s, 2) for s in smoothed_scores],
            'timestamps_days': timestamps,
            
            'confidence': round(confidence, 1),
            'recommendation': recommendation
        }
    
    def _calculate_trend_confidence(self, data_points: int, time_span_days: float) -> float:
        """Calculate confidence in trend prediction"""
        confidence = 30.0
        
        # More data points = higher confidence
        if data_points >= 20:
            confidence += 30
        elif data_points >= 10:
            confidence += 20
        elif data_points >= 5:
            confidence += 10
        
        # Longer time span = higher confidence
        if time_span_days >= 90:
            confidence += 25
        elif time_span_days >= 30:
            confidence += 15
        elif time_span_days >= 7:
            confidence += 5
        
        return min(100, confidence)
    
    def _generate_trend_recommendation(
        self,
        trend: str,
        current_ddi: float,
        slope: float,
        days_until_critical: int,
        confidence: float
    ) -> str:
        """Generate actionable recommendation based on trend"""
        
        if confidence < 50:
            prefix = "Low confidence: "
        else:
            prefix = ""
        
        if trend == 'degrading':
            if days_until_critical >= 0 and days_until_critical < 30:
                return f"{prefix}URGENT: Quality degrading rapidly. Critical in ~{days_until_critical} days. Take immediate action."
            elif days_until_critical >= 0 and days_until_critical < 90:
                return f"{prefix}Quality declining. Critical in ~{days_until_critical} days. Plan remediation soon."
            else:
                return f"{prefix}Quality slowly declining ({slope*30:.1f} DDI/month). Monitor and plan improvements."
        
        elif trend == 'slowly_degrading':
            return f"{prefix}Slight quality decline detected ({slope*30:.1f} DDI/month). Keep monitoring."
        
        elif trend == 'improving':
            return f"{prefix}Excellent! Quality improving ({abs(slope)*30:.1f} DDI reduction/month). Keep up the good work."
        
        elif trend == 'slowly_improving':
            return f"{prefix}Quality slowly improving. Continue current practices."
        
        else:  # stable
            if current_ddi > 75:
                return f"{prefix}Quality stable but critical (DDI={current_ddi:.0f}). Needs attention."
            elif current_ddi > 50:
                return f"{prefix}Quality stable but elevated (DDI={current_ddi:.0f}). Consider improvements."
            else:
                return f"{prefix}Quality stable and healthy. Continue regular maintenance."
    
    def compare_periods(
        self,
        current_period: List[Dict],
        previous_period: List[Dict]
    ) -> Dict[str, Any]:
        """
        Compare two time periods
        
        Args:
            current_period: Recent history records
            previous_period: Earlier history records
        
        Returns:
            Comparison results
        """
        current_analysis = self.analyze_history(current_period)
        previous_analysis = self.analyze_history(previous_period)
        
        if not current_analysis['has_sufficient_data'] or not previous_analysis['has_sufficient_data']:
            return {
                'comparable': False,
                'reason': 'Insufficient data in one or both periods'
            }
        
        current_avg = sum(current_analysis.get('raw_scores', [0])) / max(len(current_analysis.get('raw_scores', [1])), 1)
        previous_avg = sum(previous_analysis.get('raw_scores', [0])) / max(len(previous_analysis.get('raw_scores', [1])), 1)
        
        return {
            'comparable': True,
            'current_avg_ddi': round(current_avg, 2),
            'previous_avg_ddi': round(previous_avg, 2),
            'avg_change': round(current_avg - previous_avg, 2),
            'current_trend': current_analysis['trend'],
            'previous_trend': previous_analysis['trend'],
            'slope_change': round(current_analysis['slope'] - previous_analysis['slope'], 4),
            'improving': current_avg < previous_avg
        }
    
    def __repr__(self) -> str:
        return f"TrendAnalyzer(alpha={self.alpha})"


# Convenience functions
def analyze_ddi_trend(history: List[Dict]) -> Dict[str, Any]:
    """Quick analyze DDI trend from history"""
    analyzer = TrendAnalyzer()
    return analyzer.analyze_history(history)


def predict_ddi(current: float, slope: float, days: int = 30) -> float:
    """Quick predict future DDI"""
    analyzer = TrendAnalyzer()
    return analyzer.predict_future(current, slope, days)
