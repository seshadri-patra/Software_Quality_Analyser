"""
SQA-AI Core Package
Contains the main analysis engines:
- Parser: Extract code metrics
- GitAnalyzer: Analyze repository history
- DDICalculator: Calculate Developer-Centric Decay Index
- MetricNormalizer: Normalize metrics to standard scales
- RecommendationEngine: Generate actionable suggestions
"""

# Lazy imports to prevent circular dependencies
def get_parser():
    from .parser import CodeParser
    return CodeParser

def get_git_analyzer():
    from .git_analyzer import GitAnalyzer
    return GitAnalyzer

def get_ddi_calculator():
    from .ddi_calculator import DDICalculator
    return DDICalculator

def get_metric_normalizer():
    from .metric_normalizer import MetricNormalizer
    return MetricNormalizer

def get_recommendation_engine():
    from .recommendation_engine import RecommendationEngine
    return RecommendationEngine

__all__ = [
    'get_parser',
    'get_git_analyzer', 
    'get_ddi_calculator',
    'get_metric_normalizer',
    'get_recommendation_engine'
]

__version__ = '1.0.0'
