from collections.abc import Callable
from typing import Any, TypeVar

from fastapi_voyager.type import ModuleNode, ModuleRoute, Route, SchemaNode

N = TypeVar('N')  # Node type: ModuleNode or ModuleRoute
I = TypeVar('I')  # Item type: SchemaNode or Route


def _build_module_tree(
    items: list[I],
    *,
    get_module_path: Callable[[I], str | None],
    NodeClass: type[N],
    item_list_attr: str,
) -> list[N]:
    """
    Generic builder that groups items by dotted module path into a tree of NodeClass.

    NodeClass must accept kwargs: name, fullname, modules(list), and an item list via
    item_list_attr (e.g., 'schema_nodes' or 'routes').
    """
    # Map from top-level module name to node
    top_modules: dict[str, N] = {}
    # Items without module path
    root_level_items: list[I] = []

    def make_node(name: str, fullname: str) -> N:
        kwargs: dict[str, Any] = {
            'name': name,
            'fullname': fullname,
            'modules': [],
            item_list_attr: [],
        }
        return NodeClass(**kwargs)  # type: ignore[arg-type]

    def get_or_create(child_name: str, parent: N) -> N:
        for m in parent.modules:
            if m.name == child_name:
                return m
        parent_full = parent.fullname
        fullname = child_name if not parent_full or parent_full == "__root__" else f"{parent_full}.{child_name}"
        new_node = make_node(child_name, fullname)
        parent.modules.append(new_node)
        return new_node

    # Build the tree
    for it in items:
        module_path = get_module_path(it) or ""
        if not module_path:
            root_level_items.append(it)
            continue
        parts = module_path.split('.')
        top_name = parts[0]
        if top_name not in top_modules:
            top_modules[top_name] = make_node(top_name, top_name)
        current = top_modules[top_name]
        for part in parts[1:]:
            current = get_or_create(part, current)
        getattr(current, item_list_attr).append(it)

    result: list[N] = list(top_modules.values())
    if root_level_items:
        result.append(make_node("__root__", "__root__"))
        setattr(result[-1], item_list_attr, root_level_items)

    # Collapse linear chains: no items on node and exactly one child module
    def collapse(node: N) -> None:
        while len(node.modules) == 1 and len(getattr(node, item_list_attr)) == 0:
            child = node.modules[0]
            node.name = f"{node.name}.{child.name}"
            node.fullname = child.fullname
            setattr(node, item_list_attr, getattr(child, item_list_attr))
            node.modules = child.modules
        for m in node.modules:
            collapse(m)

    for top in result:
        collapse(top)

    return result

def build_module_schema_tree(schema_nodes: list[SchemaNode]) -> list[ModuleNode]:
    """Build a module tree for schema nodes, grouped by their module path."""
    return _build_module_tree(
        schema_nodes,
        get_module_path=lambda sn: sn.module,
        NodeClass=ModuleNode,
        item_list_attr='schema_nodes',
    )


def build_module_route_tree(routes: list[Route]) -> list[ModuleRoute]:
    """Build a module tree for routes, grouped by their module path."""
    return _build_module_tree(
        routes,
        get_module_path=lambda r: r.module,
        NodeClass=ModuleRoute,
        item_list_attr='routes',
    )