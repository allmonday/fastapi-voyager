from fastapi_router_viz.type import SchemaNode, ModuleNode

def build_module_tree(schema_nodes: list[SchemaNode]) -> list[ModuleNode]:
    """
    1. the name of module_node comes from schema_node's module field
    2. split the module_name with '.' to create a tree structure
    3. group schema_nodes under the correct module_node
    4. return the top-level module_node list
    """
    # Map from top-level module name to ModuleNode
    top_modules: dict[str, ModuleNode] = {}
    # For nodes without module path, collect separately
    root_level_nodes = []

    def get_or_create(child_name: str, parent: ModuleNode) -> ModuleNode:
        for m in parent.modules:
            if m.name == child_name:
                return m
        # derive fullname from parent
        parent_full = parent.fullname
        fullname = child_name if not parent_full or parent_full == "__root__" else f"{parent_full}.{child_name}"
        new_node = ModuleNode(name=child_name, fullname=fullname, schema_nodes=[], modules=[])
        parent.modules.append(new_node)
        return new_node

    for sn in schema_nodes:
        module_path = sn.module or ""
        if not module_path:
            root_level_nodes.append(sn)
            continue
        parts = module_path.split('.')
        top_name = parts[0]
        if top_name not in top_modules:
            top_modules[top_name] = ModuleNode(name=top_name, fullname=top_name, schema_nodes=[], modules=[])
        current = top_modules[top_name]
        for part in parts[1:]:
            current = get_or_create(part, current)
        current.schema_nodes.append(sn)

    # If there are root-level nodes, add a pseudo-module named "__root__"
    result = list(top_modules.values())
    if root_level_nodes:
        result.append(ModuleNode(name="__root__", fullname="__root__", schema_nodes=root_level_nodes, modules=[]))
    return result