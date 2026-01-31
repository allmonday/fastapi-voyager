from litestar import Litestar
from fastapi_voyager import create_voyager
from tests.litestar.demo import DemoController, diagram

# Create a basic Litestar app
app = Litestar(route_handlers=[DemoController])

# Create voyager app for visualization
voyager_app = create_voyager(
    app,
    er_diagram=diagram,
    module_color={"tests.service": "purple"},
    module_prefix="tests.service",
    swagger_url="/schema/swagger",
    initial_page_policy='first',
    ga_id='G-R64S7Q49VL',
    online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main",
    enable_pydantic_resolve_meta=True
)

# Mount voyager under a specific path
# In Litestar, you would typically create a separate controller or mount point
# For example:
#
# from litestar import Litestar, Router
#
# main_router = Router(path="/demo", route_handlers=[DemoController])
# voyager_router = Router(path="/voyager")
#
# # Mount the voyager Starlette app
# @voyager_router.get("/{path:path}")
# async def voyager_handler(request) -> Response:
#     return await voyager_app(request.scope, request.receive)
#
# app = Litestar(route_handlers=[main_router, voyager_router])
#
# Or using ASGI mount:
# from litestar import Litestar
# app = Litestar(route_handlers=[DemoController])
# app.mount("/voyager", voyager_app)
