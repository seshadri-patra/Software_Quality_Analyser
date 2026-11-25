"""
File Handler for SQA-AI
Manages file operations, directory walking, and content reading
Includes binary detection and file size limits
"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Generator, Set
from functools import lru_cache


class FileHandler:
    """
    Handles all file system operations for SQA-AI
    Includes safety checks for binary files and size limits
    """
    
    # Supported file extensions by language
    SUPPORTED_EXTENSIONS: Dict[str, List[str]] = {
        'python': ['.py', '.pyw'],
        'java': ['.java'],
        'javascript': ['.js', '.jsx', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'cpp': ['.cpp', '.cc', '.cxx', '.c', '.hpp', '.h', '.hxx'],
        'csharp': ['.cs'],
        'go': ['.go'],
        'ruby': ['.rb'],
        'php': ['.php'],
        'rust': ['.rs'],
        'kotlin': ['.kt', '.kts'],
        'swift': ['.swift'],
        'scala': ['.scala']
    }
    
    # Directories to ignore
    IGNORE_DIRS: Set[str] = {
        '__pycache__', '.git', '.svn', '.hg', '.bzr',
        'node_modules', 'venv', 'env', '.env', '.venv',
        'build', 'dist', '.idea', '.vscode', '.vs',
        'vendor', 'target', 'bin', 'obj', 'out',
        '.pytest_cache', '.mypy_cache', '.tox',
        'eggs', '.eggs', '*.egg-info',
        'coverage', 'htmlcov', '.coverage'
    }
    
    # Files to ignore
    IGNORE_FILES: Set[str] = {
        '__init__.py',
        'setup.py',
        'conftest.py',
        'manage.py',
        'wsgi.py',
        'asgi.py'
    }
    
    # Binary file signatures (magic bytes)
    BINARY_SIGNATURES: List[bytes] = [
        b'\x89PNG',      # PNG
        b'\xff\xd8\xff', # JPEG
        b'GIF8',         # GIF
        b'PK\x03\x04',   # ZIP
        b'\x7fELF',      # ELF
        b'MZ',           # EXE
        b'\x00\x00\x00', # Various binary
    ]
    
    # Default max file size: 1MB
    DEFAULT_MAX_SIZE: int = 1024 * 1024
    
    # Minimum lines to consider for analysis
    DEFAULT_MIN_LINES: int = 5
    
    def __init__(
        self, 
        base_path: str,
        max_file_size: Optional[int] = None,
        min_lines: Optional[int] = None
    ):
        """
        Initialize FileHandler with base path
        
        Args:
            base_path: Root directory to scan
            max_file_size: Maximum file size in bytes (default: 1MB)
            min_lines: Minimum lines for a file to be analyzed
        """
        self.base_path = Path(base_path).resolve()
        self.max_file_size = max_file_size or self.DEFAULT_MAX_SIZE
        self.min_lines = min_lines or self.DEFAULT_MIN_LINES
        
        # Initialize logger lazily
        self._logger = None
        
        if not self.base_path.exists():
            raise FileNotFoundError(f"Path does not exist: {base_path}")
        
        self._log_info(f"FileHandler initialized for: {self.base_path}")
    
    @property
    def logger(self):
        """Lazy logger initialization"""
        if self._logger is None:
            try:
                from .logger import get_logger
                self._logger = get_logger(__name__)
            except ImportError:
                self._logger = None
        return self._logger
    
    def _log_info(self, message: str) -> None:
        """Log info message if logger available"""
        if self.logger:
            self.logger.info(message)
    
    def _log_warning(self, message: str) -> None:
        """Log warning message if logger available"""
        if self.logger:
            self.logger.warning(message)
    
    def _log_error(self, message: str) -> None:
        """Log error message if logger available"""
        if self.logger:
            self.logger.error(message)
    
    def is_binary_file(self, file_path: Path) -> bool:
        """
        Check if file is binary by reading first few bytes
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file appears to be binary
        """
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(512)
                
                # Check for known binary signatures
                for sig in self.BINARY_SIGNATURES:
                    if chunk.startswith(sig):
                        return True
                
                # Check for null bytes (common in binary files)
                if b'\x00' in chunk:
                    return True
                
                # Try to decode as text
                try:
                    chunk.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        chunk.decode('latin-1')
                    except UnicodeDecodeError:
                        return True
                
                return False
        except Exception:
            return True  # Assume binary if we can't read
    
    def is_file_too_large(self, file_path: Path) -> bool:
        """Check if file exceeds size limit"""
        try:
            return file_path.stat().st_size > self.max_file_size
        except Exception:
            return True
    
    def should_skip_file(self, file_path: Path) -> tuple[bool, str]:
        """
        Determine if file should be skipped and why
        
        Returns:
            Tuple of (should_skip, reason)
        """
        # Check filename
        if file_path.name in self.IGNORE_FILES:
            return True, "ignored_filename"
        
        # Check size
        if self.is_file_too_large(file_path):
            return True, "too_large"
        
        # Check binary
        if self.is_binary_file(file_path):
            return True, "binary_file"
        
        return False, ""
    
    def get_all_files(self, extensions: Optional[List[str]] = None) -> List[Path]:
        """
        Get all supported files in directory tree
        
        Args:
            extensions: Optional list of extensions to filter
        
        Returns:
            List of Path objects for matching files
        """
        if extensions is None:
            extensions = self.SUPPORTED_EXTENSIONS['python']
        
        # Normalize extensions
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        
        files = []
        skipped = {'too_large': 0, 'binary_file': 0, 'ignored_filename': 0}
        
        for root, dirs, filenames in os.walk(self.base_path):
            # Remove ignored directories from walk
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS and not d.startswith('.')]
            
            for filename in filenames:
                # Check extension
                if not any(filename.lower().endswith(ext) for ext in extensions):
                    continue
                
                file_path = Path(root) / filename
                
                # Check if should skip
                should_skip, reason = self.should_skip_file(file_path)
                if should_skip:
                    skipped[reason] = skipped.get(reason, 0) + 1
                    continue
                
                files.append(file_path)
        
        self._log_info(f"Found {len(files)} files with extensions {extensions}")
        if any(skipped.values()):
            self._log_info(f"Skipped files: {skipped}")
        
        return sorted(files)
    
    def get_python_files(self) -> List[Path]:
        """Get all Python files"""
        return self.get_all_files(['.py'])
    
    @lru_cache(maxsize=128)
    def read_file_cached(self, file_path: str) -> Optional[str]:
        """
        Read file content with caching
        
        Args:
            file_path: Path to file as string (for cache key)
        
        Returns:
            File content or None if error
        """
        return self.read_file(Path(file_path))
    
    def read_file(self, file_path: Path) -> Optional[str]:
        """
        Read file content safely
        
        Args:
            file_path: Path to file
        
        Returns:
            File content as string or None if error
        """
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self._log_error(f"Error reading {file_path}: {e}")
                return None
        
        self._log_error(f"Cannot decode file with any encoding: {file_path}")
        return None
    
    def read_lines(self, file_path: Path) -> List[str]:
        """
        Read file as list of lines
        
        Args:
            file_path: Path to file
        
        Returns:
            List of lines
        """
        content = self.read_file(file_path)
        if content is None:
            return []
        return content.splitlines()
    
    def get_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file content
        More secure than MD5
        
        Args:
            file_path: Path to file
        
        Returns:
            SHA256 hash string
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def get_relative_path(self, file_path: Path) -> str:
        """
        Get path relative to base path
        
        Args:
            file_path: Absolute path
        
        Returns:
            Relative path string
        """
        try:
            return str(file_path.relative_to(self.base_path))
        except ValueError:
            return str(file_path)
    
    def detect_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension
        
        Args:
            file_path: Path to file
        
        Returns:
            Language name string
        """
        suffix = file_path.suffix.lower()
        
        for language, extensions in self.SUPPORTED_EXTENSIONS.items():
            if suffix in extensions:
                return language
        
        return 'unknown'
    
    def get_file_info(self, file_path: Path) -> Dict:
        """
        Get comprehensive file information
        
        Args:
            file_path: Path to file
        
        Returns:
            Dictionary with file metadata
        """
        try:
            stat = file_path.stat()
            content = self.read_file(file_path)
            line_count = len(content.splitlines()) if content else 0
            
            return {
                'path': str(file_path),
                'relative_path': self.get_relative_path(file_path),
                'name': file_path.name,
                'extension': file_path.suffix,
                'language': self.detect_language(file_path),
                'size_bytes': stat.st_size,
                'size_kb': round(stat.st_size / 1024, 2),
                'modified_time': stat.st_mtime,
                'hash': self.get_file_hash(file_path),
                'line_count': line_count,
                'is_empty': line_count < self.min_lines,
                'readable': content is not None
            }
        except Exception as e:
            self._log_error(f"Error getting file info for {file_path}: {e}")
            return {
                'path': str(file_path),
                'error': str(e),
                'readable': False
            }
    
    def walk_files(self, extensions: Optional[List[str]] = None) -> Generator[Dict, None, None]:
        """
        Generator that yields file info for each file
        Memory efficient for large codebases
        
        Args:
            extensions: Optional list of extensions to filter
        
        Yields:
            File info dictionary
        """
        for file_path in self.get_all_files(extensions):
            info = self.get_file_info(file_path)
            if info.get('readable', False) and not info.get('is_empty', True):
                yield info
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return Path(file_path).exists()
    
    def get_directory_stats(self) -> Dict:
        """
        Get statistics about the directory
        
        Returns:
            Dictionary with directory statistics
        """
        files = list(self.walk_files())
        total_lines = sum(f.get('line_count', 0) for f in files)
        total_size = sum(f.get('size_bytes', 0) for f in files)
        
        language_counts = {}
        for f in files:
            lang = f.get('language', 'unknown')
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        return {
            'base_path': str(self.base_path),
            'total_files': len(files),
            'total_lines': total_lines,
            'total_size_bytes': total_size,
            'total_size_kb': round(total_size / 1024, 2),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'languages': language_counts,
            'avg_lines_per_file': round(total_lines / len(files), 1) if files else 0
        }
    
    def clear_cache(self) -> None:
        """Clear the file reading cache"""
        self.read_file_cached.cache_clear()
    
    def __repr__(self) -> str:
        return f"FileHandler(base_path='{self.base_path}', max_size={self.max_file_size})"