import sys
import pytest
from typing import get_args, get_origin

from fastapi_router_viz.type_helper import get_core_types

# Only Python 3.12+ supports the PEP 695 `type` statement producing TypeAliasType
pytestmark = pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695 type aliases require Python 3.12+")

def test_union_type_alias_and_list():
    # Dynamically exec a type alias using the new syntax so test file stays valid on <3.12 (even though skipped)
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
