import sys
from pathlib import Path

# Extra safety: ensure project root is importable even if pytest discovery is odd
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.parser import CodeParser


def write_temp_file(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_parser_extracts_basic_metrics(tmp_path: Path):
    code = """
def add(a, b):
    \"\"\"Add two numbers\"\"\"
    if a > 0 and b > 0:
        return a + b
    return a - b
"""
    f = write_temp_file(tmp_path, "sample.py", code)

    parser = CodeParser()
    metrics = parser.parse_file(str(f))

    assert metrics.parse_success is True
    assert metrics.parse_error is None
    assert metrics.language == "python"
    assert metrics.loc > 0
    assert metrics.sloc >= 1
    assert metrics.function_count >= 1
    assert metrics.cyclomatic_complexity >= 1
    assert 0 <= metrics.maintainability_index <= 100


def test_parser_detects_functions_and_docstrings(tmp_path: Path):
    code = """
def f1():
    return 1

def f2():
    \"\"\"doc\"\"\"
    return 2
"""
    f = write_temp_file(tmp_path, "doc_test.py", code)

    parser = CodeParser()
    m = parser.parse_file(str(f))

    assert m.parse_success is True
    assert m.parse_error is None
    assert m.function_count == 2
    assert 0.0 <= m.docstring_coverage <= 1.0
    assert m.docstring_coverage == 0.5


def test_parser_handles_syntax_error(tmp_path: Path):
    bad = "def broken(:\n    pass\n"
    f = write_temp_file(tmp_path, "broken.py", bad)

    parser = CodeParser()
    m = parser.parse_file(str(f))

    assert m.parse_success is False
    assert m.parse_error is not None
    assert "syntax" in m.parse_error.lower()


def test_parser_handles_empty_file(tmp_path: Path):
    f = write_temp_file(tmp_path, "empty.py", "")

    parser = CodeParser()
    m = parser.parse_file(str(f))

    assert m.parse_success is True
    assert m.parse_error is None
    assert m.loc == 0
    assert m.sloc == 0
    assert m.function_count == 0
    assert m.class_count == 0


def test_parser_handles_whitespace_only_file(tmp_path: Path):
    f = write_temp_file(tmp_path, "whitespace.py", "   \n\n  \n")

    parser = CodeParser()
    m = parser.parse_file(str(f))

    assert m.parse_success is True
    assert m.parse_error is None
    assert m.sloc == 0
    assert m.function_count == 0
    assert m.class_count == 0


def test_parser_counts_imports_individual_symbols(tmp_path: Path):
    code = """
import os
import sys
from pathlib import Path
from typing import List, Dict

def main():
    pass
"""
    f = write_temp_file(tmp_path, "imports_test.py", code)

    parser = CodeParser()
    m = parser.parse_file(str(f))

    assert m.parse_success is True
    # os, sys, pathlib.Path, typing.List, typing.Dict
    assert m.import_count == 5


def test_parser_parse_directory_empty(tmp_path: Path):
    parser = CodeParser()
    results = parser.parse_directory(str(tmp_path), extensions=[".py"], use_file_handler=False)

    assert isinstance(results, list)
    assert len(results) == 0
    