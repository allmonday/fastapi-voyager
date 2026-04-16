"""
Store DTO.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Store(BaseModel):
    """店铺"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="店铺 ID")
    name: str = Field(description="店铺名称")
    description: Optional[str] = Field(default=None, description="店铺描述")
