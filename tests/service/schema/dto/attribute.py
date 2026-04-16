"""
Attribute and AttributeValue DTOs.
"""
from pydantic import BaseModel, ConfigDict, Field


class Attribute(BaseModel):
    """属性定义"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="属性 ID")
    name: str = Field(description="属性名称")


class AttributeValue(BaseModel):
    """属性值"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="属性值 ID")
    attribute_id: int = Field(description="属性 ID")
    value: str = Field(description="属性值")
