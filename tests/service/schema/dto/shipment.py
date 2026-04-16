"""
Shipment and ShipmentItem DTOs.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Shipment(BaseModel):
    """发货单"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="发货单 ID")
    warehouse_id: int = Field(description="仓库 ID")
    store_id: Optional[int] = Field(default=None, description="店铺 ID")
    status: str = Field(default="pending", description="发货状态")
    tracking_no: Optional[str] = Field(default=None, description="物流单号")


class ShipmentItem(BaseModel):
    """发货明细"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="发货明细 ID")
    shipment_id: int = Field(description="发货单 ID")
    order_item_id: int = Field(description="订单明细 ID")
    quantity: int = Field(description="发货数量")
