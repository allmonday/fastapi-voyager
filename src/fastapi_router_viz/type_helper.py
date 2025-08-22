from typing import Union
from typing import get_origin, get_args


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