"""
Store ORM model.
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import OrmBase


class StoreOrm(OrmBase):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    products: Mapped[list["ProductOrm"]] = relationship(back_populates="store")
    staff_members: Mapped[list["UserOrm"]] = relationship(
        secondary="store_staff",
        back_populates="managed_stores",
    )
    shipments: Mapped[list["ShipmentOrm"]] = relationship(back_populates="store")
