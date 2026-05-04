import pandas as pd
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 모델 임포트
from model.sales_record import SalesRecord
from model.product import Product
from model.user import User 
from model.product_stock import ProductStock

async def get_raw_db_excel(db: AsyncSession):
    # 1. 각 테이블 전체 데이터 비동기 조회
    res_sales = await db.execute(select(SalesRecord))
    res_products = await db.execute(select(Product))
    res_users = await db.execute(select(User))
    res_stocks = await db.execute(select(ProductStock))

    # 2. 결과 리스트 변환
    sales_list = [r[0] for r in res_sales.all()]
    product_list = [r[0] for r in res_products.all()]
    user_list = [r[0] for r in res_users.all()]
    stock_list = [r[0] for r in res_stocks.all()]

    # 3. Pandas 데이터프레임 생성
    df_sales = pd.DataFrame([vars(s) for s in sales_list])
    df_products = pd.DataFrame([vars(p) for p in product_list])
    df_users = pd.DataFrame([vars(u) for u in user_list])
    df_stocks = pd.DataFrame([vars(st) for st in stock_list])

    # 4. product_id 가공
    if not df_sales.empty and not df_products.empty:
        # 상품 ID와 이름을 매핑하는 딕셔너리 생성 {id: name}
        product_map = dict(zip(df_products['id'], df_products['name']))
        
        # product_id 컬럼에 map 함수를 적용하여 값을 변경 (매칭 안 될 경우 기존 ID 유지)
        df_sales['product_id'] = df_sales['product_id'].map(product_map).fillna(df_sales['product_id'])

    # 5. 전처리 (내부 필드 제거 및 시간대 처리)
    target_dfs = [
        ("Sales_Records", df_sales),
        ("Products", df_products),
        ("Users", df_users),
        ("Product_Stocks", df_stocks)
    ]

    for name, df in target_dfs:
        if not df.empty:
            # SQLAlchemy 객체 전용 필드 및 보안 필드 삭제
            df.drop(columns=['_sa_instance_state', 'password_hash', 'hashed_password'], errors='ignore', inplace=True)
            
            # Excel 에러 방지: 시간대 정보 제거
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.tz_localize(None)

    # 6. 엑셀 파일 생성
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sales.to_excel(writer, sheet_name='Sales_Records', index=False)
        df_products.to_excel(writer, sheet_name='Products', index=False)
        df_users.to_excel(writer, sheet_name='Users', index=False)
        df_stocks.to_excel(writer, sheet_name='Product_Stocks', index=False)
    
    output.seek(0)
    return output