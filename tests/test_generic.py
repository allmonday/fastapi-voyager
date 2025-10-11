from pydantic import BaseModel
from typing import Generic, TypeVar
from fastapi_voyager.type_helper import is_generic_container

class PageStory(BaseModel):
    id: int
    title: str

T = TypeVar('T')
class DataModel(BaseModel, Generic[T]):
    data: T
    id: int

type DataModelPageStory = DataModel[PageStory]

def test_is_generic_container():
    print(DataModelPageStory.__value__.__bases__)
    print(DataModelPageStory.__value__.model_fields.items())
    assert is_generic_container(DataModel) is True
    assert is_generic_container(DataModelPageStory) is False