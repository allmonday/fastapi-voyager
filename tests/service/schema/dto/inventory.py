"""
Warehouse and Inventory DTOs.
"""
from pydantic import BaseModel, ConfigDict, Field


class Warehouse(BaseModel):
    """仓库"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="仓库 ID")
    name: str = Field(description="仓库名称")
    location: str = Field(description="仓库位置")


class Inventory(BaseModel):
    """库存"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="库存 ID")
    warehouse_id: int = Field(description="仓库 ID")
    variant_id: int = Field(description="商品规格 ID")
    quantity: int = Field(default=0, description="库存数量")
