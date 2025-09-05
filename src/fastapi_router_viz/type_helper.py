from typing import get_origin, get_args, Union
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