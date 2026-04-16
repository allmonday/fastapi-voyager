"""
M:N association tables for e-commerce schema.
"""
from sqlalchemy import Column, ForeignKey, Integer, Table

from ..db import OrmBase

# Product <-> Tag
product_tag = Table(
    "product_tag",
    OrmBase.metadata,
    Column("id", Integer, primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False),
    Column("tag_id", Integer, ForeignKey("tags.id"), nullable=False),
)

# Store <-> User (staff)
store_staff = Table(
    "store_staff",
    OrmBase.metadata,
    Column("id", Integer, primary_key=True),
    Column("store_id", Integer, ForeignKey("stores.id"), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
)

# ProductVariant <-> AttributeValue
product_attribute = Table(
    "product_attribute",
    OrmBase.metadata,
    Column("id", Integer, primary_key=True),
    Column("variant_id", Integer, ForeignKey("product_variants.id"), nullable=False),
    Column("value_id", Integer, ForeignKey("attribute_values.id"), nullable=False),
)
