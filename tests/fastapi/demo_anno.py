from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic_resolve import Resolver, ensure_subset

from tests.service.schema.schema import Product, ProductVariant, User

app = FastAPI(title="Demo API", description="A demo FastAPI application for router visualization")

@app.get("/products", tags=['for-restapi'], response_model=list[Product])
def get_product():
    return []

class PageUser(User):
    display_name: str = ''
    def post_display_name(self):
        return self.username + ' (' + self.email + ')'

class VariantA(ProductVariant):
    variant_type: str = 'A'

class VariantB(ProductVariant):
    variant_type: str = 'B'


type VariantUnion = VariantA | VariantB
class PageVariant(ProductVariant):
    product: PageUser | None


class PageOverall(BaseModel):
    brands: Annotated[list[PageBrand], Field(description="List of brands")]

class PageBrand(Product):
    products: Annotated[list[PageProduct], Field(description="List of products")]
    owner: Annotated[PageUser | None, Field(description="Owner of the brand")] = None


@ensure_subset(Product)
class PageProduct(BaseModel):
    id: int
    name: str
    price: float = Field(exclude=True)

    desc: str = ''
    def post_desc(self):
        return self.name + ' (processed)'

    variants: list[PageVariant] = []
    owner: PageUser | None = None
    union_variants: list[VariantUnion] = []

@app.get("/page_overall", tags=['for-page'], response_model=PageOverall)
async def get_page_info():
    page_overall = PageOverall(brands=[]) # focus on schema only
    return await Resolver().resolve(page_overall)
