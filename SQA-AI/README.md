# SQA-AI — Smart Software Quality Analyzer (MVP)

SQA-AI is a lightweight, local-first software quality analyzer.
It extracts standard static code metrics (LOC/SLOC, complexity, MI, Halstead, doc coverage),
stores history in SQLite, and computes the **DDI** feature (Developer-Centric Decay Index) to
estimate future risk using a transparent, explainable score.

## What this MVP includes
- Python static analysis (AST + Radon)
- File-level metrics: SLOC, Cyclomatic Complexity, Maintainability Index, Halstead, imports, functions/classes
- DDI score (currently using simplified git factors for MVP; Git integration exists via `core/git_analyzer.py`)
- Recommendations engine (rule-based + function/class checks)
- SQLite database storage (projects, files, metrics, DDI, analyses, recommendations, history)
- Streamlit dashboard (overview, files, DDI, recommendations, trends)

## Requirements
- Python 3.10+
- Git (optional for now; required when enabling GitAnalyzer)

Install dependencies:
```bash
pip install -r requirements.txt
