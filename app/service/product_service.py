from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession



# 모든 상품 가져오기
async def find_all_product(db: AsyncSession):

    return

# 상품명(name)이 오징어링인 상품 가져오기
async def find_product_by_name(db: AsyncSession, name: str):

    return