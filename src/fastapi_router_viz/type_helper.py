import inspect
import os
from pydantic import BaseModel
from typing import get_origin, get_args, Union, Annotated, Any
from fastapi_router_viz.type import FieldInfo
from types import UnionType


def _is_optional(annotation):
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Union and type(None) in args:
        return True
    return False


def _is_list(annotation):
    return getattr(annotation, "__origin__", None) == list


def shelling_type(type):
    while _is_optional(type) or _is_list(type):
        type = type.__args__[0]
    return type


def full_class_name(cls):
    return f"{cls.__module__}.{cls.__qualname__}"


def get_core_types(tp):
    """
    - get the core type
    - always return a tuple of core types
    """
    if tp is type(None):
        return tuple()

    # 1. Unwrap list layers
    def _shell_list(_tp):
        while _is_list(_tp):
            args = getattr(_tp, "__args__", ())
            if args:
                _tp = args[0]
            else:
                break
        return _tp
    
    tp = _shell_list(tp)

    if tp is type(None): # check again
        return tuple()

    while True:
        orig = get_origin(tp)

        if orig in (Union, UnionType):
            args = list(get_args(tp))
            non_none = [a for a in args if a is not type(None)]  # noqa: E721
            has_none = len(non_none) != len(args)
            # Optional[T] case -> keep unwrapping (exactly one real type + None)
            if has_none and len(non_none) == 1:
                tp = non_none[0]
                tp = _shell_list(tp)
                continue
            # General union: return all non-None members (order preserved)
            if non_none:
                return tuple(non_none)
            return tuple()
        break

    # single concrete type
    return (tp,)


def get_type_name(anno):
    def name_of(tp):
        origin = get_origin(tp)
        args = get_args(tp)

        # Annotated[T, ...] -> T
        if origin is Annotated:
            return name_of(args[0]) if args else 'Annotated'

        # Union / Optional
        if origin is Union:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1 and len(args) == 2:
                return f"Optional[{name_of(non_none[0])}]"
            return f"Union[{', '.join(name_of(a) for a in args)}]"

        # Parametrized generics
        if origin is not None:
            origin_name_map = {
                list: 'List',
                dict: 'Dict',
                set: 'Set',
                tuple: 'Tuple',
                frozenset: 'FrozenSet',
            }
            origin_name = origin_name_map.get(origin)
            if origin_name is None:
                origin_name = getattr(origin, '__name__', None) or str(origin).replace('typing.', '')
            if args:
                return f"{origin_name}[{', '.join(name_of(a) for a in args)}]"
            return origin_name

        # Non-generic leaf types
        if tp is Any:
            return 'Any'
        if tp is None or tp is type(None):
            return 'None'
        if isinstance(tp, type):
            return tp.__name__

        # ForwardRef
        fwd = getattr(tp, '__forward_arg__', None) or getattr(tp, 'arg', None)
        if fwd:
            return str(fwd)

        # Fallback clean string
        return str(tp).replace('typing.', '').replace('<class ', '').replace('>', '').replace("'", '')

    return name_of(anno)

def is_inheritance_of_pydantic_base(cls):
        return issubclass(cls, BaseModel) and cls is not BaseModel


def get_bases_fields(schemas: list[type[BaseModel]]) -> set[str]:
    """Collect field names from a list of BaseModel subclasses (their model_fields keys)."""
    fields: set[str] = set()
    for schema in schemas:
        for k, _ in getattr(schema, 'model_fields', {}).items():
            fields.add(k)
    return fields


def get_pydantic_fields(schema: type[BaseModel], bases_fields: set[str]) -> list[FieldInfo]:
    """Extract pydantic model fields with metadata.

    Parameters:
        schema: The pydantic BaseModel subclass to inspect.
        bases_fields: Set of field names that come from base classes (for from_base marking).

    Returns:
        A list of FieldInfo objects describing the schema's direct fields.
    """

    def _is_object(anno):  # internal helper, previously a method on Analytics
        _types = get_core_types(anno)
        return any(is_inheritance_of_pydantic_base(t) for t in _types if t)

    fields: list[FieldInfo] = []
    for k, v in schema.model_fields.items():
        anno = v.annotation
        fields.append(FieldInfo(
            is_object=_is_object(anno),
            name=k,
            from_base=k in bases_fields,
            type_name=get_type_name(anno),
            is_exclude=bool(v.exclude)
        ))
    return fields


def get_vscode_link(kls):
    """Build a VSCode deep link to the class definition.

    Priority:
      1. If running inside WSL and WSL_DISTRO_NAME is present, return a remote link:
         vscode://vscode-remote/wsl+<distro>/<absolute/path>:<line>
         (This opens directly in the VSCode WSL remote window.)
      2. Else, if path is /mnt/<drive>/..., translate to Windows drive and return vscode://file/C:\\...:line
      3. Else, fallback to vscode://file/<unix-absolute-path>:line
    """
    try:
        source_file = inspect.getfile(kls)
        _lines, start_line = inspect.getsourcelines(kls)

        distro = os.environ.get("WSL_DISTRO_NAME")
        if distro:
            # Ensure absolute path (it should already be under /) and build remote link
            return f"vscode://vscode-remote/wsl+{distro}{source_file}:{start_line}"

        # Non-remote scenario: maybe user wants to open via translated Windows path
        if source_file.startswith('/mnt/') and len(source_file) > 6:
            parts = source_file.split('/')
            if len(parts) >= 4 and len(parts[2]) == 1:  # drive letter
                drive = parts[2].upper()
                rest = parts[3:]
                win_path = drive + ':\\' + '\\'.join(rest)
                return f"vscode://file/{win_path}:{start_line}"

        # Fallback plain unix path
        return f"vscode://file/{source_file}:{start_line}"
    except Exception:
        return ""


def get_source(kls):
    try:
        source = inspect.getsource(kls)
        return source
    except Exception:
        return "failed to get source"