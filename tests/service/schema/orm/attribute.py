"""
Attribute and AttributeValue ORM models.
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import OrmBase


class AttributeOrm(OrmBase):
    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # Relationships
    values: Mapped[list["AttributeValueOrm"]] = relationship(back_populates="attribute")


class AttributeValueOrm(OrmBase):
    __tablename__ = "attribute_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attribute_id: Mapped[int] = mapped_column(ForeignKey("attributes.id"))
    value: Mapped[str] = mapped_column(String(100))

    # Relationships
    attribute: Mapped["AttributeOrm"] = relationship(back_populates="values")
    variants: Mapped[list["ProductVariantOrm"]] = relationship(
        secondary="product_attribute",
        back_populates="attribute_values",
    )
