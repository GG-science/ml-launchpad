# Contributing to ml-launchpad

## Setup

```bash
git clone https://github.com/GG-science/ml-launchpad.git
cd ml-launchpad
uv sync --all-extras
```

## Running tests

```bash
uv run pytest tests/ -v
```

## Adding new model types

1. Create `src/models/your_model.py` with a `run_your_model()` function
2. Return a result dataclass (see `src/models/base.py`)
3. Add MLflow logging in `src/experiments/tracker.py`
4. Add tests in `tests/test_models.py`
5. Add a command section in `CLAUDE.md`

## Code style

- Type hints on all function signatures
- Docstrings on public functions
- Config via `config/project.yml` — no hardcoded paths
- Tests run without network access or GPU
