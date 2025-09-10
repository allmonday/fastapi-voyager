from typing import get_origin, get_args, Union, Annotated, Any
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
