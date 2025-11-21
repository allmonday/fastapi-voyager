from fastapi_voyager.filter import filter_subgraph_by_module_prefix
from fastapi_voyager.type import PK, Link, Route, SchemaNode, Tag


def _make_tag_route_link(tag: Tag, route: Route) -> Link:
    return Link(
        source=tag.id,
        source_origin=tag.id,
        target=route.id,
        target_origin=route.id,
        type="tag_route",
    )


def test_filter_subgraph_filters_nodes_and_links():
    tag = Tag(id="tag1", name="Tag 1", routes=[])
    route = Route(id="route1", name="route1", module="api.routes")
    tag.routes.append(route)

    node_a = SchemaNode(id="pkg.ModelA", name="ModelA", module="pkg.moduleA")
    node_b = SchemaNode(id="pkg.ModelB", name="ModelB", module="target.moduleB")

    links = [
        _make_tag_route_link(tag, route),
        Link(
            source=route.id,
            source_origin=route.id,
            target=f"{node_a.id}::{PK}",
            target_origin=node_a.id,
            type="route_to_schema",
        ),
        Link(
            source=f"{node_a.id}::ffield",
            source_origin=node_a.id,
            target=f"{node_b.id}::{PK}",
            target_origin=node_b.id,
            type="schema",
        ),
    ]

    tags = [tag]
    routes = [route]
    nodes = [node_a, node_b]

    _, _, filtered_nodes, filtered_links = filter_subgraph_by_module_prefix(
        tags=tags,
        routes=routes,
        links=links,
        nodes=nodes,
        module_prefix="target",
    )

    assert filtered_nodes == [node_b]
    assert any(
        lk.type == "route_to_schema" and \
        lk.source_origin == route.id and \
        lk.target_origin == node_b.id
        for lk in filtered_links
    )
    assert len(filtered_links) == 2  # tag -> route and merged route -> filtered node



def test_filter_subgraph_handles_cycles_and_multiple_matches():
    tag = Tag(id="tag-main", name="Tag", routes=[])
    route = Route(id="route-main", name="route", module="api.routes")
    tag.routes.append(route)

    node_root = SchemaNode(id="pkg.Root", name="Root", module="pkg.root")
    node_mid = SchemaNode(id="pkg.Mid", name="Mid", module="pkg.mid")
    node_target1 = SchemaNode(id="pkg.Target1", name="Target1", module="target.mod.alpha")
    node_target2 = SchemaNode(id="pkg.Target2", name="Target2", module="target.mod.beta")

    links = [
        _make_tag_route_link(tag, route),
        Link(
            source=route.id,
            source_origin=route.id,
            target=f"{node_root.id}::{PK}",
            target_origin=node_root.id,
            type="route_to_schema",
        ),
        Link(
            source=f"{node_root.id}::ffield",
            source_origin=node_root.id,
            target=f"{node_mid.id}::{PK}",
            target_origin=node_mid.id,
            type="schema",
        ),
        Link(
            source=f"{node_mid.id}::{PK}",
            source_origin=node_mid.id,
            target=f"{node_target1.id}::{PK}",
            target_origin=node_target1.id,
            type="parent",
        ),
        Link(
            source=f"{node_mid.id}::ffield",
            source_origin=node_mid.id,
            target=f"{node_target2.id}::{PK}",
            target_origin=node_target2.id,
            type="subset",
        ),
        Link(
            source=f"{node_target1.id}::ffield",
            source_origin=node_target1.id,
            target=f"{node_root.id}::{PK}",
            target_origin=node_root.id,
            type="schema",
        ),
    ]

    nodes = [node_root, node_mid, node_target1, node_target2]

    _, _, filtered_nodes, filtered_links = filter_subgraph_by_module_prefix(
        tags=[tag],
        routes=[route],
        links=links,
        nodes=nodes,
        module_prefix="target.mod",
    )

    assert filtered_nodes == [node_target1, node_target2]

    route_to_schema_targets = {
        (lk.source_origin, lk.target_origin)
        for lk in filtered_links
        if lk.type == "route_to_schema"
    }
    assert route_to_schema_targets == {
        (route.id, node_target1.id),
        (route.id, node_target2.id),
    }

    assert all(lk.type in {"tag_route", "route_to_schema"} for lk in filtered_links)
    assert len(filtered_links) == 3  # 1 tag_route + 2 merged links
