import sys
import pytest
from fastapi_voyager.type_helper import get_core_types
from typing import Annotated


def test_optional_and_list_core_types():
    class T: ...

    # Optional[T] -> (T,)
    opt = T | None
    core = get_core_types(opt)
    assert core == (T,)

    # list[T] -> (T,)
    lst = list[T]
    core2 = get_core_types(lst)
    assert core2 == (T,)


def test_typing_union_core_types():
    class A: ...
    class B: ...

    u = A | B
    core = get_core_types(u)
    # order preserved
    assert core == (A, B)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="PEP 604 union (|) requires Python 3.10+")
def test_uniontype_pep604_core_types():
    class A: ...
    class B: ...

    u = A | B
    core = get_core_types(u)
    assert core == (A, B)


def test_mixed_optional_list():
    class T: ...

    # Optional[list[T]] -> (T,) (list unwrapped after removing None)
    anno = list[T] | None
    core = get_core_types(anno)
    assert core == (T,)


def test_nested_union_flattening():
    class A: ...
    class B: ...
    class C: ...

    anno = A | (B | C)
    core = get_core_types(anno)
    # typing normalizes nested unions -> (A, B, C)
    assert core == (A, B, C)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="PEP 604 union (|) requires Python 3.10+")
def test_uniontype_with_list_member():
    class A: ...
    class B: ...

    anno = A | list[B]
    anno2 = A | list[list[B]]
    core = get_core_types(anno)
    core2 = get_core_types(anno2)
    assert core == (A, B)
    assert core2 == (A, B)


# Only Python 3.12+ supports the PEP 695 `type` statement producing TypeAliasType
@pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695 type aliases require Python 3.12+")
def test_union_type_alias_and_list():
    # Dynamically exec a type alias using the new syntax 
    # so test file stays valid on <3.12 (even though skipped)
    ns: dict = {}
    code = """
class A: ...
class B: ...

type MyAlias = A | B
"""
    exec(code, ns, ns)
    MyAlias = ns['MyAlias']
    A = ns['A']
    B = ns['B']

    # list[MyAlias] should yield (A, B)
    core = get_core_types(list[MyAlias])
    assert set(core) == {A, B}

    # Direct alias should also work
    core2 = get_core_types(MyAlias)
    assert set(core2) == {A, B}


def test_annotated():
    class A: ...

    core = get_core_types(Annotated[A, 'hello'])
    assert set(core) == {A}

