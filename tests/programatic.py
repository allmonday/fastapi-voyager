from fastapi_voyager import create_voyager
from tests.demo import app

app.mount(
    '/voyager', 
    create_voyager(
        app, 
        module_color={"tests.service": "purple", "tests.demo": "#ccaa00", "tests": "green"}, 
        module_prefix="tests.service", 
        swagger_url="/docs",
        initial_page_policy='full',
        online_repo_url="https://github.com/allmonday/fastapi-voyager/blob/main"))
