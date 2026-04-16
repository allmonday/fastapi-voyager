"""
User and UserAddress ORM models.
"""
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import OrmBase


class UserOrm(OrmBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))

    # Relationships
    addresses: Mapped[list["UserAddressOrm"]] = relationship(back_populates="user")
    orders: Mapped[list["OrderOrm"]] = relationship(back_populates="user")
    reviews: Mapped[list["ReviewOrm"]] = relationship(back_populates="user")
    coupon_usages: Mapped[list["CouponUsageOrm"]] = relationship(back_populates="user")
    managed_stores: Mapped[list["StoreOrm"]] = relationship(
        secondary="store_staff",
        back_populates="staff_members",
    )


class UserAddressOrm(OrmBase):
    __tablename__ = "user_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    province: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50))
    district: Mapped[str] = mapped_column(String(50))
    detail: Mapped[str] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user: Mapped["UserOrm"] = relationship(back_populates="addresses")
