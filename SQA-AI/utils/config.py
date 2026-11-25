"""
Configuration Manager for SQA-AI
Loads and manages all configuration settings from YAML file
Supports environment variable overrides
"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class Config:
    """
    Singleton configuration manager
    Loads settings from config.yaml and provides easy access
    Supports environment variable overrides with SQA_ prefix
    """
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    _loaded: bool = False
    
    # Validation rules: metric -> (min, max)
    VALIDATION_RULES = {
        'thresholds.cyclomatic_complexity.low': (1, 50),
        'thresholds.cyclomatic_complexity.medium': (5, 100),
        'thresholds.cyclomatic_complexity.high': (10, 200),
        'thresholds.maintainability_index.good': (50, 100),
        'thresholds.maintainability_index.moderate': (25, 75),
        'thresholds.maintainability_index.poor': (0, 50),
        'ddi.weights.decay_rate': (0, 1),
        'ddi.weights.entropy': (0, 1),
        'ddi.weights.volatility': (0, 1),
        'ddi.weights.frequency': (0, 1),
    }
    
    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Config._loaded:
            self._load_config()
            self._apply_env_overrides()
            self._validate_config()
            Config._loaded = True
    
    def _find_config_file(self) -> Optional[Path]:
        """Find config file in possible locations"""
        possible_paths = [
            Path('config.yaml'),
            Path('../config.yaml'),
            Path(__file__).parent.parent / 'config.yaml',
            Path.home() / '.sqa-ai' / 'config.yaml'
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.resolve()
        
        return None
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        config_path = self._find_config_file()
        
        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    self._config = yaml.safe_load(file) or {}
                    self._config_path = config_path
            except yaml.YAMLError as e:
                print(f"Warning: Error parsing config file: {e}")
                self._config = self._get_defaults()
        else:
            self._config = self._get_defaults()
            self._config_path = None
    
    def _apply_env_overrides(self) -> None:
        """
        Apply environment variable overrides
        Format: SQA_SECTION_KEY=value
        Example: SQA_DATABASE_PATH=./mydb.db
        """
        for key, value in os.environ.items():
            if key.startswith('SQA_'):
                # Convert SQA_DATABASE_PATH to database.path
                config_key = key[4:].lower().replace('_', '.')
                self._set_nested(config_key, self._parse_env_value(value))
    
    def _parse_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Parse environment variable value to appropriate type"""
        # Boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # String
        return value
    
    def _set_nested(self, key: str, value: Any) -> None:
        """Set a nested configuration value"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def _validate_config(self) -> None:
        """Validate configuration values against rules"""
        errors = []
        
        for key, (min_val, max_val) in self.VALIDATION_RULES.items():
            value = self.get(key)
            if value is not None:
                if not isinstance(value, (int, float)):
                    errors.append(f"{key}: expected number, got {type(value).__name__}")
                elif not min_val <= value <= max_val:
                    errors.append(f"{key}: {value} not in range [{min_val}, {max_val}]")
        
        # Validate DDI weights sum to 1
        weights = self.get('ddi.weights', {})
        if weights:
            weight_sum = sum(weights.values())
            if not 0.99 <= weight_sum <= 1.01:  # Allow small floating point errors
                errors.append(f"DDI weights must sum to 1.0, got {weight_sum}")
        
        if errors:
            for error in errors:
                print(f"Config Warning: {error}")
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Return default configuration values"""
        return {
            'project': {
                'name': 'SQA-AI',
                'version': '1.0.0'
            },
            'thresholds': {
                'cyclomatic_complexity': {'low': 10, 'medium': 20, 'high': 30},
                'maintainability_index': {'good': 65, 'moderate': 45, 'poor': 25},
                'comment_density': {'good': 0.2, 'moderate': 0.1, 'poor': 0.05},
                'loc_per_function': {'good': 30, 'moderate': 50, 'poor': 100}
            },
            'ddi': {
                'weights': {
                    'decay_rate': 0.35,
                    'entropy': 0.30,
                    'volatility': 0.20,
                    'frequency': 0.15
                },
                'risk_levels': {'low': 25, 'medium': 50, 'high': 75, 'critical': 90}
            },
            'scoring': {
                'maintainability_index': 0.30,
                'cyclomatic_complexity': 0.25,
                'comment_density': 0.10,
                'coupling': 0.15,
                'cohesion': 0.10,
                'duplication': 0.10
            },
            'analysis': {
                'max_file_size_kb': 1024,  # Skip files larger than 1MB
                'min_lines': 5,  # Skip files with fewer lines
                'include_tests': False
            },
            'database': {
                'path': 'sqa.db',
                'backup_enabled': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'sqa_ai.log',
                'console_colors': True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('thresholds.cyclomatic_complexity.low')
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_threshold(self, metric: str, level: str) -> Any:
        """Get specific threshold value for a metric"""
        return self.get(f'thresholds.{metric}.{level}')
    
    def get_ddi_weight(self, factor: str) -> float:
        """Get DDI weight for specific factor"""
        return self.get(f'ddi.weights.{factor}', 0.25)
    
    def get_risk_level(self, level: str) -> int:
        """Get DDI risk level threshold"""
        return self.get(f'ddi.risk_levels.{level}', 50)
    
    def get_scoring_weight(self, metric: str) -> float:
        """Get scoring weight for specific metric"""
        return self.get(f'scoring.{metric}', 0.1)
    
    @property
    def database_path(self) -> str:
        """Get database file path"""
        return self.get('database.path', 'sqa.db')
    
    @property
    def log_level(self) -> str:
        """Get logging level"""
        return self.get('logging.level', 'INFO')
    
    @property
    def log_file(self) -> str:
        """Get log file path"""
        return self.get('logging.file', 'sqa_ai.log')
    
    @property
    def max_file_size(self) -> int:
        """Get maximum file size in bytes"""
        return self.get('analysis.max_file_size_kb', 1024) * 1024
    
    @property
    def min_lines(self) -> int:
        """Get minimum lines threshold"""
        return self.get('analysis.min_lines', 5)
    
    def reload(self) -> None:
        """Reload configuration from file"""
        Config._loaded = False
        self._load_config()
        self._apply_env_overrides()
        self._validate_config()
        Config._loaded = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Return full configuration as dictionary"""
        return self._config.copy()
    
    def __repr__(self) -> str:
        return f"Config(project={self.get('project.name')}, version={self.get('project.version')})"


# Create singleton instance
config = Config()