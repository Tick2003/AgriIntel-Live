## Description

Please include a summary of the change and which issue is fixed. Include relevant motivation and context.

Fixes # (issue)

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?

Describe the tests you ran and how to reproduce them.

- [ ] `pytest -m "not integration" -q` — all unit tests pass
- [ ] `ruff check .` — zero lint errors
- [ ] Manual test on Streamlit UI (if UI changes)

## Checklist

- [ ] My code follows the project style guidelines (see `CONTRIBUTING.md`)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have updated the documentation (README / ARCHITECTURE / CHANGELOG) if needed
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally
- [ ] Any new ETL sources go through `DataReliabilityAgent.validate_batch()`
- [ ] No new `print()` calls — all output uses `logging.getLogger(__name__)`
- [ ] If I touched the data pipeline, I verified it works with `python etl/data_loader.py --skip-swarm`
