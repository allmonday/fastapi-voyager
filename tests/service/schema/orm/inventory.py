"""
Warehouse and Inventory ORM models.
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import OrmBase


class WarehouseOrm(OrmBase):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(200))

    # Relationships
    inventories: Mapped[list["InventoryOrm"]] = relationship(back_populates="warehouse")
    shipments: Mapped[list["ShipmentOrm"]] = relationship(back_populates="warehouse")


class InventoryOrm(OrmBase):
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    warehouse: Mapped["WarehouseOrm"] = relationship(back_populates="inventories")
    variant: Mapped["ProductVariantOrm"] = relationship(back_populates="inventories")
