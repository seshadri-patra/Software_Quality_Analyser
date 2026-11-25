"""
SQA-AI Utilities Package
Contains helper functions and configurations

Uses lazy imports to prevent circular dependency issues
"""

# Lazy imports - only load when accessed
def get_config():
    from .config import Config
    return Config()

def get_logger(name: str):
    from .logger import Logger
    return Logger(name)

def get_file_handler(path: str):
    from .file_handler import FileHandler
    return FileHandler(path)

# For direct imports when needed
__all__ = ['get_config', 'get_logger', 'get_file_handler']