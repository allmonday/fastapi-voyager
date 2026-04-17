"""
电商系统实体定义 - 用于 GraphQL 和 REST API 演示
使用 SQLAlchemy ORM + build_relationship 自动构建 relationships 和 loaders
"""

from typing import List, Optional

from pydantic import BaseModel
from pydantic_resolve import ErDiagram, MutationConfig, QueryConfig
from pydantic_resolve.integration.mapping import Mapping
from pydantic_resolve.integration.sqlalchemy import build_relationship
from sqlalchemy import select

from .db import async_session, create_tables
from .dto.attribute import Attribute, AttributeValue
from .dto.inventory import Inventory, Warehouse
from .dto.marketing import Coupon, CouponUsage
from .dto.order import Order, OrderItem, Payment, Refund
from .dto.product import Brand, Category, Product, ProductImage, ProductVariant, Review
from .dto.shipment import Shipment, ShipmentItem
from .dto.store import Store
from .dto.tag import Tag
from .dto.user import User, UserAddress
from .orm import (
    AttributeOrm,
    AttributeValueOrm,
    BrandOrm,
    CategoryOrm,
    CouponOrm,
    CouponUsageOrm,
    InventoryOrm,
    OrderItemOrm,
    OrderOrm,
    PaymentOrm,
    ProductImageOrm,
    ProductOrm,
    ProductVariantOrm,
    RefundOrm,
    ReviewOrm,
    ShipmentItemOrm,
    ShipmentOrm,
    StoreOrm,
    TagOrm,
    UserAddressOrm,
    UserOrm,
    WarehouseOrm,
)

# =====================================
# Input Types for Mutations
# =====================================


class CreateProductInput(BaseModel):
    """创建商品的输入类型"""

    name: str
    description: str = ""
    price: float
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    store_id: Optional[int] = None


class CreateOrderInput(BaseModel):
    """创建订单的输入类型"""

    user_id: int
    total_amount: float = 0


# =====================================
# Build Relationships from SQLAlchemy ORM
# =====================================

_mappings = [
    Mapping(entity=User, orm=UserOrm),
    Mapping(entity=UserAddress, orm=UserAddressOrm),
    Mapping(entity=Category, orm=CategoryOrm),
    Mapping(entity=Brand, orm=BrandOrm),
    Mapping(entity=Product, orm=ProductOrm),
    Mapping(entity=ProductVariant, orm=ProductVariantOrm),
    Mapping(entity=ProductImage, orm=ProductImageOrm),
    Mapping(entity=Review, orm=ReviewOrm),
    Mapping(entity=Tag, orm=TagOrm),
    Mapping(entity=Order, orm=OrderOrm),
    Mapping(entity=OrderItem, orm=OrderItemOrm),
    Mapping(entity=Payment, orm=PaymentOrm),
    Mapping(entity=Refund, orm=RefundOrm),
    Mapping(entity=Warehouse, orm=WarehouseOrm),
    Mapping(entity=Inventory, orm=InventoryOrm),
    Mapping(entity=Shipment, orm=ShipmentOrm),
    Mapping(entity=ShipmentItem, orm=ShipmentItemOrm),
    Mapping(entity=Coupon, orm=CouponOrm),
    Mapping(entity=CouponUsage, orm=CouponUsageOrm),
    Mapping(entity=Store, orm=StoreOrm),
    Mapping(entity=Attribute, orm=AttributeOrm),
    Mapping(entity=AttributeValue, orm=AttributeValueOrm),
]

_entities = build_relationship(
    mappings=_mappings,
    session_factory=lambda: async_session(),
)


# =====================================
# Query & Mutation Functions
# =====================================


# --- User ---
async def user_get_all(limit: int = 10, offset: int = 0) -> List[User]:
    """获取所有用户（分页）"""
    async with async_session() as session:
        stmt = select(UserOrm).offset(offset).limit(limit)
        rows = (await session.scalars(stmt)).all()
        return [User.model_validate(r) for r in rows]


async def user_get_by_id(id: int) -> Optional[User]:
    """根据 ID 获取用户"""
    async with async_session() as session:
        row = await session.get(UserOrm, id)
        return User.model_validate(row) if row else None


async def user_create(username: str, email: str, phone: str = "") -> User:
    """创建新用户"""
    async with async_session() as session:
        async with session.begin():
            orm = UserOrm(username=username, email=email, phone=phone or None)
            session.add(orm)
            await session.flush()
            return User.model_validate(orm)


# --- Product ---
async def product_get_all(
    limit: int = 10, offset: int = 0, category_id: Optional[int] = None
) -> List[Product]:
    """获取所有商品（分页，可按分类筛选）"""
    async with async_session() as session:
        stmt = select(ProductOrm)
        if category_id:
            stmt = stmt.where(ProductOrm.category_id == category_id)
        stmt = stmt.offset(offset).limit(limit)
        rows = (await session.scalars(stmt)).all()
        return [Product.model_validate(r) for r in rows]


async def product_get_by_id(id: int) -> Optional[Product]:
    """根据 ID 获取商品"""
    async with async_session() as session:
        row = await session.get(ProductOrm, id)
        return Product.model_validate(row) if row else None


async def product_create(
    name: str,
    price: float,
    description: str = "",
    brand_id: Optional[int] = None,
    category_id: Optional[int] = None,
    store_id: Optional[int] = None,
) -> Product:
    """创建新商品"""
    async with async_session() as session:
        async with session.begin():
            orm = ProductOrm(
                name=name,
                price=price,
                description=description or None,
                brand_id=brand_id,
                category_id=category_id,
                store_id=store_id,
            )
            session.add(orm)
            await session.flush()
            return Product.model_validate(orm)


# --- Order ---
async def order_get_all(
    limit: int = 10, offset: int = 0, user_id: Optional[int] = None
) -> List[Order]:
    """获取所有订单（分页，可按用户筛选）"""
    async with async_session() as session:
        stmt = select(OrderOrm)
        if user_id:
            stmt = stmt.where(OrderOrm.user_id == user_id)
        stmt = stmt.offset(offset).limit(limit)
        rows = (await session.scalars(stmt)).all()
        return [Order.model_validate(r) for r in rows]


async def order_get_by_id(id: int) -> Optional[Order]:
    """根据 ID 获取订单"""
    async with async_session() as session:
        row = await session.get(OrderOrm, id)
        return Order.model_validate(row) if row else None


async def order_create(user_id: int, total_amount: float = 0) -> Order:
    """创建新订单"""
    async with async_session() as session:
        async with session.begin():
            orm = OrderOrm(user_id=user_id, total_amount=total_amount)
            session.add(orm)
            await session.flush()
            return Order.model_validate(orm)


async def order_update_status(id: int, status: str) -> Optional[Order]:
    """更新订单状态"""
    async with async_session() as session:
        async with session.begin():
            row = await session.get(OrderOrm, id)
            if row:
                row.status = status
                await session.flush()
                return Order.model_validate(row)
    return None


# --- Category ---
async def category_get_all() -> List[Category]:
    """获取所有分类"""
    async with async_session() as session:
        stmt = select(CategoryOrm)
        rows = (await session.scalars(stmt)).all()
        return [Category.model_validate(r) for r in rows]


async def category_create(name: str, parent_id: Optional[int] = None) -> Category:
    """创建分类"""
    async with async_session() as session:
        async with session.begin():
            orm = CategoryOrm(name=name, parent_id=parent_id)
            session.add(orm)
            await session.flush()
            return Category.model_validate(orm)


# --- Brand ---
async def brand_get_all() -> List[Brand]:
    """获取所有品牌"""
    async with async_session() as session:
        stmt = select(BrandOrm)
        rows = (await session.scalars(stmt)).all()
        return [Brand.model_validate(r) for r in rows]


async def brand_create(name: str, logo: str = "") -> Brand:
    """创建品牌"""
    async with async_session() as session:
        async with session.begin():
            orm = BrandOrm(name=name, logo=logo or None)
            session.add(orm)
            await session.flush()
            return Brand.model_validate(orm)


# --- Tag ---
async def tag_get_all() -> List[Tag]:
    """获取所有标签"""
    async with async_session() as session:
        stmt = select(TagOrm)
        rows = (await session.scalars(stmt)).all()
        return [Tag.model_validate(r) for r in rows]


async def tag_create(name: str) -> Tag:
    """创建标签"""
    async with async_session() as session:
        async with session.begin():
            orm = TagOrm(name=name)
            session.add(orm)
            await session.flush()
            return Tag.model_validate(orm)


# --- Coupon ---
async def coupon_get_all() -> List[Coupon]:
    """获取所有优惠券"""
    async with async_session() as session:
        stmt = select(CouponOrm)
        rows = (await session.scalars(stmt)).all()
        return [Coupon.model_validate(r) for r in rows]


async def coupon_create(code: str, discount: float, min_amount: float = 0) -> Coupon:
    """创建优惠券"""
    async with async_session() as session:
        async with session.begin():
            orm = CouponOrm(code=code, discount=discount, min_amount=min_amount)
            session.add(orm)
            await session.flush()
            return Coupon.model_validate(orm)


# --- Store ---
async def store_get_all() -> List[Store]:
    """获取所有店铺"""
    async with async_session() as session:
        stmt = select(StoreOrm)
        rows = (await session.scalars(stmt)).all()
        return [Store.model_validate(r) for r in rows]


async def store_create(name: str, description: str = "") -> Store:
    """创建店铺"""
    async with async_session() as session:
        async with session.begin():
            orm = StoreOrm(name=name, description=description or None)
            session.add(orm)
            await session.flush()
            return Store.model_validate(orm)


# --- Warehouse ---
async def warehouse_get_all() -> List[Warehouse]:
    """获取所有仓库"""
    async with async_session() as session:
        stmt = select(WarehouseOrm)
        rows = (await session.scalars(stmt)).all()
        return [Warehouse.model_validate(r) for r in rows]


# --- ProductVariant ---
async def product_variant_get_by_product(product_id: int) -> List[ProductVariant]:
    """根据商品 ID 获取规格列表"""
    async with async_session() as session:
        stmt = select(ProductVariantOrm).where(
            ProductVariantOrm.product_id == product_id
        )
        rows = (await session.scalars(stmt)).all()
        return [ProductVariant.model_validate(r) for r in rows]


# --- OrderItem ---
async def order_item_get_by_order(order_id: int) -> List[OrderItem]:
    """根据订单 ID 获取明细"""
    async with async_session() as session:
        stmt = select(OrderItemOrm).where(OrderItemOrm.order_id == order_id)
        rows = (await session.scalars(stmt)).all()
        return [OrderItem.model_validate(r) for r in rows]


# =====================================
# Build ErDiagram with QueryConfig
# =====================================

_entity_queries: dict[type, list] = {
    User: [
        QueryConfig(method=user_get_all),
        QueryConfig(method=user_get_by_id),
    ],
    Product: [
        QueryConfig(method=product_get_all),
        QueryConfig(method=product_get_by_id),
    ],
    Order: [
        QueryConfig(method=order_get_all),
        QueryConfig(method=order_get_by_id),
    ],
    Category: [QueryConfig(method=category_get_all)],
    Brand: [QueryConfig(method=brand_get_all)],
    Tag: [QueryConfig(method=tag_get_all)],
    Coupon: [QueryConfig(method=coupon_get_all)],
    Store: [QueryConfig(method=store_get_all)],
    Warehouse: [QueryConfig(method=warehouse_get_all)],
    ProductVariant: [QueryConfig(method=product_variant_get_by_product)],
    OrderItem: [QueryConfig(method=order_item_get_by_order)],
}

_entity_mutations: dict[type, list] = {
    User: [MutationConfig(method=user_create)],
    Product: [MutationConfig(method=product_create)],
    Order: [MutationConfig(method=order_create), MutationConfig(method=order_update_status)],
    Category: [MutationConfig(method=category_create)],
    Brand: [MutationConfig(method=brand_create)],
    Tag: [MutationConfig(method=tag_create)],
    Coupon: [MutationConfig(method=coupon_create)],
    Store: [MutationConfig(method=store_create)],
}

# Attach QueryConfig/MutationConfig to entities
for entity in _entities:
    kls = entity.kls
    if kls in _entity_queries:
        entity.queries = _entity_queries[kls]
    if kls in _entity_mutations:
        entity.mutations = _entity_mutations[kls]

diagram = ErDiagram(entities=[]).add_relationship(_entities)


# =====================================
# 初始化种子数据
# =====================================


async def init_db():
    """创建表并插入种子数据"""
    await create_tables()

    async with async_session() as session:
        async with session.begin():
            # Users
            session.add_all(
                [
                    UserOrm(id=1, username="zhangsan", email="zhangsan@example.com"),
                    UserOrm(id=2, username="lisi", email="lisi@example.com"),
                    UserOrm(id=3, username="wangwu", email="wangwu@example.com"),
                ]
            )
            # Addresses
            session.add_all(
                [
                    UserAddressOrm(
                        id=1,
                        user_id=1,
                        province="广东",
                        city="深圳",
                        district="南山区",
                        detail="科技园路1号",
                        is_default=True,
                    ),
                    UserAddressOrm(
                        id=2,
                        user_id=1,
                        province="广东",
                        city="深圳",
                        district="福田区",
                        detail="华强北路2号",
                    ),
                    UserAddressOrm(
                        id=3,
                        user_id=2,
                        province="北京",
                        city="北京",
                        district="朝阳区",
                        detail="望京路3号",
                        is_default=True,
                    ),
                    UserAddressOrm(
                        id=4,
                        user_id=3,
                        province="上海",
                        city="上海",
                        district="浦东新区",
                        detail="张江路4号",
                        is_default=True,
                    ),
                ]
            )
            # Brands
            session.add_all(
                [
                    BrandOrm(id=1, name="Apple"),
                    BrandOrm(id=2, name="Nike"),
                ]
            )
            # Categories (with nesting)
            session.add_all(
                [
                    CategoryOrm(id=1, name="电子产品"),
                    CategoryOrm(id=2, name="手机", parent_id=1),
                    CategoryOrm(id=3, name="电脑", parent_id=1),
                    CategoryOrm(id=4, name="服装"),
                    CategoryOrm(id=5, name="鞋子", parent_id=4),
                ]
            )
            # Stores
            session.add_all(
                [
                    StoreOrm(id=1, name="Apple 官方旗舰店", description="Apple 官方授权"),
                    StoreOrm(id=2, name="Nike 运动专营", description="Nike 品牌直营"),
                ]
            )
            # Tags
            session.add_all(
                [
                    TagOrm(id=1, name="新品"),
                    TagOrm(id=2, name="热卖"),
                    TagOrm(id=3, name="折扣"),
                    TagOrm(id=4, name="高端"),
                    TagOrm(id=5, name="运动"),
                ]
            )
            # Products
            session.add_all(
                [
                    ProductOrm(
                        id=1,
                        name="iPhone 15",
                        price=5999.0,
                        brand_id=1,
                        category_id=2,
                        store_id=1,
                    ),
                    ProductOrm(
                        id=2,
                        name="MacBook Pro",
                        price=12999.0,
                        brand_id=1,
                        category_id=3,
                        store_id=1,
                    ),
                    ProductOrm(
                        id=3,
                        name="Air Jordan 1",
                        price=1299.0,
                        brand_id=2,
                        category_id=5,
                        store_id=2,
                    ),
                    ProductOrm(
                        id=4,
                        name="iPad Air",
                        price=4799.0,
                        brand_id=1,
                        category_id=2,
                        store_id=1,
                    ),
                    ProductOrm(
                        id=5,
                        name="Nike Air Max",
                        price=899.0,
                        brand_id=2,
                        category_id=5,
                        store_id=2,
                    ),
                ]
            )
            # Product Variants
            session.add_all(
                [
                    ProductVariantOrm(id=1, product_id=1, sku="IP15-128-BLK", price=5999.0, stock=100),
                    ProductVariantOrm(id=2, product_id=1, sku="IP15-256-WHT", price=6499.0, stock=50),
                    ProductVariantOrm(id=3, product_id=2, sku="MBP14-512", price=12999.0, stock=30),
                    ProductVariantOrm(id=4, product_id=2, sku="MBP16-1T", price=18999.0, stock=10),
                    ProductVariantOrm(id=5, product_id=3, sku="AJ1-42-RED", price=1299.0, stock=80),
                    ProductVariantOrm(id=6, product_id=3, sku="AJ1-43-BLK", price=1299.0, stock=60),
                    ProductVariantOrm(id=7, product_id=4, sku="IPA-64-BLU", price=4799.0, stock=40),
                    ProductVariantOrm(id=8, product_id=5, sku="NAM-42-WHT", price=899.0, stock=120),
                ]
            )
            # Product Images
            session.add_all(
                [
                    ProductImageOrm(id=1, product_id=1, url="/img/iphone15-1.jpg", sort_order=1),
                    ProductImageOrm(id=2, product_id=1, url="/img/iphone15-2.jpg", sort_order=2),
                    ProductImageOrm(id=3, product_id=2, url="/img/macbook-1.jpg", sort_order=1),
                    ProductImageOrm(id=4, product_id=2, url="/img/macbook-2.jpg", sort_order=2),
                    ProductImageOrm(id=5, product_id=3, url="/img/aj1-1.jpg", sort_order=1),
                    ProductImageOrm(id=6, product_id=3, url="/img/aj1-2.jpg", sort_order=2),
                    ProductImageOrm(id=7, product_id=4, url="/img/ipad-1.jpg", sort_order=1),
                    ProductImageOrm(id=8, product_id=4, url="/img/ipad-2.jpg", sort_order=2),
                    ProductImageOrm(id=9, product_id=5, url="/img/airmax-1.jpg", sort_order=1),
                    ProductImageOrm(id=10, product_id=5, url="/img/airmax-2.jpg", sort_order=2),
                ]
            )
            # Product Tags (M:N)
            from .orm.tables import product_tag

            await session.execute(
                product_tag.insert(),
                [
                    {"product_id": 1, "tag_id": 1},
                    {"product_id": 1, "tag_id": 4},
                    {"product_id": 2, "tag_id": 2},
                    {"product_id": 2, "tag_id": 4},
                    {"product_id": 3, "tag_id": 1},
                    {"product_id": 3, "tag_id": 5},
                    {"product_id": 4, "tag_id": 2},
                    {"product_id": 5, "tag_id": 3},
                    {"product_id": 5, "tag_id": 5},
                ],
            )
            # Store Staff (M:N)
            from .orm.tables import store_staff

            await session.execute(
                store_staff.insert(),
                [
                    {"store_id": 1, "user_id": 1},
                    {"store_id": 1, "user_id": 2},
                    {"store_id": 2, "user_id": 2},
                ],
            )
            # Attributes & Values
            session.add_all(
                [
                    AttributeOrm(id=1, name="颜色"),
                    AttributeOrm(id=2, name="尺寸"),
                    AttributeOrm(id=3, name="材质"),
                    AttributeOrm(id=4, name="容量"),
                    AttributeOrm(id=5, name="款式"),
                ]
            )
            session.add_all(
                [
                    AttributeValueOrm(id=1, attribute_id=1, value="黑色"),
                    AttributeValueOrm(id=2, attribute_id=1, value="白色"),
                    AttributeValueOrm(id=3, attribute_id=1, value="红色"),
                    AttributeValueOrm(id=4, attribute_id=2, value="S"),
                    AttributeValueOrm(id=5, attribute_id=2, value="M"),
                    AttributeValueOrm(id=6, attribute_id=2, value="L"),
                    AttributeValueOrm(id=7, attribute_id=3, value="皮革"),
                    AttributeValueOrm(id=8, attribute_id=3, value="网布"),
                    AttributeValueOrm(id=9, attribute_id=4, value="128GB"),
                    AttributeValueOrm(id=10, attribute_id=4, value="256GB"),
                    AttributeValueOrm(id=11, attribute_id=4, value="512GB"),
                    AttributeValueOrm(id=12, attribute_id=4, value="1TB"),
                    AttributeValueOrm(id=13, attribute_id=5, value="低帮"),
                    AttributeValueOrm(id=14, attribute_id=5, value="高帮"),
                    AttributeValueOrm(id=15, attribute_id=1, value="蓝色"),
                ]
            )
            # Product Attribute Values (M:N)
            from .orm.tables import product_attribute

            await session.execute(
                product_attribute.insert(),
                [
                    {"variant_id": 1, "value_id": 1},  # iPhone 15 Black
                    {"variant_id": 1, "value_id": 9},  # 128GB
                    {"variant_id": 2, "value_id": 2},  # iPhone 15 White
                    {"variant_id": 2, "value_id": 10},  # 256GB
                    {"variant_id": 3, "value_id": 11},  # MBP 512GB
                    {"variant_id": 4, "value_id": 12},  # MBP 1TB
                    {"variant_id": 5, "value_id": 3},  # AJ1 Red
                    {"variant_id": 5, "value_id": 14},  # 高帮
                    {"variant_id": 6, "value_id": 1},  # AJ1 Black
                    {"variant_id": 6, "value_id": 14},  # 高帮
                ],
            )
            # Orders
            session.add_all(
                [
                    OrderOrm(id=1, user_id=1, status="completed", total_amount=7298.0),
                    OrderOrm(id=2, user_id=1, status="shipped", total_amount=12999.0),
                    OrderOrm(id=3, user_id=2, status="pending", total_amount=2598.0),
                    OrderOrm(id=4, user_id=2, status="paid", total_amount=4799.0),
                    OrderOrm(id=5, user_id=3, status="pending", total_amount=899.0),
                    OrderOrm(id=6, user_id=3, status="refunded", total_amount=1299.0),
                ]
            )
            # Order Items
            session.add_all(
                [
                    OrderItemOrm(id=1, order_id=1, variant_id=1, quantity=1, unit_price=5999.0),
                    OrderItemOrm(id=2, order_id=1, variant_id=5, quantity=1, unit_price=1299.0),
                    OrderItemOrm(id=3, order_id=2, variant_id=3, quantity=1, unit_price=12999.0),
                    OrderItemOrm(id=4, order_id=3, variant_id=5, quantity=2, unit_price=1299.0),
                    OrderItemOrm(id=5, order_id=4, variant_id=7, quantity=1, unit_price=4799.0),
                    OrderItemOrm(id=6, order_id=5, variant_id=8, quantity=1, unit_price=899.0),
                    OrderItemOrm(id=7, order_id=6, variant_id=6, quantity=1, unit_price=1299.0),
                    OrderItemOrm(id=8, order_id=1, variant_id=2, quantity=1, unit_price=6499.0),
                    OrderItemOrm(id=9, order_id=2, variant_id=4, quantity=1, unit_price=18999.0),
                    OrderItemOrm(id=10, order_id=3, variant_id=6, quantity=1, unit_price=1299.0),
                    OrderItemOrm(id=11, order_id=4, variant_id=1, quantity=1, unit_price=5999.0),
                    OrderItemOrm(id=12, order_id=6, variant_id=8, quantity=1, unit_price=899.0),
                ]
            )
            # Payments
            session.add_all(
                [
                    PaymentOrm(id=1, order_id=1, method="wechat", amount=7298.0, status="success"),
                    PaymentOrm(id=2, order_id=2, method="alipay", amount=12999.0, status="success"),
                    PaymentOrm(id=3, order_id=4, method="wechat", amount=4799.0, status="success"),
                    PaymentOrm(id=4, order_id=6, method="alipay", amount=1299.0, status="refunded"),
                ]
            )
            # Refunds
            session.add_all(
                [
                    RefundOrm(id=1, order_id=6, amount=1299.0, reason="不想要了", status="approved"),
                    RefundOrm(id=2, order_id=2, amount=18999.0, reason="质量问题", status="pending"),
                ]
            )
            # Warehouses
            session.add_all(
                [
                    WarehouseOrm(id=1, name="华南仓", location="深圳"),
                    WarehouseOrm(id=2, name="华东仓", location="上海"),
                ]
            )
            # Inventory
            session.add_all(
                [
                    InventoryOrm(id=1, warehouse_id=1, variant_id=1, quantity=60),
                    InventoryOrm(id=2, warehouse_id=2, variant_id=1, quantity=40),
                    InventoryOrm(id=3, warehouse_id=1, variant_id=2, quantity=30),
                    InventoryOrm(id=4, warehouse_id=2, variant_id=2, quantity=20),
                    InventoryOrm(id=5, warehouse_id=1, variant_id=3, quantity=20),
                    InventoryOrm(id=6, warehouse_id=2, variant_id=3, quantity=10),
                    InventoryOrm(id=7, warehouse_id=1, variant_id=5, quantity=50),
                    InventoryOrm(id=8, warehouse_id=2, variant_id=5, quantity=30),
                ]
            )
            # Reviews
            session.add_all(
                [
                    ReviewOrm(id=1, product_id=1, user_id=1, rating=5, content="很好用"),
                    ReviewOrm(id=2, product_id=1, user_id=2, rating=4, content="不错"),
                    ReviewOrm(id=3, product_id=2, user_id=1, rating=5, content="性能强劲"),
                    ReviewOrm(id=4, product_id=3, user_id=2, rating=4, content="好看"),
                ]
            )
            # Coupons
            session.add_all(
                [
                    CouponOrm(id=1, code="NEW100", discount=100.0, min_amount=500.0),
                    CouponOrm(id=2, code="VIP500", discount=500.0, min_amount=3000.0),
                    CouponOrm(id=3, code="SALE200", discount=200.0, min_amount=1000.0),
                ]
            )
            # Coupon Usages
            session.add_all(
                [
                    CouponUsageOrm(id=1, coupon_id=1, user_id=1, order_id=1),
                    CouponUsageOrm(id=2, coupon_id=2, user_id=1, order_id=2),
                    CouponUsageOrm(id=3, coupon_id=3, user_id=2, order_id=3),
                    CouponUsageOrm(id=4, coupon_id=1, user_id=3, order_id=5),
                ]
            )
            # Shipments
            session.add_all(
                [
                    ShipmentOrm(
                        id=1, warehouse_id=1, store_id=1, status="delivered",
                        tracking_no="SF1234567890",
                    ),
                    ShipmentOrm(
                        id=2, warehouse_id=2, store_id=1, status="shipped",
                        tracking_no="SF0987654321",
                    ),
                    ShipmentOrm(
                        id=3, warehouse_id=1, store_id=2, status="pending",
                        tracking_no=None,
                    ),
                ]
            )
            # Shipment Items
            session.add_all(
                [
                    ShipmentItemOrm(id=1, shipment_id=1, order_item_id=1, quantity=1),
                    ShipmentItemOrm(id=2, shipment_id=1, order_item_id=2, quantity=1),
                    ShipmentItemOrm(id=3, shipment_id=2, order_item_id=3, quantity=1),
                    ShipmentItemOrm(id=4, shipment_id=2, order_item_id=9, quantity=1),
                    ShipmentItemOrm(id=5, shipment_id=3, order_item_id=4, quantity=1),
                    ShipmentItemOrm(id=6, shipment_id=3, order_item_id=10, quantity=1),
                ]
            )
