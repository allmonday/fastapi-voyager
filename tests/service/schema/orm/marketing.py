"""
Coupon and CouponUsage ORM models.
"""
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import OrmBase


class CouponOrm(OrmBase):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50))
    discount: Mapped[float] = mapped_column(Float)
    min_amount: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Relationships
    usages: Mapped[list["CouponUsageOrm"]] = relationship(back_populates="coupon")


class CouponUsageOrm(OrmBase):
    __tablename__ = "coupon_usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupons.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))

    # Relationships
    coupon: Mapped["CouponOrm"] = relationship(back_populates="usages")
    user: Mapped["UserOrm"] = relationship(back_populates="coupon_usages")
    order: Mapped["OrderOrm"] = relationship(back_populates="coupon_usages")
