# Changelog

## 0.20.1

**Bug fix**: Fix `TypeError: issubclass() arg 1 must be a class` on Python 3.13.

- **Root cause**: `voyager.analysis()` used bare `issubclass(schema, BaseModel)` on values returned by `get_core_types()`. When a route's `response_model` resolves to a parameterized generic (e.g. `dict[X, set[Y]]`, `Callable[[int], str]`), the result is a `types.GenericAlias`, not a class.
- **Python version difference**:
  - Python 3.12: `issubclass(GenericAlias, BaseModel)` returns `False` (no error)
  - Python 3.13: raises `TypeError: issubclass() arg 1 must be a class`
- **Fix**: Replace `issubclass` with `safe_issubclass` in `voyager.py`, which catches `TypeError` gracefully.
- **Typical trigger**: A FastAPI route using a PEP 695 type alias (e.g. `type ResourceActionDict = dict[K, set[V]]`) as return annotation, with FastAPI inferring `response_model` from it.

## 0.20.0

- feat: prevent event propagation on double-click for edge interactions
- feat: show dataloader source code sidebar on edge double-click in ER diagram
