from fastapi_voyager.module import build_module_schema_tree
from fastapi_voyager.type import SchemaNode


def _sn(id: str, module: str, name: str) -> SchemaNode:
    return SchemaNode(id=id, module=module, name=name, fields=[])


def _find_child(module_node, name: str):
    return next((m for m in module_node.modules if m.name == name), None)

def _find_top(top_modules, name: str):
    return next((m for m in top_modules if m.name == name), None)


def test_build_module_tree_basic():
    # Arrange: schema nodes in various module depths
    schema_nodes = [
        _sn("A", "pkg", "A"),
        _sn("B", "pkg.sub", "B"),
        _sn("B2", "pkg.sub", "B2"),
        _sn("C", "pkg.other", "C"),
        _sn("D", "x.y.z", "D"),
    ]

    # Act
    top_modules = build_module_schema_tree(schema_nodes)
    from pprint import pprint
    pprint(top_modules)

    # Assert: top-level modules
    names = sorted(m.name for m in top_modules)
    assert names == ["pkg", "x.y.z"]

    # pkg level
    pkg = _find_top(top_modules, "pkg")
    assert pkg is not None
    assert [sn.name for sn in pkg.schema_nodes] == ["A"]
    assert sorted(m.name for m in pkg.modules) == ["other", "sub"]

    # pkg.sub level
    sub = _find_child(pkg, "sub")
    assert sub is not None
    assert sorted(sn.name for sn in sub.schema_nodes) == ["B", "B2"]
    assert sub.modules == []

    # pkg.other level
    other = _find_child(pkg, "other")
    assert other is not None
    assert [sn.name for sn in other.schema_nodes] == ["C"]
    assert other.modules == []

    # x.y.z chain should collapse to a single module named "x.y.z"
    x = _find_top(top_modules, "x.y.z")
    assert x is not None
    assert [sn.name for sn in x.schema_nodes] == ["D"]
    assert x.modules == []


def test_build_module_tree_empty_input():
    top_modules = build_module_schema_tree([])
    assert top_modules == []


def test_build_module_tree_root_level_nodes():
    # Nodes without module path should be attached to __root__
    schema_nodes = [
        _sn("Root1", "", "Root1"),
        _sn("Root2", "", "Root2"),
        _sn("PkgA", "pkg", "PkgA"),
    ]

    top_modules = build_module_schema_tree(schema_nodes)
    names = sorted(m.name for m in top_modules)
    assert names == ["__root__", "pkg"]
    root = _find_top(top_modules, "__root__")
    assert root is not None
    assert sorted(sn.name for sn in root.schema_nodes) == ["Root1", "Root2"]
    pkg = _find_top(top_modules, "pkg")
    assert pkg is not None and [sn.name for sn in pkg.schema_nodes] == ["PkgA"]


def test_collapse_single_child_empty_modules():
    # Construct a deeper chain with empty intermediate modules that should collapse
    schema_nodes = [
        _sn("Deep", "a.b.c.d", "Deep"),
        _sn("Peer", "a.b.x", "Peer"),
    ]
    top_modules = build_module_schema_tree(schema_nodes)
    print(top_modules)
    # 'a' should have one child path 'b', but due to branching at x, only a.b collapses into a.b
    # and below it, 'c.d' should collapse to 'c.d'. Final structure:
    # a
    #  └── b
    #       ├── c.d (holds Deep)
    #       └── x (holds Peer)
    a = _find_top(top_modules, "a.b")
    assert a is not None
    assert a.schema_nodes == []
    # b remains as child of a
    b = _find_child(a, "c.d")
    assert b is not None
    assert [sn.name for sn in b.schema_nodes] == ['Deep']
    # collapsed node under b is named "c.d"
    x = _find_child(a, "x")
    assert x is not None
    assert [sn.name for sn in x.schema_nodes] == ["Peer"]