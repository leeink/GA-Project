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
            past_years = []
            
            # 💡 방어 1: DB에서 온 연도 데이터를 안전하게 정수로 변환
            for y in years:
                if hasattr(y, '_mapping'):
                    y_val = list(y._mapping.values())[0]
                elif hasattr(y, 'keys') and callable(getattr(y, 'keys')):
                    y_val = list(dict(y).values())[0]
                elif isinstance(y, (tuple, list)):
                    y_val = y[0]
                else:
                    y_val = y
                
                if 2015 <= int(y_val) <= 2025:
                    past_years.append(int(y_val))
            
            X_train = []
            y_train = []
            
            # DB에서 과거 데이터 수집
            for y in past_years:
                # 🚨 핵심 원인 해결: 문자열(str)이 아닌 정수(int)로 전달!
                sales = await find_monthly_sales(db, int(y)) 
                
                for row in sales:
                    # 💡 방어 2: 딕셔너리, 튜플 상관없이 매출액 안전 추출
                    if hasattr(row, '_mapping'):
                        vals = list(row._mapping.values())
                    elif hasattr(row, 'keys') and callable(getattr(row, 'keys')):
                        vals = list(dict(row).values())
                    else:
                        vals = list(row)
                        
                    month = int(vals[0])
                    val = int(vals[1])
                        
                    X_train.append([int(y), month])
                    y_train.append(val)
                    
            if not X_train:
                return [0] * 12

            # 머신러닝 학습 (Random Forest)
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            # 2026년 예측 데이터 생성
            X_2026 = [[2026, m] for m in range(1, 13)]
            predictions = model.predict(X_2026)

            # 🚨 여기도 문자열 "2026" 대신 정수 2026 으로 전달!
            sales_2026 = await find_monthly_sales(db, 2026)
            map_2026 = {}
            
            for row in sales_2026:
                if hasattr(row, '_mapping'):
                    vals = list(row._mapping.values())
                elif hasattr(row, 'keys') and callable(getattr(row, 'keys')):
                    vals = list(dict(row).values())
                else:
                    vals = list(row)
                    
                if vals[0] is not None:
                    map_2026[int(vals[0])] = int(vals[1])
            
            results = []
            for i, month in enumerate(range(1, 13)):
                if month <= 4 and month in map_2026:
                    final_val = map_2026[month]
                else:
                    final_val = int(predictions[i])
                results.append(final_val)
                
            return results
        
        except Exception as e:
            print(f"🚨 ML Prediction Error 원인 파악: {e}")
            import traceback
            traceback.print_exc() # 만약 또 에러 나면 어디서 났는지 줄 번호까지 알려줌!
            return [0] * 12