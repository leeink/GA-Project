import pandas as pd
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

# 모델 임포트
from model.sales_record import SalesRecord
from model.product import Product
from model.user import User 
from model.product_stock import ProductStock

async def get_raw_db_excel(db: AsyncSession):
    # 1. 각 테이블 데이터 비동기 전체 조회
    res_sales = await db.execute(select(SalesRecord))
    res_products = await db.execute(select(Product))
    res_users = await db.execute(select(User))
    res_stocks = await db.execute(select(ProductStock))

    # 2. 결과 객체 추출
    sales_list = [r[0] for r in res_sales.all()]
    product_list = [r[0] for r in res_products.all()]
    user_list = [r[0] for r in res_users.all()]
    stock_list = [r[0] for r in res_stocks.all()]

    # 3. Pandas 데이터프레임 변환
    df_sales = pd.DataFrame([vars(s) for s in sales_list])
    df_products = pd.DataFrame([vars(p) for p in product_list])
    df_users = pd.DataFrame([vars(u) for u in user_list])
    df_stocks = pd.DataFrame([vars(st) for st in stock_list])

    # 4. 필드 전처리 (순환 참조 방지 및 시간대 제거)
    target_dfs = [
        ("Sales_Records", df_sales),
        ("Products", df_products),
        ("Users", df_users),
        ("Product_Stocks", df_stocks)
    ]

    for name, df in target_dfs:
        if not df.empty:
            # SQLAlchemy 내부 상태 필드 제거
            df.drop(columns=['_sa_instance_state', 'password_hash'], errors='ignore', inplace=True)
            
            # === [에러 해결 핵심 로직] 시간대 정보 제거 ===
            # 데이터프레임의 모든 컬럼을 돌면서 datetime 타입인 경우 시간대를 제거(Naive 상태로 변환)
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    # dt.tz_localize(None)을 사용해 시간대 정보를 삭제합니다.
                    df[col] = df[col].dt.tz_localize(None)

    # 5. 메모리 버퍼(BytesIO)에 엑셀 파일 생성
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sales.to_excel(writer, sheet_name='Sales_Records', index=False)
        df_products.to_excel(writer, sheet_name='Products', index=False)
        df_users.to_excel(writer, sheet_name='Users', index=False)
        df_stocks.to_excel(writer, sheet_name='Product_Stocks', index=False)
    
    output.seek(0)
    return output