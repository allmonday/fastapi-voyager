"""
Product, ProductVariant, ProductImage, Brand, Category ORM models.
"""
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import OrmBase


class CategoryOrm(OrmBase):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))

    # Relationships
    parent: Mapped["CategoryOrm | None"] = relationship(
        remote_side="CategoryOrm.id",
        back_populates="children",
    )
    children: Mapped[list["CategoryOrm"]] = relationship(back_populates="parent")
    products: Mapped[list["ProductOrm"]] = relationship(back_populates="category")


class BrandOrm(OrmBase):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    logo: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    products: Mapped[list["ProductOrm"]] = relationship(back_populates="brand")


class ProductOrm(OrmBase):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"))

    # Relationships
    brand: Mapped["BrandOrm | None"] = relationship(back_populates="products")
    category: Mapped["CategoryOrm | None"] = relationship(back_populates="products")
    store: Mapped["StoreOrm | None"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariantOrm"]] = relationship(back_populates="product")
    images: Mapped[list["ProductImageOrm"]] = relationship(back_populates="product")
    reviews: Mapped[list["ReviewOrm"]] = relationship(back_populates="product")
    tags: Mapped[list["TagOrm"]] = relationship(
        secondary="product_tag",
        back_populates="products",
    )


class ProductVariantOrm(OrmBase):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    sku: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    product: Mapped["ProductOrm"] = relationship(back_populates="variants")
    order_items: Mapped[list["OrderItemOrm"]] = relationship(back_populates="variant")
    inventories: Mapped[list["InventoryOrm"]] = relationship(back_populates="variant")
    attribute_values: Mapped[list["AttributeValueOrm"]] = relationship(
        secondary="product_attribute",
        back_populates="variants",
    )


class ProductImageOrm(OrmBase):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    url: Mapped[str] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    product: Mapped["ProductOrm"] = relationship(back_populates="images")


class TagOrm(OrmBase):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # Relationships
    products: Mapped[list["ProductOrm"]] = relationship(
        secondary="product_tag",
        back_populates="tags",
    )


class ReviewOrm(OrmBase):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int] = mapped_column(Integer)
    content: Mapped[str | None] = mapped_column(Text)

    # Relationships
    product: Mapped["ProductOrm"] = relationship(back_populates="reviews")
    user: Mapped["UserOrm"] = relationship(back_populates="reviews")
