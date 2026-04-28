from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Sequence

from model.sales_record import SalesRecord

"""
SclesRecord
id : id? ㅁㄹ?
sold_at : 팔린시점(년/월/일/시간), 판매액?, 판매개수?
product_id : 상품고유코드
user_id : 유저id
quantity : 개수
sales_price : 판매가격
product : 외부 ORM에서 땡겨온 상품이름
"""

# #selectAll
# async def find_all(db: AsyncSession) -> Sequence[Any]:
#     DTO = await db.execute(
#         select(SalesRecord)
#     )

# 판매시점을 기준으로한 년간매출 추출
#selectYear_totalSales
async def selectYear_totalSales(db : AsyncSession) -> SalesRecord | None:
    DTO = await db.execute(
        select()
    )