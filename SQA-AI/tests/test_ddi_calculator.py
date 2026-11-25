import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.ddi_calculator import DDICalculator, RiskLevel


def test_ddi_low_risk_minimal_inputs():
    calc = DDICalculator()

    git_factors = {
        "file_path": "a.py",
        "contributor_count": 1,
        "total_commits": 20,
        "age_days": 365,
        "days_since_last_change": 5,
        "contributor_entropy": 0.05,
        "commit_frequency": 2.0,
        "avg_commit_gap_days": 10,
        "commit_gap_variance": 50,
        "total_churn": 10,
    }

    current_metrics = {
        "maintainability_index": 80,
        "cyclomatic_complexity": 5,
        "comment_density": 0.2,
        "sloc": 120,
    }

    r = calc.calculate_ddi(git_factors, current_metrics)

    assert 0 <= r.ddi_score <= 100
    assert r.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)

    assert 0 <= r.decay_rate_score <= 100
    assert 0 <= r.entropy_score <= 100
    assert 0 <= r.volatility_score <= 100
    assert 0 <= r.frequency_score <= 100


def test_ddi_entropy_drives_score_up():
    calc = DDICalculator()

    git_factors = {
        "file_path": "b.py",
        "contributor_count": 12,
        "total_commits": 20,
        "age_days": 365,
        "days_since_last_change": 5,
        "contributor_entropy": 0.8,
        "commit_frequency": 2.0,
        "avg_commit_gap_days": 10,
        "commit_gap_variance": 50,
        "total_churn": 10,
    }

    r = calc.calculate_ddi(git_factors, current_metrics={"sloc": 200})

    assert r.entropy_score > 40


def test_ddi_risk_level_thresholding():
    calc = DDICalculator()

    git_factors = {
        "file_path": "c.py",
        "contributor_count": 25,
        "total_commits": 30,
        "age_days": 365,
        "days_since_last_change": 400,
        "contributor_entropy": 0.9,
        "commit_frequency": 20.0,
        "avg_commit_gap_days": 200,
        "commit_gap_variance": 5000,
        "total_churn": 5000,
    }

    r = calc.calculate_ddi(git_factors, current_metrics={"sloc": 500})

    assert r.ddi_score >= 50
    