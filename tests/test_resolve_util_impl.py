from pydantic import BaseModel
from typing import Annotated
from pydantic_resolve import Collector
from pydantic_resolve.utils.er_diagram import LoaderInfo
from fastapi_voyager.pydantic_resolve_util import analysis_pydantic_resolve_fields


class SchemaA(BaseModel):
    __pydantic_resolve_expose__ = {"exposed_field": "alias_name"}
    __pydantic_resolve_collect__ = {
        "collected_field": "collector_name",
        ("collected_field_a", "collected_field_b"): "collector_x",
        ("collected_field_c", "collected_field_d"): ("collector_y", "collector_z"),

        ("collected_field", "collected_field_c"): ("collector_u", "collector_v"),
    }

    id: int
    resolved_field: Annotated[str, LoaderInfo(field="id")] = ""
    exposed_field: str = ""
    collected_field: str = ""

    collected_field_a: str = ""
    collected_field_b: str = ""

    collected_field_c: str = ""
    collected_field_d: str = ""

    post_field: str = ""

    def resolve_resolved_field(self):
        return "resolved"

    def post_post_field(self):
        return "posted"

    collector: list[str] = []
    def post_collector(self, collector=Collector(alias="top_collector")):    
        return collector.values()

def test_resolve_util():
    # Test resolved field
    res = analysis_pydantic_resolve_fields(SchemaA, "resolved_field")
    assert res["is_resolve"] is True

    # Test exposed field
    res = analysis_pydantic_resolve_fields(SchemaA, "exposed_field")
    assert res["expose_as_info"] == "alias_name"

    # Test collected field
    res = analysis_pydantic_resolve_fields(SchemaA, "collected_field")
    assert set(res["send_to_info"]) == {"collector_name", "collector_u", "collector_v"}

    # Test collected field a (tuple key)
    res = analysis_pydantic_resolve_fields(SchemaA, "collected_field_a")
    assert set(res["send_to_info"]) == {"collector_x"}

    # Test collected field c (tuple key and tuple value)
    res = analysis_pydantic_resolve_fields(SchemaA, "collected_field_c")
    assert set(res["send_to_info"]) == {"collector_y", "collector_z", "collector_u", "collector_v"}

    # Test post field
    res = analysis_pydantic_resolve_fields(SchemaA, "post_field")
    assert res["is_post"] is True


    res = analysis_pydantic_resolve_fields(SchemaA, "collector")
    assert set(res["collect_info"]) == {"top_collector"}