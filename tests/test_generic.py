import sys
from typing import Generic, TypeVar

from pydantic import BaseModel

from fastapi_voyager.type_helper import is_generic_container


class PageStory(BaseModel):
    id: int
    title: str

T = TypeVar('T')
class DataModel(BaseModel, Generic[T]):
    data: T
    id: int

DataModelPageStory: object  # Stub declaration for static analysis
if sys.version_info >= (3, 12):
    exec("type DataModelPageStory = DataModel[PageStory]")
else:
    DataModelPageStory = DataModel[PageStory]

def test_is_generic_container():
    print(DataModelPageStory.__value__.__bases__)
    print(DataModelPageStory.__value__.model_fields.items())
    assert is_generic_container(DataModel) is True
    assert is_generic_container(DataModelPageStory) is False