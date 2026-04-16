"""
Coupon and CouponUsage DTOs.
"""
from pydantic import BaseModel, ConfigDict, Field


class Coupon(BaseModel):
    """优惠券"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="优惠券 ID")
    code: str = Field(description="优惠券代码")
    discount: float = Field(description="折扣金额")
    min_amount: float = Field(default=0, description="最低消费金额")
    status: str = Field(default="active", description="状态")


class CouponUsage(BaseModel):
    """优惠券使用记录"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="使用记录 ID")
    coupon_id: int = Field(description="优惠券 ID")
    user_id: int = Field(description="用户 ID")
    order_id: int = Field(description="订单 ID")
