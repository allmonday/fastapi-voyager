from fastapi_voyager import create_voyager
from tests.demo import app

app.mount(
    '/voyager', 
    create_voyager(
        app, 
        module_color={"tests.service": "purple"}, 
        module_prefix="tests.service", 
        swagger_url="/docs",
        initial_page_policy='first',
        online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main"))
