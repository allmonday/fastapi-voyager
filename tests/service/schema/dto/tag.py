"""
Tag DTO.
"""
from pydantic import BaseModel, ConfigDict, Field


class Tag(BaseModel):
    """标签"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="标签 ID")
    name: str = Field(description="标签名称")
