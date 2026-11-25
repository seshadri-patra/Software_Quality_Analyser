"""
SQA-AI Database Package
Handles data persistence using SQLite

Components:
- DBManager: CRUD operations
- Models: Data classes for type safety
- Schema: Table definitions
"""

from .db_manager import DBManager
from .models import (
    Project,
    FileRecord,
    MetricRecord,
    AnalysisRecord,
    RecommendationRecord,
    DDIRecord
)

__all__ = [
    'DBManager',
    'Project',
    'FileRecord',
    'MetricRecord',
    'AnalysisRecord',
    'RecommendationRecord',
    'DDIRecord'
]