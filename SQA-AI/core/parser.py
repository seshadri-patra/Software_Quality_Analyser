"""
Code Parser for SQA-AI
Extracts comprehensive code metrics from source files using AST and Radon

Metrics Extracted:
- LOC (Lines of Code)
- SLOC (Source Lines of Code)
- Comments and Comment Density
- Cyclomatic Complexity
- Maintainability Index
- Halstead Metrics
- Function/Class counts
- Import analysis

Multi-language:
- Python: full AST + Radon
- Non-python: basic parsing + heuristic complexity estimation (keyword counting)
"""

import ast
import re
import math
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict

# Radon imports for advanced metrics
try:
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit, mi_rank, h_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False


@dataclass
class FunctionMetrics:
    """Metrics for a single function/method"""
    name: str
    line_start: int
    line_end: int
    complexity: int
    parameters: int
    lines: int
    is_method: bool = False
    class_name: Optional[str] = None
    has_docstring: bool = False
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'complexity': self.complexity,
            'parameters': self.parameters,
            'lines': self.lines,
            'is_method': self.is_method,
            'class_name': self.class_name,
            'has_docstring': self.has_docstring,
            'is_async': self.is_async,
            'decorators': self.decorators
        }


@dataclass
class ClassMetrics:
    """Metrics for a single class"""
    name: str
    line_start: int
    line_end: int
    method_count: int
    wmc: int
    attributes: int
    instance_attributes: int = 0
    parents: List[str] = field(default_factory=list)
    has_docstring: bool = False
    decorators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'method_count': self.method_count,
            'wmc': self.wmc,
            'attributes': self.attributes,
            'instance_attributes': self.instance_attributes,
            'parents': self.parents,
            'depth_of_inheritance': len(self.parents),
            'has_docstring': self.has_docstring,
            'decorators': self.decorators
        }


@dataclass
class FileMetrics:
    """Complete metrics for a source file"""
    file_path: str
    language: str

    # Size metrics
    loc: int = 0
    sloc: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    docstring_lines: int = 0
    comment_density: float = 0.0

    # Complexity metrics
    cyclomatic_complexity: float = 0.0
    max_complexity: int = 0
    avg_complexity: float = 0.0
    complexity_rank: str = 'A'

    # Maintainability
    maintainability_index: float = 100.0
    mi_rank: str = 'A'

    # Halstead metrics
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    halstead_bugs: float = 0.0
    halstead_time: float = 0.0

    # Structure metrics
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    avg_function_length: float = 0.0
    max_function_length: int = 0
    min_function_length: int = 0

    # Code quality indicators
    has_docstrings: bool = False
    docstring_coverage: float = 0.0

    # Detailed breakdowns
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: List[ClassMetrics] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)

    # Analysis metadata
    parse_success: bool = True
    parse_error: Optional[str] = None
    analysis_time_ms: float = 0.0

    def _safe_round(self, value: float, decimals: int) -> float:
        if value is None or math.isnan(value) or math.isinf(value):
            return 0.0
        return round(value, decimals)

    def to_dict(self) -> Dict:
        return {
            'file_path': self.file_path,
            'language': self.language,
            'loc': self.loc,
            'sloc': self.sloc,
            'blank_lines': self.blank_lines,
            'comment_lines': self.comment_lines,
            'docstring_lines': self.docstring_lines,
            'comment_density': self._safe_round(self.comment_density, 4),
            'cyclomatic_complexity': self._safe_round(self.cyclomatic_complexity, 2),
            'max_complexity': self.max_complexity,
            'avg_complexity': self._safe_round(self.avg_complexity, 2),
            'complexity_rank': self.complexity_rank,
            'maintainability_index': self._safe_round(self.maintainability_index, 2),
            'mi_rank': self.mi_rank,
            'halstead_volume': self._safe_round(self.halstead_volume, 2),
            'halstead_difficulty': self._safe_round(self.halstead_difficulty, 2),
            'halstead_effort': self._safe_round(self.halstead_effort, 2),
            'halstead_bugs': self._safe_round(self.halstead_bugs, 4),
            'halstead_time': self._safe_round(self.halstead_time, 2),
            'function_count': self.function_count,
            'class_count': self.class_count,
            'import_count': self.import_count,
            'avg_function_length': self._safe_round(self.avg_function_length, 2),
            'max_function_length': self.max_function_length,
            'min_function_length': self.min_function_length,
            'has_docstrings': self.has_docstrings,
            'docstring_coverage': self._safe_round(self.docstring_coverage, 2),
            'functions': [f.to_dict() for f in self.functions],
            'classes': [c.to_dict() for c in self.classes],
            'imports': self.imports,
            'parse_success': self.parse_success,
            'parse_error': self.parse_error,
            'analysis_time_ms': self._safe_round(self.analysis_time_ms, 2)
        }


class ASTVisitor(ast.NodeVisitor):
    """Custom AST visitor to extract detailed code structure"""

    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.functions: List[FunctionMetrics] = []
        self.classes: List[ClassMetrics] = []
        self.imports: List[str] = []
        self.current_class: Optional[str] = None
        self.class_methods: Dict[str, List[FunctionMetrics]] = defaultdict(list)
        self.class_instance_attributes: Dict[str, set] = defaultdict(set)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ''
        for alias in node.names:
            if alias.name == '*':
                self.imports.append(f"{module}.*")
            else:
                self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name

        parents = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                parents.append(base.id)
            elif isinstance(base, ast.Attribute):
                parents.append(base.attr)
            elif isinstance(base, ast.Subscript):
                if isinstance(base.value, ast.Name):
                    parents.append(base.value.id)

        decorators = self._get_decorators(node)
        has_docstring = self._has_docstring(node)

        self.generic_visit(node)

        # count class-level attributes
        attr_count = 0
        for item in node.body:
            if isinstance(item, ast.Assign):
                for t in item.targets:
                    if isinstance(t, ast.Name):
                        attr_count += 1
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    attr_count += 1

        methods = self.class_methods.get(node.name, [])
        wmc = sum(m.complexity for m in methods)
        instance_attr_count = len(self.class_instance_attributes.get(node.name, set()))

        self.classes.append(ClassMetrics(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            method_count=len(methods),
            wmc=wmc,
            attributes=attr_count,
            instance_attributes=instance_attr_count,
            parents=parents,
            has_docstring=has_docstring,
            decorators=decorators
        ))

        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node, is_async=True)
        self.generic_visit(node)

    def _process_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool) -> None:
        complexity = self._calculate_complexity(node)

        params = len(node.args.args)
        if self.current_class and params > 0:
            first = node.args.args[0].arg
            if first in ('self', 'cls'):
                params -= 1

        decorators = self._get_decorators(node)
        has_docstring = self._has_docstring(node)

        if self.current_class and node.name == '__init__':
            self._extract_instance_attributes(node)

        fm = FunctionMetrics(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            complexity=complexity,
            parameters=params,
            lines=(node.end_lineno or node.lineno) - node.lineno + 1,
            is_method=self.current_class is not None,
            class_name=self.current_class,
            has_docstring=has_docstring,
            is_async=is_async,
            decorators=decorators
        )

        self.functions.append(fm)

        if self.current_class:
            self.class_methods[self.current_class].append(fm)

    def _get_decorators(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]) -> List[str]:
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(dec.func.attr)
        return decorators

    def _has_docstring(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef]) -> bool:
        if not node.body:
            return False
        first = node.body[0]
        return (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        )

    def _extract_instance_attributes(self, node: ast.FunctionDef) -> None:
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == 'self'
                    ):
                        self.class_instance_attributes[self.current_class].add(target.attr)
            elif isinstance(child, ast.AnnAssign):
                t = child.target
                if (
                    isinstance(t, ast.Attribute)
                    and isinstance(t.value, ast.Name)
                    and t.value.id == 'self'
                ):
                    self.class_instance_attributes[self.current_class].add(t.attr)

    def _calculate_complexity(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                complexity += 1
            elif isinstance(child, ast.While):
                complexity += 1
            elif isinstance(child, ast.For):
                complexity += 1
            elif isinstance(child, ast.AsyncFor):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.IfExp):
                complexity += 1
            elif hasattr(ast, 'Match') and isinstance(child, ast.Match):
                complexity += len(child.cases)
        return complexity


class CodeParser:
    """
    Main parser class for extracting code metrics
    Supports Python with extensibility for other languages
    """

    MIN_LINES_FOR_ANALYSIS = 3
    MAX_FILE_SIZE = 5 * 1024 * 1024

    def __init__(self):
        self._logger = None
        self._init_logger()

        if not RADON_AVAILABLE:
            self._log('warning', "Radon not installed. Some metrics will use fallback calculations. Run: pip install radon")

    def _init_logger(self) -> None:
        try:
            from utils.logger import get_logger
            self._logger = get_logger(__name__)
        except ImportError:
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from utils.logger import get_logger
                self._logger = get_logger(__name__)
            except ImportError:
                self._logger = None

    def _log(self, level: str, message: str) -> None:
        if self._logger:
            getattr(self._logger, level)(message)

    def parse_file(self, file_path: str) -> FileMetrics:
        import time
        start_time = time.time()

        path = Path(file_path)
        metrics = FileMetrics(
            file_path=str(path),
            language=self._detect_language(path)
        )

        validation_error = self._validate_file(path)
        if validation_error:
            metrics.parse_success = False
            metrics.parse_error = validation_error
            metrics.analysis_time_ms = (time.time() - start_time) * 1000
            return metrics

        try:
            content = self._read_file(path)
            if content is None:
                metrics.parse_success = False
                metrics.parse_error = "Could not read file"
                metrics.analysis_time_ms = (time.time() - start_time) * 1000
                return metrics
        except Exception as e:
            metrics.parse_success = False
            metrics.parse_error = f"Read error: {str(e)}"
            metrics.analysis_time_ms = (time.time() - start_time) * 1000
            return metrics

        if not content or not content.strip():
            lines = content.splitlines() if content else []
            metrics.loc = len(lines)
            metrics.blank_lines = len(lines)
            metrics.sloc = 0
            metrics.comment_lines = 0
            metrics.docstring_lines = 0
            metrics.comment_density = 0.0
            metrics.analysis_time_ms = (time.time() - start_time) * 1000
            return metrics

        lines = content.splitlines()

        if len(lines) < self.MIN_LINES_FOR_ANALYSIS:
            if metrics.language == 'python':
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    self._count_lines_python(content, metrics)
                    metrics.parse_success = False
                    metrics.parse_error = f"Syntax error at line {e.lineno}: {e.msg}"
                    metrics.analysis_time_ms = (time.time() - start_time) * 1000
                    return metrics
                except Exception as e:
                    self._count_lines_python(content, metrics)
                    metrics.parse_success = False
                    metrics.parse_error = f"AST parse error: {str(e)}"
                    metrics.analysis_time_ms = (time.time() - start_time) * 1000
                    return metrics

                self._count_lines_python(content, metrics)
            else:
                metrics.loc = len(lines)
                metrics.sloc = len([l for l in lines if l.strip()])
                metrics.blank_lines = metrics.loc - metrics.sloc

            metrics.analysis_time_ms = (time.time() - start_time) * 1000
            return metrics

        if metrics.language == 'python':
            self._parse_python(content, metrics)
        else:
            self._parse_basic(content, metrics)

        metrics.analysis_time_ms = (time.time() - start_time) * 1000
        self._log('debug', f"Parsed {file_path}: CC={metrics.cyclomatic_complexity}, MI={metrics.maintainability_index}")
        return metrics

    def _validate_file(self, path: Path) -> Optional[str]:
        if not path.exists():
            return "File does not exist"
        if not path.is_file():
            return "Path is not a file"

        try:
            size = path.stat().st_size
            if size > self.MAX_FILE_SIZE:
                return f"File too large ({size} bytes > {self.MAX_FILE_SIZE} bytes)"
        except OSError as e:
            return f"Cannot access file: {e}"

        return None

    def _detect_language(self, path: Path) -> str:
        ext_map = {
            '.py': 'python',
            '.pyw': 'python',
            '.pyi': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.mjs': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.hxx': 'cpp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.rs': 'rust',
            '.kt': 'kotlin',
            '.kts': 'kotlin',
            '.swift': 'swift',
            '.scala': 'scala',
            '.cs': 'csharp'
        }
        return ext_map.get(path.suffix.lower(), 'unknown')

    def _read_file(self, path: Path) -> Optional[str]:
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'ascii']
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self._log('error', f"Error reading {path}: {e}")
                return None
        self._log('error', f"Could not decode file with any encoding: {path}")
        return None

    def _has_inline_comment(self, line: str) -> bool:
        in_string = False
        string_char = None
        for i, ch in enumerate(line):
            if ch in ('"', "'") and (i == 0 or line[i - 1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = ch
                elif ch == string_char:
                    in_string = False
            elif ch == '#' and not in_string:
                return True
        return False

    def _count_lines_python(self, content: str, metrics: FileMetrics) -> None:
        lines = content.splitlines()
        metrics.loc = len(lines)

        blank_count = 0
        comment_count = 0
        inline_comment_count = 0
        docstring_count = 0

        in_docstring = False
        docstring_char = None

        for line in lines:
            stripped = line.strip()

            if not stripped:
                blank_count += 1
                continue

            if in_docstring:
                docstring_count += 1
                if docstring_char and docstring_char in stripped:
                    in_docstring = False
                    docstring_char = None
                continue

            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_char = stripped[:3]
                docstring_count += 1
                remaining = stripped[3:]
                if docstring_char not in remaining:
                    in_docstring = True
                continue

            if stripped.startswith('#'):
                comment_count += 1
                continue

            if '#' in stripped and self._has_inline_comment(stripped):
                inline_comment_count += 1

        metrics.blank_lines = blank_count
        metrics.comment_lines = comment_count + inline_comment_count
        metrics.docstring_lines = docstring_count
        metrics.sloc = max(0, metrics.loc - blank_count - metrics.comment_lines - docstring_count)

        total_documentation = metrics.comment_lines + docstring_count
        metrics.comment_density = (total_documentation / metrics.sloc) if metrics.sloc > 0 else 0.0

    def _parse_python(self, content: str, metrics: FileMetrics) -> None:
        self._count_lines_python(content, metrics)

        try:
            tree = ast.parse(content)
            visitor = ASTVisitor(content.splitlines())
            visitor.visit(tree)

            metrics.functions = visitor.functions
            metrics.classes = visitor.classes
            metrics.imports = list(set(visitor.imports))
            metrics.function_count = len(visitor.functions)
            metrics.class_count = len(visitor.classes)
            metrics.import_count = len(metrics.imports)

            if visitor.functions:
                lengths = [f.lines for f in visitor.functions]
                metrics.avg_function_length = sum(lengths) / len(lengths)
                metrics.max_function_length = max(lengths)
                metrics.min_function_length = min(lengths)

                with_docstrings = sum(1 for f in visitor.functions if f.has_docstring)
                metrics.docstring_coverage = with_docstrings / len(visitor.functions)
                metrics.has_docstrings = with_docstrings > 0

        except SyntaxError as e:
            metrics.parse_success = False
            metrics.parse_error = f"Syntax error at line {e.lineno}: {e.msg}"
            self._calculate_fallback_complexity(metrics)
            return
        except Exception as e:
            metrics.parse_success = False
            metrics.parse_error = f"AST parse error: {str(e)}"
            self._calculate_fallback_complexity(metrics)
            return

        if RADON_AVAILABLE:
            self._extract_radon_metrics(content, metrics)
        else:
            self._calculate_fallback_complexity(metrics)

    def _safe_float(self, value: Any) -> float:
        if value is None:
            return 0.0
        try:
            f = float(value)
            if math.isnan(f) or math.isinf(f):
                return 0.0
            return f
        except (TypeError, ValueError):
            return 0.0

    def _extract_radon_metrics(self, content: str, metrics: FileMetrics) -> None:
        try:
            cc_results = cc_visit(content)
            if cc_results:
                complexities = [b.complexity for b in cc_results]
                metrics.cyclomatic_complexity = sum(complexities)
                metrics.max_complexity = max(complexities) if complexities else 0
                metrics.avg_complexity = (sum(complexities) / len(complexities)) if complexities else 0.0

                avg_cc = metrics.avg_complexity
                if avg_cc <= 5:
                    metrics.complexity_rank = 'A'
                elif avg_cc <= 10:
                    metrics.complexity_rank = 'B'
                elif avg_cc <= 20:
                    metrics.complexity_rank = 'C'
                elif avg_cc <= 30:
                    metrics.complexity_rank = 'D'
                elif avg_cc <= 40:
                    metrics.complexity_rank = 'E'
                else:
                    metrics.complexity_rank = 'F'
            else:
                metrics.cyclomatic_complexity = 1
                metrics.max_complexity = 1
                metrics.avg_complexity = 1.0
                metrics.complexity_rank = 'A'
        except Exception:
            self._calculate_fallback_complexity(metrics)

        try:
            mi = mi_visit(content, multi=False)
            if mi is not None and not math.isnan(mi) and not math.isinf(mi):
                metrics.maintainability_index = max(0, min(100, mi))
                metrics.mi_rank = mi_rank(mi)
            else:
                self._calculate_fallback_mi(metrics)
        except Exception:
            self._calculate_fallback_mi(metrics)

        try:
            h_results = h_visit(content)
            if h_results:
                for result in h_results:
                    if hasattr(result, 'total') and result.total:
                        h = result.total
                        metrics.halstead_volume = self._safe_float(getattr(h, 'volume', 0))
                        metrics.halstead_difficulty = self._safe_float(getattr(h, 'difficulty', 0))
                        metrics.halstead_effort = self._safe_float(getattr(h, 'effort', 0))
                        metrics.halstead_bugs = self._safe_float(getattr(h, 'bugs', 0))
                        metrics.halstead_time = self._safe_float(getattr(h, 'time', 0))
                        break
        except Exception:
            pass

    def _calculate_fallback_complexity(self, metrics: FileMetrics) -> None:
        if metrics.functions:
            complexities = [f.complexity for f in metrics.functions]
            metrics.cyclomatic_complexity = sum(complexities)
            metrics.max_complexity = max(complexities)
            metrics.avg_complexity = sum(complexities) / len(complexities)
        else:
            metrics.cyclomatic_complexity = 1
            metrics.max_complexity = 1
            metrics.avg_complexity = 1.0

        avg = metrics.avg_complexity
        if avg <= 5:
            metrics.complexity_rank = 'A'
        elif avg <= 10:
            metrics.complexity_rank = 'B'
        elif avg <= 20:
            metrics.complexity_rank = 'C'
        else:
            metrics.complexity_rank = 'D'

        self._calculate_fallback_mi(metrics)

    def _calculate_fallback_mi(self, metrics: FileMetrics) -> None:
        loc = max(metrics.sloc, 1)
        cc = max(metrics.cyclomatic_complexity, 1)

        try:
            mi = 171 - 0.23 * cc - 16.2 * math.log(loc)
            mi = max(0, min(100, mi))
        except Exception:
            mi = 50.0

        metrics.maintainability_index = mi
        if mi >= 65:
            metrics.mi_rank = 'A'
        elif mi >= 45:
            metrics.mi_rank = 'B'
        else:
            metrics.mi_rank = 'C'

    def _parse_basic(self, content: str, metrics: FileMetrics) -> None:
        """
        Basic parsing for non-Python files:
        - LOC/SLOC/comments
        - heuristic complexity estimation
        - fallback MI
        """
        lines = content.splitlines()
        metrics.loc = len(lines)

        blank_count = 0
        comment_count = 0

        single_comment = {
            'javascript': '//', 'java': '//', 'cpp': '//', 'c': '//',
            'go': '//', 'rust': '//', 'kotlin': '//', 'swift': '//',
            'scala': '//', 'csharp': '//', 'ruby': '#', 'php': '//',
            'typescript': '//'
        }
        comment_prefix = single_comment.get(metrics.language, '//')

        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_count += 1
            elif stripped.startswith(comment_prefix) or stripped.startswith('#'):
                comment_count += 1

        metrics.blank_lines = blank_count
        metrics.comment_lines = comment_count
        metrics.sloc = max(0, metrics.loc - blank_count - comment_count)
        metrics.comment_density = (comment_count / metrics.sloc) if metrics.sloc > 0 else 0.0

        # ---- IMPORTANT CHANGE: complexity estimate (so non-python can be high DDI) ----
        complexity_keywords = [
            "if", "else if", "for", "while", "switch", "case", "catch", "try",
            "&&", "||", "?", "elif"
        ]
        text = content.lower()
        complexity = 1
        for kw in complexity_keywords:
            complexity += text.count(kw)

        # rough structure estimates
        if metrics.language in ("javascript", "typescript"):
            metrics.function_count = len(re.findall(r"\bfunction\b|\=\s*\(.*\)\s*=>", content))
            metrics.class_count = len(re.findall(r"\bclass\s+\w+", content))
            metrics.import_count = len(re.findall(r"\bimport\b|\brequire\s*\(", content))
        elif metrics.language == "java":
            metrics.function_count = len(re.findall(r"\b(public|private|protected)\b.*\(", content))
            metrics.class_count = len(re.findall(r"\bclass\s+\w+|\binterface\s+\w+", content))
            metrics.import_count = len(re.findall(r"^\s*import\s+", content, re.MULTILINE))

        metrics.cyclomatic_complexity = float(complexity)
        if metrics.function_count > 0:
            metrics.avg_complexity = float(complexity) / float(metrics.function_count)
        else:
            metrics.avg_complexity = float(complexity)

        metrics.max_complexity = int(metrics.avg_complexity * 1.5) if metrics.avg_complexity else 1

        avg = metrics.avg_complexity
        if avg <= 5:
            metrics.complexity_rank = 'A'
        elif avg <= 10:
            metrics.complexity_rank = 'B'
        elif avg <= 20:
            metrics.complexity_rank = 'C'
        else:
            metrics.complexity_rank = 'D'

        self._calculate_fallback_mi(metrics)

    def parse_directory(self, directory: str, extensions: Optional[List[str]] = None, use_file_handler: bool = True) -> List[FileMetrics]:
        if extensions is None:
            extensions = ['.py']

        results: List[FileMetrics] = []
        dir_path = Path(directory)

        if not dir_path.exists():
            self._log('error', f"Directory does not exist: {directory}")
            return results

        if use_file_handler:
            try:
                from utils.file_handler import FileHandler
                handler = FileHandler(directory)
                files = handler.get_all_files(extensions)
                for file_path in files:
                    results.append(self.parse_file(str(file_path)))
                return results
            except ImportError:
                self._log('debug', "FileHandler not available, using basic file discovery")

        skip_dirs = {'__pycache__', '.git', 'venv', 'env', '.env',
                     'node_modules', '.tox', 'build', 'dist', '.idea', '.vscode'}

        for ext in extensions:
            ext = ext if ext.startswith('.') else f'.{ext}'
            for file_path in dir_path.rglob(f'*{ext}'):
                if any(skip in file_path.parts for skip in skip_dirs):
                    continue
                results.append(self.parse_file(str(file_path)))

        return results


def parse_file(file_path: str) -> FileMetrics:
    parser = CodeParser()
    return parser.parse_file(file_path)


def parse_directory(directory: str, extensions: Optional[List[str]] = None) -> List[FileMetrics]:
    parser = CodeParser()
    return parser.parse_directory(directory, extensions)
