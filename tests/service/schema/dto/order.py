"""
Order, OrderItem, Payment, Refund DTOs.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Order(BaseModel):
    """订单"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="订单 ID")
    user_id: int = Field(description="用户 ID")
    status: str = Field(default="pending", description="订单状态")
    total_amount: float = Field(default=0, description="订单总额")


class OrderItem(BaseModel):
    """订单明细"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="明细 ID")
    order_id: int = Field(description="订单 ID")
    variant_id: int = Field(description="商品规格 ID")
    quantity: int = Field(description="数量")
    unit_price: float = Field(description="单价")


class Payment(BaseModel):
    """支付记录"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="支付 ID")
    order_id: int = Field(description="订单 ID")
    method: str = Field(description="支付方式")
    amount: float = Field(description="支付金额")
    status: str = Field(default="pending", description="支付状态")


class Refund(BaseModel):
    """退款"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="退款 ID")
    order_id: int = Field(description="订单 ID")
    amount: float = Field(description="退款金额")
    reason: Optional[str] = Field(default=None, description="退款原因")
    status: str = Field(default="pending", description="退款状态")
