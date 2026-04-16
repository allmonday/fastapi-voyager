"""
Shipment and ShipmentItem ORM models.
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import OrmBase


class ShipmentOrm(OrmBase):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    tracking_no: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    warehouse: Mapped["WarehouseOrm"] = relationship(back_populates="shipments")
    store: Mapped["StoreOrm | None"] = relationship(back_populates="shipments")
    items: Mapped[list["ShipmentItemOrm"]] = relationship(back_populates="shipment")


class ShipmentItemOrm(OrmBase):
    __tablename__ = "shipment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"))
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    quantity: Mapped[int] = mapped_column(Integer)

    # Relationships
    shipment: Mapped["ShipmentOrm"] = relationship(back_populates="items")
    order_item: Mapped["OrderItemOrm"] = relationship()
