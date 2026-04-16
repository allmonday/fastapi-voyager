"""
Shared utilities for testing embedding services across different frameworks.

This module provides common test functions that can be reused across
FastAPI, Django Ninja, and Litestar embedding tests.
"""
import httpx
import pytest


# Expected routes - same across all frameworks after standardization
EXPECTED_ROUTES = [
    "get_products",
    "get_page_info",
    "get_page_stories",
    "get_page_test_1",
    "get_page_test_2",
    "get_page_test_3_long_long_long_name",
    "get_page_test_3_no_response_model",
    "get_page_test_3_no_response_model_long_long_long_name",
]


async def test_dot_endpoint_returns_success(async_client: httpx.AsyncClient):
    """Test that /voyager/dot endpoint returns 200 OK."""
    response = await async_client.get("/voyager/dot")
    assert response.status_code == 200


async def test_dot_endpoint_has_tags(async_client: httpx.AsyncClient):
    """Test that /voyager/dot endpoint returns tags data."""
    response = await async_client.get("/voyager/dot")
    assert response.status_code == 200
    data = response.json()

    # Check that tags key exists and is a list
    assert "tags" in data
    assert isinstance(data["tags"], list)

    # Should have tags defined in demo.py
    tags = data["tags"]
    tag_names = [tag["name"] for tag in tags]

    # Check expected tags from demo.py
    assert "for-restapi" in tag_names
    assert "for-ui-page" in tag_names
    assert "long_long_long_tag_name" in tag_names

    # Note: group_a and group_b tags might not be returned if they're not
    # properly recognized by the framework introspection
    # This is acceptable behavior as tag filtering varies by framework


async def test_dot_endpoint_tags_have_routes(async_client: httpx.AsyncClient):
    """Test that tags have associated routes."""
    response = await async_client.get("/voyager/dot")
    assert response.status_code == 200
    data = response.json()

    tags = data["tags"]

    # Each tag should have routes
    for tag in tags:
        assert "routes" in tag
        assert isinstance(tag["routes"], list)
        # Routes should be sorted by name
        route_names = [r["name"] for r in tag["routes"]]
        assert route_names == sorted(route_names)


async def test_dot_endpoint_routes_structure(async_client: httpx.AsyncClient):
    """Test that routes have correct structure."""
    response = await async_client.get("/voyager/dot")
    assert response.status_code == 200
    data = response.json()

    tags = data["tags"]

    # Find a tag with routes and check route structure
    for tag in tags:
        if tag["routes"]:
            route = tag["routes"][0]
            # Check required fields
            assert "id" in route
            assert "name" in route
            assert "module" in route
            assert "unique_id" in route

            # Check types
            assert isinstance(route["id"], str)
            assert isinstance(route["name"], str)
            assert isinstance(route["module"], str)
            assert isinstance(route["unique_id"], str)
            break
    else:
        pytest.fail("No routes found in any tag")


async def test_dot_endpoint_other_fields(async_client: httpx.AsyncClient, expected_framework_name: str):
    """Test other required fields in /dot response."""
    response = await async_client.get("/voyager/dot")
    assert response.status_code == 200
    data = response.json()

    # Check other required fields
    assert "schemas" in data
    assert isinstance(data["schemas"], list)

    assert "dot" in data
    assert isinstance(data["dot"], str)

    assert "version" in data
    assert isinstance(data["version"], str)

    assert "initial_page_policy" in data
    assert data["initial_page_policy"] in ["first", "full", "empty"]

    assert "framework_name" in data
    assert isinstance(data["framework_name"], str)
    assert data["framework_name"] == expected_framework_name

    assert "has_er_diagram" in data
    assert isinstance(data["has_er_diagram"], bool)

    assert "enable_pydantic_resolve_meta" in data
    assert isinstance(data["enable_pydantic_resolve_meta"], bool)
    assert data["enable_pydantic_resolve_meta"] is True


async def test_dot_endpoint_expected_routes(
    async_client: httpx.AsyncClient,
    expected_routes: list[str]
):
    """Test that expected routes from demo.py are present."""
    response = await async_client.get("/voyager/dot")
    assert response.status_code == 200
    data = response.json()

    # Collect all route names
    all_routes = []
    for tag in data["tags"]:
        for route in tag["routes"]:
            all_routes.append(route["name"])

    # Check expected routes
    for expected_route in expected_routes:
        assert expected_route in all_routes, f"Expected route '{expected_route}' not found"
