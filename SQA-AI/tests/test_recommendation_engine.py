import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.recommendation_engine import RecommendationEngine


def test_recommendations_generated_for_bad_metrics():
    engine = RecommendationEngine()

    file_path = "x.py"
    metrics = {
        "file_path": file_path,
        "sloc": 1200,
        "cyclomatic_complexity": 50,
        "max_complexity": 40,
        "maintainability_index": 20,
        "comment_density": 0.01,
        "import_count": 30,
        "docstring_coverage": 0.0,
        "function_count": 10,
        "class_count": 1,
    }

    ddi_result = {
        "ddi_score": 95,
        "contributor_entropy": 0.8,
        "contributor_count": 15
    }

    recs = engine.analyze_file(file_path, metrics, ddi_result=ddi_result)

    assert len(recs) > 0

    severities = {r.severity.value for r in recs}
    assert ("high" in severities) or ("critical" in severities)