"""
Product, ProductVariant, ProductImage, Brand, Category, Review DTOs.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Category(BaseModel):
    """商品分类"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="分类 ID")
    name: str = Field(description="分类名称")
    parent_id: Optional[int] = Field(default=None, description="父分类 ID")


class Brand(BaseModel):
    """品牌"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="品牌 ID")
    name: str = Field(description="品牌名称")
    logo: Optional[str] = Field(default=None, description="品牌 Logo URL")


class Product(BaseModel):
    """商品"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="商品 ID")
    name: str = Field(description="商品名称")
    description: Optional[str] = Field(default=None, description="商品描述")
    price: float = Field(description="价格")
    brand_id: Optional[int] = Field(default=None, description="品牌 ID")
    category_id: Optional[int] = Field(default=None, description="分类 ID")
    store_id: Optional[int] = Field(default=None, description="店铺 ID")


class ProductVariant(BaseModel):
    """商品规格 (SKU)"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="规格 ID")
    product_id: int = Field(description="商品 ID")
    sku: str = Field(description="SKU 编码")
    price: float = Field(description="规格价格")
    stock: int = Field(default=0, description="库存数量")


class ProductImage(BaseModel):
    """商品图片"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="图片 ID")
    product_id: int = Field(description="商品 ID")
    url: str = Field(description="图片 URL")
    sort_order: int = Field(default=0, description="排序")


class Review(BaseModel):
    """商品评价"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="评价 ID")
    product_id: int = Field(description="商品 ID")
    user_id: int = Field(description="用户 ID")
    rating: int = Field(description="评分 (1-5)")
    content: Optional[str] = Field(default=None, description="评价内容")
