import inspect
import logging
import os
from types import UnionType
from typing import Annotated, Any, Generic, Union, get_args, get_origin, ForwardRef

import pydantic_resolve.constant as const
from pydantic import BaseModel

from fastapi_voyager.type import FieldInfo
from fastapi_voyager.pydantic_resolve_util import analysis_pydantic_resolve_fields

logger = logging.getLogger(__name__)

# Python <3.12 compatibility: TypeAliasType exists only from 3.12 (PEP 695)
try:  # pragma: no cover - import guard
    from typing import TypeAliasType  # type: ignore
except Exception:  # pragma: no cover
    class _DummyTypeAliasType:  # minimal sentinel so isinstance checks are safe
        pass
    TypeAliasType = _DummyTypeAliasType  # type: ignore


def is_list(annotation):
    return getattr(annotation, "__origin__", None) == list


def full_class_name(cls):
    return f"{cls.__module__}.{cls.__qualname__}"


def get_core_types(tp):
    """
    - get the core type
    - always return a tuple of core types
    """
    # Helpers
    def _unwrap_alias(t):
        """Unwrap PEP 695 type aliases by following __value__ repeatedly."""
        while isinstance(t, TypeAliasType) or (
            t.__class__.__name__ == 'TypeAliasType' and hasattr(t, '__value__')
        ):
            try:
                t = t.__value__
            except Exception:  # pragma: no cover - defensive
                break
        return t

    def _enqueue(items, q):
        for it in items:
            if it is not type(None):  # skip None in unions
                q.append(it)

    # Queue-based shelling to reach concrete core types
    queue: list[object] = [tp]
    result: list[object] = []

    while queue:
        cur = queue.pop(0)
        if cur is type(None):
            continue

        cur = _unwrap_alias(cur)

        # Handle Annotated[T, ...] as a shell
        if get_origin(cur) is Annotated:
            args = get_args(cur)
            if args:
                queue.append(args[0])
            continue

        # Handle Union / Optional / PEP 604 UnionType
        orig = get_origin(cur)
        if orig in (Union, UnionType):
            args = get_args(cur)
            # push all non-None members back for further shelling
            _enqueue(args, queue)
            continue

        # Handle list shells
        if is_list(cur):
            args = getattr(cur, "__args__", ())
            if args:
                queue.append(args[0])
            continue

        # If still an alias-like wrapper, unwrap again and re-process
        _cur2 = _unwrap_alias(cur)
        if _cur2 is not cur:
            queue.append(_cur2)
            continue

        # Otherwise treat as a concrete core type (could be a class, typing.Final, etc.)
        result.append(cur)

    return tuple(result)


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
    return safe_issubclass(cls, BaseModel) and cls is not BaseModel and not is_generic_container(cls)


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
        pydantic_resolve_specific_params = analysis_pydantic_resolve_fields(schema, k)
        fields.append(FieldInfo(
            is_object=_is_object(anno),
            name=k,
            from_base=k in bases_fields,
            type_name=get_type_name(anno),
            is_exclude=bool(v.exclude),
            desc=v.description or '',
            **pydantic_resolve_specific_params
        ))
    return fields


def get_vscode_link(kls, online_repo_url: str | None = None) -> str:
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
        if online_repo_url:
            cwd = os.getcwd()
            relative_path = os.path.relpath(source_file, cwd)
            return f"{online_repo_url}/{relative_path}#L{start_line}"
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


def safe_issubclass(kls, target_kls):
    try:
        return issubclass(kls, target_kls)
    except TypeError:
        # if kls is ForwardRef, log it
        if isinstance(kls, ForwardRef):
            logger.error(f'{str(kls)} is a ForwardRef, not a subclass of {target_kls.__module__}:{target_kls.__qualname__}')
        else:
            logger.debug(f'{kls.__module__}:{kls.__qualname__} is not subclass of {target_kls.__module__}:{target_kls.__qualname__}')  
        return False


def update_forward_refs(kls):
    # TODO: refactor
    def update_pydantic_forward_refs(pydantic_kls: type[BaseModel]):
        """
        recursively update refs.
        """

        pydantic_kls.model_rebuild()
        setattr(pydantic_kls, const.PYDANTIC_FORWARD_REF_UPDATED, True)

        values = pydantic_kls.model_fields.values()
        for field in values:
            update_forward_refs(field.annotation)
        
    for shelled_type in get_core_types(kls):
        # Only treat as updated if the flag is set on the class itself, not via inheritance

        local_attrs = getattr(shelled_type, '__dict__', {})
        if local_attrs.get(const.PYDANTIC_FORWARD_REF_UPDATED, False):
            logger.debug("%s visited", shelled_type.__qualname__)
            continue
        if safe_issubclass(shelled_type, BaseModel):
            update_pydantic_forward_refs(shelled_type)


def is_generic_container(cls):
    """
    T = TypeVar('T')
    class DataModel(BaseModel, Generic[T]):
        data: T
        id: int

    type DataModelPageStory = DataModel[PageStory]

    is_generic_container(DataModel) -> True
    is_generic_container(DataModel[PageStory]) -> False

    DataModel.__parameters__ == (T,)
    DataModelPageStory.__parameters__ == (,)
    """
    try:
        return (hasattr(cls, '__bases__') and Generic in cls.__bases__ and (hasattr(cls, '__parameters__') and bool(cls.__parameters__)))
    except (TypeError, AttributeError):
        return False
    
def is_non_pydantic_type(tp):
    for schema in get_core_types(tp):
        if schema and safe_issubclass(schema, BaseModel):
            return False
    return True

if __name__ == "__main__":
    from tests.demo_anno import PageOverall, PageSprint

    update_forward_refs(PageOverall)
    update_forward_refs(PageSprint)