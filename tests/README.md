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
├── django_ninja/          # Django Ninja-specific test examples
│   ├── __init__.py
│   ├── demo.py           # Demo Django Ninja application
│   └── embedding.py      # Example of embedding voyager in Django Ninja
├── litestar/              # Litestar-specific test examples
│   ├── __init__.py
│   ├── demo.py           # Demo Litestar application
│   └── embedding.py      # Example of embedding voyager in Litestar
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
- Includes `Member`, `Sprint`, `Story`, `Task` models
- Includes pydantic-resolve BaseEntity and diagram

### Framework-Specific Tests

Each supported framework has its own directory with similar structure:

#### FastAPI (`fastapi/`)
- `demo.py` - Example FastAPI application with various route patterns
- `embedding.py` - Shows how to mount voyager into FastAPI app
- Demonstrates pydantic-resolve integration

#### Django Ninja (`django_ninja/`)
- `demo.py` - Django Ninja version of the demo application
- Uses `NinjaAPI` instead of `FastAPI`
- Shows similar functionality with framework-specific differences

#### Litestar (`litestar/`)
- `demo.py` - Litestar version using Controller pattern
- Uses `@get` decorator and Controller classes
- Demonstrates framework-specific patterns

## Running Tests

Run all tests:
```bash
uv run pytest tests/
```

Run specific test file:
```bash
uv run pytest tests/test_analysis.py
```

Run framework-specific demos:
```bash
# FastAPI
python tests/fastapi/embedding.py

# Django Ninja (requires Django setup)
# See tests/django_ninja/embedding.py for integration instructions

# Litestar
python tests/litestar/embedding.py
```

## Key Differences Between Frameworks

### FastAPI
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/path", response_model=Model)
def route():
    return Model()

app.mount("/voyager", create_voyager(app))
```

### Django Ninja
```python
from ninja import NinjaAPI
api = NinjaAPI()

@api.get("/path")
def route(request) -> Model:
    return Model()

# Integrated via Django urls.py
# See embedding.py for details
```

### Litestar
```python
from litestar import Litestar, Controller

class MyController(Controller):
    @get("/path")
    def path(self) -> Model:
        return Model()

app = Litestar(route_handlers=[MyController])
app.mount("/voyager", voyager_app)
```

## Adding Tests for New Frameworks

When adding support for a new framework:

1. Create directory: `tests/<framework_name>/`
2. Add `__init__.py`
3. Create `demo.py` with example routes
   - Reuse `tests.service.schema` models
   - Mirror FastAPI demo functionality
   - Use framework-specific patterns
4. Create `embedding.py` with voyager integration
5. Add introspector in `src/fastapi_voyager/introspectors/`
6. Update `Voyager._get_introspector()` to detect framework
7. Add framework-specific tests if needed

All frameworks share the same:
- Pydantic models from `tests.service.schema`
- pydantic-resolve BaseEntity diagram
- Testing patterns

