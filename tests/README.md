# Tests Directory Structure

This directory contains all tests for fastapi-voyager.

## Directory Structure

```
tests/
├── __init__.py
├── test_*.py              # Unit tests for individual modules
├── service/               # Shared test utilities (reused across frameworks)
│   ├── __init__.py
│   └── schema/           # Shared schema definitions
├── fastapi/              # FastAPI-specific test examples
│   ├── __init__.py
│   ├── demo.py           # Demo FastAPI application
│   ├── demo_anno.py     # Demo with annotations
│   └── embedding.py      # Example of embedding voyager in FastAPI app
└── README.md
```

## Test Organization

### Unit Tests (`test_*.py`)
- `test_analysis.py` - Core voyager analysis functionality
- `test_filter.py` - Graph filtering logic
- `test_generic.py` - Generic type handling
- `test_import.py` - Import validation
- `test_module.py` - Module tree building
- `test_resolve_util_impl.py` - Pydantic resolve utilities
- `test_type_helper.py` - Type extraction and analysis

### Shared Utilities (`service/`)
- Reusable test utilities and schema definitions
- Used across different framework tests
- Contains shared Pydantic models and test data

### Framework-Specific Tests (`fastapi/`, `django_ninja/`, `litestar/`, etc.)
- Example applications for each supported framework
- Integration tests for framework introspectors
- Can be run independently or as part of the full test suite

## Adding Tests for New Frameworks

When adding support for a new framework (e.g., Django Ninja, Litestar):

1. Create a new directory: `tests/<framework_name>/`
2. Add example applications and tests
3. Reuse utilities from `service/` where possible
4. Follow the same structure as `tests/fastapi/`

Example:
```
tests/
├── django_ninja/
│   ├── __init__.py
│   ├── demo.py
│   └── test_introspector.py
└── litestar/
    ├── __init__.py
    ├── demo.py
    └── test_introspector.py
```

## Running Tests

Run all tests:
```bash
uv run pytest tests/
```

Run specific test file:
```bash
uv run pytest tests/test_analysis.py
```

Run framework-specific tests:
```bash
uv run pytest tests/fastapi/
```
