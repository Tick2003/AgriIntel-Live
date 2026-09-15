---
name: Bug report
about: Report a broken feature, data pipeline failure, or agent error
title: '[BUG] '
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**Component**
Which part of the system is affected? (tick all that apply)
- [ ] Streamlit UI (`app/`)
- [ ] Data pipeline / ETL (`etl/`)
- [ ] Intelligence agents (`agents/`)
- [ ] Database layer (`database/`)
- [ ] GitHub Actions CI/CD (`.github/workflows/`)
- [ ] FastAPI backend (`api_server.py`)

**To Reproduce**
Steps to reproduce the behavior:
1. ...
2. ...
3. See error

**Expected behavior**
A clear description of what you expected to happen.

**Logs / Error Output**
Paste any relevant error messages, stack traces, or GitHub Actions log snippets here.
```
<paste logs here>
```

**Environment**
- OS:
- Python version:
- Key package versions (`pip show pandas numpy xgboost` output):
- `AGRIINTEL_ENV` value:

**Additional context**
Any other context about the problem.
