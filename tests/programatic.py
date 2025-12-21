from fastapi_voyager import create_voyager
# from tests.demo_anno import app
from tests.demo import app, diagram

app.mount(
    '/voyager', 
    create_voyager(
        app, 
        er_diagram=diagram,
        module_color={"tests.service": "purple"}, 
        module_prefix="tests.service", 
        swagger_url="/docs",
        initial_page_policy='first',
        ga_id='G-R64S7Q49VL',
        online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main", 
        enable_pydantic_resolve_meta=True))
