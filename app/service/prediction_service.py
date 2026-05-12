import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy.ext.asyncio import AsyncSession
from service.sales_record_service_detail import find_monthly_sales, find_yearly_total, find_available_years

class PredictionService:
    
    @staticmethod
    async def predict_ml_sklearn(db: AsyncSession):
        """사이킷런 랜덤포레스트로 2026년 12개월 매출 예측 (이중 막대 차트용)"""
        try:
            years = await find_available_years(db)
            # 2015년부터 2025년까지의 데이터만 학습에 사용
            past_years = [int(y) for y in years if 2015 <= int(y) <= 2025]
            
            X_train = []
            y_train = []
            
            # DB에서 과거 데이터 수집 (안전하게 row 인덱스로 접근)
            for y in past_years:
                sales = await find_monthly_sales(db, str(y))
                for row in sales:
                    month = int(row[0])
                    val = int(row[1])
                    X_train.append([y, month])  # 특성: [연도, 월]
                    y_train.append(val)         # 정답: 매출액
                    
            if not X_train:
                return [0] * 12

            # 머신러닝 학습 (Random Forest)
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            # 2026년 예측 데이터 생성
            X_2026 = [[2026, m] for m in range(1, 13)]
            predictions = model.predict(X_2026)

            # 현실 반영: 2026년 1~4월은 실제 데이터로 덮어쓰기
            sales_2026 = await find_monthly_sales(db, "2026")
            map_2026 = {int(row[0]): int(row[1]) for row in sales_2026 if row[0] is not None}
            
            results = []
            for i, month in enumerate(range(1, 13)):
                # 1~4월 중에 실제 실적이 있으면 그걸 사용
                if month <= 4 and month in map_2026:
                    final_val = map_2026[month]
                else:
                    # 5월부터는 머신러닝 예측값 사용
                    final_val = int(predictions[i])
                results.append(final_val)
                
            # HTML 템플릿 차트에서 바로 쓸 수 있도록 1차원 리스트 반환
            return results
        
        except Exception as e:
            print(f"ML Prediction Error: {e}")
            return [0] * 12