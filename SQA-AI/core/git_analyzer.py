"""
Git Analyzer for SQA-AI
Extracts repository history and contributor patterns for DDI calculation

Features:
- Commit history extraction
- Contributor analysis
- File change tracking
- Temporal pattern detection
- Blame analysis

FIXES APPLIED:
- Shannon entropy formula (was simple ratio)
- Volatility as standard deviation (was variance)
"""

import os
import re
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from enum import Enum

# GitPython import
try:
    from git import Repo, InvalidGitRepositoryError, NoSuchPathError
    from git.exc import GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


class ChangeType(Enum):
    """Type of file change in a commit"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    UNKNOWN = "unknown"


@dataclass
class CommitInfo:
    """Information about a single commit"""
    hash: str
    short_hash: str
    author_name: str
    author_email: str
    date: datetime
    message: str
    files_changed: int
    insertions: int
    deletions: int
    
    def to_dict(self) -> Dict:
        return {
            'hash': self.hash,
            'short_hash': self.short_hash,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'date': self.date.isoformat(),
            'message': self.message,
            'files_changed': self.files_changed,
            'insertions': self.insertions,
            'deletions': self.deletions
        }


@dataclass
class FileChange:
    """Information about a file change in a commit"""
    file_path: str
    change_type: ChangeType
    insertions: int
    deletions: int
    commit_hash: str
    commit_date: datetime
    author: str
    old_path: Optional[str] = None  # For renames
    
    def to_dict(self) -> Dict:
        result = {
            'file_path': self.file_path,
            'change_type': self.change_type.value,
            'insertions': self.insertions,
            'deletions': self.deletions,
            'commit_hash': self.commit_hash,
            'commit_date': self.commit_date.isoformat(),
            'author': self.author
        }
        if self.old_path:
            result['old_path'] = self.old_path
        return result


@dataclass
class ContributorStats:
    """Statistics for a contributor"""
    name: str
    email: str
    commit_count: int
    files_touched: Set[str] = field(default_factory=set)
    total_insertions: int = 0
    total_deletions: int = 0
    first_commit: Optional[datetime] = None
    last_commit: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        active_days = 0
        if self.first_commit and self.last_commit:
            active_days = (self.last_commit - self.first_commit).days
        
        return {
            'name': self.name,
            'email': self.email,
            'commit_count': self.commit_count,
            'files_touched': len(self.files_touched),
            'total_insertions': self.total_insertions,
            'total_deletions': self.total_deletions,
            'first_commit': self.first_commit.isoformat() if self.first_commit else None,
            'last_commit': self.last_commit.isoformat() if self.last_commit else None,
            'active_days': active_days
        }


@dataclass
class FileHistory:
    """Complete history for a single file"""
    file_path: str
    total_commits: int
    contributors: List[str]
    first_commit_date: Optional[datetime]
    last_commit_date: Optional[datetime]
    total_insertions: int
    total_deletions: int
    changes: List[FileChange] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        age_days = 0
        if self.first_commit_date and self.last_commit_date:
            age_days = (self.last_commit_date - self.first_commit_date).days
        
        return {
            'file_path': self.file_path,
            'total_commits': self.total_commits,
            'contributor_count': len(self.contributors),
            'contributors': self.contributors,
            'first_commit_date': self.first_commit_date.isoformat() if self.first_commit_date else None,
            'last_commit_date': self.last_commit_date.isoformat() if self.last_commit_date else None,
            'age_days': age_days,
            'total_insertions': self.total_insertions,
            'total_deletions': self.total_deletions,
            'churn': self.total_insertions + self.total_deletions,
            'changes': [c.to_dict() for c in self.changes[-50:]]
        }
    
    @property
    def contributor_count(self) -> int:
        return len(self.contributors)
    
    @property
    def age_days(self) -> int:
        if self.first_commit_date and self.last_commit_date:
            return max(0, (self.last_commit_date - self.first_commit_date).days)
        return 0
    
    @property
    def churn(self) -> int:
        return self.total_insertions + self.total_deletions
    
    @property
    def commit_frequency(self) -> float:
        """Commits per month"""
        if self.age_days <= 0:
            return float(self.total_commits)
        months = max(self.age_days / 30.0, 1.0)
        return self.total_commits / months


@dataclass
class RepositoryStats:
    """Overall repository statistics"""
    path: str
    total_commits: int
    total_contributors: int
    total_files: int
    first_commit_date: Optional[datetime]
    last_commit_date: Optional[datetime]
    active_branch: str
    contributors: List[ContributorStats] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        age_days = 0
        if self.first_commit_date and self.last_commit_date:
            age_days = (self.last_commit_date - self.first_commit_date).days
        
        return {
            'path': self.path,
            'total_commits': self.total_commits,
            'total_contributors': self.total_contributors,
            'total_files': self.total_files,
            'first_commit_date': self.first_commit_date.isoformat() if self.first_commit_date else None,
            'last_commit_date': self.last_commit_date.isoformat() if self.last_commit_date else None,
            'age_days': age_days,
            'active_branch': self.active_branch,
            'contributors': [c.to_dict() for c in self.contributors]
        }


class GitAnalyzer:
    """
    Analyzes Git repository history for DDI calculation
    """
    
    # Maximum commits to analyze (for performance)
    MAX_COMMITS = 5000
    
    # Maximum iterations for safety
    MAX_ITERATIONS = 10000
    
    # File extensions to track
    CODE_EXTENSIONS = {
        '.py', '.java', '.js', '.jsx', '.ts', '.tsx',
        '.cpp', '.c', '.h', '.hpp', '.go', '.rb', '.php',
        '.rs', '.kt', '.swift', '.scala', '.cs'
    }
    
    # Directories to skip
    SKIP_DIRECTORIES = {
        'test', 'tests', 'spec', 'specs',
        'vendor', 'node_modules', 'venv', 'env',
        '__pycache__', '.git', '.svn', '.hg',
        'build', 'dist', 'target', 'bin', 'obj',
        'coverage', '.tox', '.pytest_cache'
    }
    
    def __init__(self, repo_path: str):
        """
        Initialize Git analyzer
        
        Args:
            repo_path: Path to Git repository
        
        Raises:
            ValueError: If GitPython not available or invalid repo
        """
        if not GIT_AVAILABLE:
            raise ValueError("GitPython not installed. Run: pip install gitpython")
        
        self.repo_path = Path(repo_path).resolve()
        self._logger = None
        self._init_logger()
        
        # Initialize repository
        try:
            self.repo = Repo(self.repo_path)
            if self.repo.bare:
                raise ValueError("Cannot analyze bare repository")
        except InvalidGitRepositoryError:
            raise ValueError(f"Not a valid Git repository: {repo_path}")
        except NoSuchPathError:
            raise ValueError(f"Path does not exist: {repo_path}")
        
        # Cache for file histories
        self._file_histories: Dict[str, FileHistory] = {}
        self._commits_cache: List[CommitInfo] = []
        self._contributor_stats: Dict[str, ContributorStats] = {}
        self._cache_valid = False
        
        self._log('info', f"GitAnalyzer initialized for: {self.repo_path}")
    
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
    
    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file based on extension"""
        return Path(file_path).suffix.lower() in self.CODE_EXTENSIONS
    
    def _should_skip_path(self, file_path: str) -> bool:
        """Check if path should be skipped"""
        path_lower = file_path.lower()
        for skip_dir in self.SKIP_DIRECTORIES:
            if skip_dir in path_lower:
                return True
        return False
    
    def _parse_commit_stats(self, commit) -> Tuple[int, int, int]:
        """
        Parse commit statistics (files changed, insertions, deletions)
        
        Returns:
            Tuple of (files_changed, insertions, deletions)
        """
        try:
            stats = commit.stats.total
            return (
                stats.get('files', 0),
                stats.get('insertions', 0),
                stats.get('deletions', 0)
            )
        except Exception as e:
            self._log('debug', f"Error parsing commit stats: {e}")
            return (0, 0, 0)
    
    def _detect_change_type(self, diff_item) -> ChangeType:
        """Detect the type of change from a diff item"""
        try:
            if diff_item.new_file:
                return ChangeType.ADDED
            elif diff_item.deleted_file:
                return ChangeType.DELETED
            elif diff_item.renamed:
                return ChangeType.RENAMED
            elif diff_item.copied_file:
                return ChangeType.COPIED
            else:
                return ChangeType.MODIFIED
        except Exception:
            return ChangeType.UNKNOWN
    
    def _safe_get_datetime(self, timestamp) -> datetime:
        """Safely convert timestamp to datetime"""
        try:
            return datetime.fromtimestamp(timestamp)
        except (OSError, ValueError, OverflowError):
            return datetime.now()
    
    def get_commits(
        self, 
        max_count: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        file_path: Optional[str] = None
    ) -> List[CommitInfo]:
        """
        Get commit history
        
        Args:
            max_count: Maximum number of commits to retrieve
            since: Only commits after this date
            until: Only commits before this date
            file_path: Only commits affecting this file
        
        Returns:
            List of CommitInfo objects
        """
        if max_count is None:
            max_count = self.MAX_COMMITS
        
        commits = []
        iterations = 0
        
        try:
            # Build git log arguments
            log_args = {'max_count': max_count}
            
            if since:
                log_args['since'] = since.strftime('%Y-%m-%d')
            if until:
                log_args['until'] = until.strftime('%Y-%m-%d')
            
            # Get commits
            if file_path:
                commit_iter = self.repo.iter_commits(paths=file_path, **log_args)
            else:
                commit_iter = self.repo.iter_commits(**log_args)
            
            for commit in commit_iter:
                iterations += 1
                if iterations > self.MAX_ITERATIONS:
                    self._log('warning', f"Reached max iterations ({self.MAX_ITERATIONS}), stopping")
                    break
                
                files_changed, insertions, deletions = self._parse_commit_stats(commit)
                
                # Safe author extraction
                author_name = 'Unknown'
                author_email = ''
                try:
                    if commit.author:
                        author_name = commit.author.name or 'Unknown'
                        author_email = commit.author.email or ''
                except Exception:
                    pass
                
                # Safe date extraction
                commit_date = self._safe_get_datetime(commit.committed_date)
                
                # Safe message extraction
                try:
                    message = commit.message.strip().split('\n')[0][:100]
                except Exception:
                    message = ''
                
                commit_info = CommitInfo(
                    hash=commit.hexsha,
                    short_hash=commit.hexsha[:7],
                    author_name=author_name,
                    author_email=author_email,
                    date=commit_date,
                    message=message,
                    files_changed=files_changed,
                    insertions=insertions,
                    deletions=deletions
                )
                commits.append(commit_info)
        
        except GitCommandError as e:
            self._log('error', f"Git command error: {e}")
        except Exception as e:
            self._log('error', f"Error getting commits: {e}")
        
        self._log('debug', f"Retrieved {len(commits)} commits")
        return commits
    
    def get_file_history(self, file_path: str, use_cache: bool = True) -> Optional[FileHistory]:
        """
        Get complete history for a specific file
        
        Args:
            file_path: Relative path to file
            use_cache: Whether to use cached results
        
        Returns:
            FileHistory object or None if file not found
        """
        # Normalize path
        file_path = str(Path(file_path)).replace('\\', '/')
        
        # Check cache
        if use_cache and file_path in self._file_histories:
            return self._file_histories[file_path]
        
        commits = self.get_commits(file_path=file_path)
        
        if not commits:
            self._log('debug', f"No commits found for file: {file_path}")
            return None
        
        changes = []
        contributors = set()
        total_insertions = 0
        total_deletions = 0
        
        for commit in commits:
            contributors.add(commit.author_name)
            
            # Get file-specific stats from this commit
            try:
                git_commit = self.repo.commit(commit.hash)
                
                # Find this file in the commit stats
                file_stats = git_commit.stats.files.get(file_path, {})
                ins = file_stats.get('insertions', 0)
                dels = file_stats.get('deletions', 0)
                
                total_insertions += ins
                total_deletions += dels
                
                # Detect change type
                change_type = ChangeType.MODIFIED
                old_path = None
                
                try:
                    if git_commit.parents:
                        diffs = git_commit.parents[0].diff(git_commit)
                        for diff in diffs:
                            diff_path = diff.b_path or diff.a_path
                            if diff_path == file_path:
                                change_type = self._detect_change_type(diff)
                                if diff.renamed:
                                    old_path = diff.a_path
                                break
                except Exception:
                    pass
                
                change = FileChange(
                    file_path=file_path,
                    change_type=change_type,
                    insertions=ins,
                    deletions=dels,
                    commit_hash=commit.hash,
                    commit_date=commit.date,
                    author=commit.author_name,
                    old_path=old_path
                )
                changes.append(change)
            
            except Exception as e:
                self._log('debug', f"Error getting file stats for commit {commit.short_hash}: {e}")
        
        history = FileHistory(
            file_path=file_path,
            total_commits=len(commits),
            contributors=list(contributors),
            first_commit_date=commits[-1].date if commits else None,
            last_commit_date=commits[0].date if commits else None,
            total_insertions=total_insertions,
            total_deletions=total_deletions,
            changes=changes
        )
        
        # Cache result
        self._file_histories[file_path] = history
        
        self._log('debug', f"File history for {file_path}: {len(commits)} commits, {len(contributors)} contributors")
        
        return history
    
    def get_contributor_stats(self, refresh: bool = False) -> Dict[str, ContributorStats]:
        """
        Get statistics for all contributors
        
        Args:
            refresh: Force refresh of cached stats
        
        Returns:
            Dictionary of contributor email -> ContributorStats
        """
        # Return cache if valid and not forcing refresh
        if self._contributor_stats and self._cache_valid and not refresh:
            return self._contributor_stats
        
        commits = self.get_commits()
        stats: Dict[str, ContributorStats] = {}
        
        for commit in commits:
            email = commit.author_email or commit.author_name
            
            if email not in stats:
                stats[email] = ContributorStats(
                    name=commit.author_name,
                    email=commit.author_email,
                    commit_count=0,
                    files_touched=set(),
                    total_insertions=0,
                    total_deletions=0
                )
            
            contributor = stats[email]
            contributor.commit_count += 1
            contributor.total_insertions += commit.insertions
            contributor.total_deletions += commit.deletions
            
            # Track commit dates
            if contributor.first_commit is None or commit.date < contributor.first_commit:
                contributor.first_commit = commit.date
            if contributor.last_commit is None or commit.date > contributor.last_commit:
                contributor.last_commit = commit.date
            
            # Get files touched in this commit
            try:
                git_commit = self.repo.commit(commit.hash)
                for file_path in git_commit.stats.files.keys():
                    if self._is_code_file(file_path):
                        contributor.files_touched.add(file_path)
            except Exception:
                pass
        
        self._contributor_stats = stats
        self._cache_valid = True
        
        return stats
    
    def get_repository_stats(self) -> RepositoryStats:
        """
        Get overall repository statistics
        
        Returns:
            RepositoryStats object
        """
        commits = self.get_commits()
        contributor_stats = self.get_contributor_stats()
        
        # Count tracked files
        tracked_files = []
        try:
            all_files = self.repo.git.ls_files().split('\n')
            tracked_files = [f for f in all_files if f and self._is_code_file(f)]
        except Exception as e:
            self._log('debug', f"Error getting tracked files: {e}")
        
        # Get active branch
        active_branch = 'unknown'
        try:
            active_branch = self.repo.active_branch.name
        except Exception:
            try:
                active_branch = self.repo.head.commit.hexsha[:7]
            except Exception:
                pass
        
        return RepositoryStats(
            path=str(self.repo_path),
            total_commits=len(commits),
            total_contributors=len(contributor_stats),
            total_files=len(tracked_files),
            first_commit_date=commits[-1].date if commits else None,
            last_commit_date=commits[0].date if commits else None,
            active_branch=active_branch,
            contributors=list(contributor_stats.values())
        )
    
    def get_file_contributors(self, file_path: str) -> List[str]:
        """
        Get list of contributors who modified a file
        
        Args:
            file_path: Relative path to file
        
        Returns:
            List of contributor names
        """
        history = self.get_file_history(file_path)
        if history:
            return history.contributors
        return []
    
    def get_contributor_entropy(self, file_path: str) -> float:
        """
        Calculate Shannon entropy for contributor distribution
        
        FIXED: Now uses proper Shannon entropy formula
        H = -Σ(p_i × log2(p_i))
        
        Higher entropy = more evenly distributed contributions (higher risk)
        Lower entropy = concentrated ownership (lower risk)
        
        Args:
            file_path: Relative path to file
        
        Returns:
            Entropy value in bits (typically 0 to ~4)
        """
        history = self.get_file_history(file_path)
        
        if not history or history.total_commits == 0:
            return 0.0
        
        # Count commits per author
        author_commits = Counter()
        for change in history.changes:
            author_commits[change.author] += 1
        
        # If no changes tracked, fall back to contributor count
        if not author_commits:
            # Assume equal distribution among known contributors
            n_contributors = len(history.contributors)
            if n_contributors <= 1:
                return 0.0
            # Maximum entropy for n contributors
            return math.log2(n_contributors)
        
        total = sum(author_commits.values())
        if total == 0:
            return 0.0
        
        # Shannon entropy: H = -Σ(p_i × log2(p_i))
        entropy = 0.0
        for count in author_commits.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy
    
    def get_commit_frequency(self, file_path: str) -> float:
        """
        Calculate average commits per month for a file
        
        Args:
            file_path: Relative path to file
        
        Returns:
            Commits per month
        """
        history = self.get_file_history(file_path)
        
        if not history:
            return 0.0
        
        return history.commit_frequency
    
    def get_code_churn(self, file_path: str) -> int:
        """
        Get total code churn (insertions + deletions) for a file
        
        Args:
            file_path: Relative path to file
        
        Returns:
            Total churn
        """
        history = self.get_file_history(file_path)
        
        if not history:
            return 0
        
        return history.churn
    
    def get_recent_activity(
        self, 
        file_path: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get recent activity metrics for a file
        
        Args:
            file_path: Relative path to file
            days: Number of days to look back
        
        Returns:
            Dictionary with recent activity metrics
        """
        since = datetime.now() - timedelta(days=days)
        commits = self.get_commits(file_path=file_path, since=since)
        
        if not commits:
            return {
                'period_days': days,
                'commit_count': 0,
                'contributor_count': 0,
                'contributors': [],
                'insertions': 0,
                'deletions': 0,
                'is_active': False
            }
        
        contributors = set()
        insertions = 0
        deletions = 0
        
        for commit in commits:
            contributors.add(commit.author_name)
            insertions += commit.insertions
            deletions += commit.deletions
        
        return {
            'period_days': days,
            'commit_count': len(commits),
            'contributor_count': len(contributors),
            'contributors': list(contributors),
            'insertions': insertions,
            'deletions': deletions,
            'is_active': len(commits) > 0
        }
    
    def get_file_age_days(self, file_path: str) -> int:
        """
        Get age of file in days since first commit
        
        Args:
            file_path: Relative path to file
        
        Returns:
            Age in days
        """
        history = self.get_file_history(file_path)
        
        if not history or not history.first_commit_date:
            return 0
        
        return max(0, (datetime.now() - history.first_commit_date).days)
    
    def get_days_since_last_change(self, file_path: str) -> int:
        """
        Get days since last modification
        
        Args:
            file_path: Relative path to file
        
        Returns:
            Days since last change
        """
        history = self.get_file_history(file_path)
        
        if not history or not history.last_commit_date:
            return 0
        
        return max(0, (datetime.now() - history.last_commit_date).days)
    
    def get_commit_gaps(self, file_path: str) -> List[int]:
        """
        Get gaps between commits in days
        Useful for detecting irregular maintenance patterns
        
        Args:
            file_path: Relative path to file
        
        Returns:
            List of gaps in days between consecutive commits
        """
        history = self.get_file_history(file_path)
        
        if not history or len(history.changes) < 2:
            return []
        
        gaps = []
        sorted_changes = sorted(history.changes, key=lambda c: c.commit_date)
        
        for i in range(1, len(sorted_changes)):
            gap = (sorted_changes[i].commit_date - sorted_changes[i-1].commit_date).days
            gaps.append(max(0, gap))
        
        return gaps
    
    def get_commit_volatility(self, file_path: str) -> float:
        """
        Calculate volatility as standard deviation of commit gaps
        
        FIXED: Now returns standard deviation instead of variance
        
        Args:
            file_path: Relative path to file
        
        Returns:
            Standard deviation of commit gaps in days
        """
        gaps = self.get_commit_gaps(file_path)
        
        if len(gaps) < 2:
            return 0.0
        
        # Calculate mean
        mean_gap = sum(gaps) / len(gaps)
        
        # Calculate variance
        variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
        
        # Return standard deviation (square root of variance)
        return math.sqrt(variance)
    
    def get_ddi_factors(self, file_path: str) -> Dict[str, Any]:
        """
        Get all factors needed for DDI calculation
        
        Args:
            file_path: Relative path to file
        
        Returns:
            Dictionary with all DDI-relevant metrics
        """
        history = self.get_file_history(file_path)
        
        if not history:
            return {
                'file_path': file_path,
                'found': False,
                'error': 'No history found',
                'total_commits': 0,
                'contributor_count': 0,
                'contributors': [],
                'age_days': 0,
                'days_since_last_change': 0,
                'commit_frequency': 0.0,
                'total_insertions': 0,
                'total_deletions': 0,
                'total_churn': 0,
                'contributor_entropy': 0.0,
                'avg_commit_gap_days': 0.0,
                'max_commit_gap_days': 0,
                'commit_gap_std_dev': 0.0,
                'recent_commits_30d': 0,
                'recent_contributors_30d': 0,
                'is_recently_active': False,
                'first_commit_date': None,
                'last_commit_date': None
            }
        
        commit_gaps = self.get_commit_gaps(file_path)
        recent_activity = self.get_recent_activity(file_path, days=30)
        
        # Calculate gap statistics
        avg_gap = 0.0
        max_gap = 0
        gap_std_dev = 0.0
        
        if commit_gaps:
            avg_gap = sum(commit_gaps) / len(commit_gaps)
            max_gap = max(commit_gaps)
            gap_std_dev = self.get_commit_volatility(file_path)
        
        return {
            'file_path': file_path,
            'found': True,
            
            # Basic counts
            'total_commits': history.total_commits,
            'contributor_count': history.contributor_count,
            'contributors': history.contributors,
            
            # Time-based
            'age_days': history.age_days,
            'days_since_last_change': self.get_days_since_last_change(file_path),
            'commit_frequency': round(history.commit_frequency, 4),
            
            # Churn
            'total_insertions': history.total_insertions,
            'total_deletions': history.total_deletions,
            'total_churn': history.churn,
            
            # Entropy (FIXED - now Shannon entropy)
            'contributor_entropy': round(self.get_contributor_entropy(file_path), 4),
            
            # Gaps (FIXED - now includes std_dev)
            'avg_commit_gap_days': round(avg_gap, 2),
            'max_commit_gap_days': max_gap,
            'commit_gap_std_dev': round(gap_std_dev, 2),
            # Keep variance for backward compatibility
            'commit_gap_variance': round(gap_std_dev ** 2, 2),
            
            # Recent activity
            'recent_commits_30d': recent_activity['commit_count'],
            'recent_contributors_30d': recent_activity['contributor_count'],
            'is_recently_active': recent_activity['is_active'],
            
            # Dates
            'first_commit_date': history.first_commit_date.isoformat() if history.first_commit_date else None,
            'last_commit_date': history.last_commit_date.isoformat() if history.last_commit_date else None
        }
    
    def analyze_all_files(
        self, 
        extensions: Optional[List[str]] = None,
        include_tests: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all code files in repository
        
        Args:
            extensions: File extensions to analyze
            include_tests: Whether to include test files
        
        Returns:
            Dictionary of file_path -> DDI factors
        """
        if extensions is None:
            extensions = list(self.CODE_EXTENSIONS)
        
        # Normalize extensions
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        extensions_set = set(ext.lower() for ext in extensions)
        
        results = {}
        
        try:
            # Get all tracked files
            tracked_files = self.repo.git.ls_files().split('\n')
            
            for file_path in tracked_files:
                if not file_path:
                    continue
                
                # Check extension
                file_ext = Path(file_path).suffix.lower()
                if file_ext not in extensions_set:
                    continue
                
                # Skip test files if not included
                if not include_tests and self._should_skip_path(file_path):
                    continue
                
                factors = self.get_ddi_factors(file_path)
                results[file_path] = factors
        
        except Exception as e:
            self._log('error', f"Error analyzing files: {e}")
        
        self._log('info', f"Analyzed {len(results)} files")
        return results
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._file_histories.clear()
        self._commits_cache.clear()
        self._contributor_stats.clear()
        self._cache_valid = False
    
    def __repr__(self) -> str:
        return f"GitAnalyzer(repo='{self.repo_path}')"


# Convenience functions
def analyze_repository(repo_path: str) -> RepositoryStats:
    """Quick analyze a repository"""
    analyzer = GitAnalyzer(repo_path)
    return analyzer.get_repository_stats()


def get_file_ddi_factors(repo_path: str, file_path: str) -> Dict[str, Any]:
    """Quick get DDI factors for a file"""
    analyzer = GitAnalyzer(repo_path)
    return analyzer.get_ddi_factors(file_path)
