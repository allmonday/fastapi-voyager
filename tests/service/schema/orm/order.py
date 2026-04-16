"""
Order, OrderItem, Payment, Refund ORM models.
"""
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import OrmBase


class OrderOrm(OrmBase):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_amount: Mapped[float] = mapped_column(Float, default=0)

    # Relationships
    user: Mapped["UserOrm"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItemOrm"]] = relationship(back_populates="order")
    payment: Mapped["PaymentOrm | None"] = relationship(
        back_populates="order",
        uselist=False,
    )
    refunds: Mapped[list["RefundOrm"]] = relationship(back_populates="order")
    coupon_usages: Mapped[list["CouponUsageOrm"]] = relationship(back_populates="order")


class OrderItemOrm(OrmBase):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)

    # Relationships
    order: Mapped["OrderOrm"] = relationship(back_populates="items")
    variant: Mapped["ProductVariantOrm"] = relationship(back_populates="order_items")


class PaymentOrm(OrmBase):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    method: Mapped[str] = mapped_column(String(20))
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Relationships
    order: Mapped["OrderOrm"] = relationship(back_populates="payment")


class RefundOrm(OrmBase):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    amount: Mapped[float] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Relationships
    order: Mapped["OrderOrm"] = relationship(back_populates="refunds")
