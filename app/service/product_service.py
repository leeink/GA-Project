from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from model.product import Product, CategoryType


# 모든 상품 가져오기
async def find_all_product(db: AsyncSession):
    result = await db.execute(select(Product))
    return result.scalars().all()


# 상품명 검색 가져오기
async def find_product_search(db: AsyncSession, name: str):
    result = await db.execute(
        select(Product).where(Product.name.ilike(f"%{name}%"))
    )
    return result.scalars().all()


# 카테고리 별로 가져오기
async def find_product_by_category(db: AsyncSession, category: str):
    result = await db.execute(
        select(Product).where(Product.category == CategoryType(category))
    )
    return result.scalars().all()