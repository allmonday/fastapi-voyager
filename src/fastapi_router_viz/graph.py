from fastapi import FastAPI
from fastapi.openapi.utils import get_fields_from_routes
from fastapi_router_viz.type_helper import shelling_type
from pydantic import BaseModel
# read route and schemas, generate graph


def analysis(app: FastAPI):
    """
    1. get routes which return pydantic schema
    2. iterate routes, construct the nodes and links
    """
    _fields = get_fields_from_routes(app.routes)

    fields = []

    for field in _fields:
        if field.mode == 'serialization':
            schema = shelling_type(field.field_info.annotation)
            if issubclass(schema, BaseModel):
                fields.append(field)

    return len(fields)
