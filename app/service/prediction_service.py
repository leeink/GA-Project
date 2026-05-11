from sqlalchemy.ext.asyncio import AsyncSession
from service.sales_record_service_detail import find_monthly_sales, find_yearly_total, find_available_years

class PredictionService:
    
    @staticmethod
    async def predict_short_term(db: AsyncSession, base_year: int):
        """[왼쪽 차트] 선택한 연도 실적 패턴을 기준으로 2026년 단기 예측"""
        try:
            sales_base = await find_monthly_sales(db, str(base_year))
            sales_2026 = await find_monthly_sales(db, "2026")
            
            map_base = {int(m): int(s) for m, s in sales_base}
            map_2026 = {int(m): int(s) for m, s in sales_2026}
            
            # 1~4월 실적만 비교해서 성장률 계산
            common_months = [m for m in range(1, 5) if m in map_base and m in map_2026]
            
            if not common_months:
                growth_rate = 1.0
            else:
                total_base = sum(map_base[m] for m in common_months)
                total_2026 = sum(map_2026[m] for m in common_months)
                growth_rate = total_2026 / total_base if total_base > 0 else 1.0

            predictions = []
            for month in range(1, 13):
                # 💡 [단기 예측 핵심] 5월부터는 DB에 0이 있든 없든 무조건 예측값 덮어씌움!
                if month <= 4:
                    val = map_2026.get(month, 0)
                else:
                    val = int(map_base.get(month, 0) * growth_rate)
                
                predictions.append({"month": month, "sales": val})
                
            return predictions
        except Exception as e:
            print(f"Short-term Prediction Error: {e}")
            return [{"month": m, "sales": 0} for m in range(1, 13)]

    @staticmethod
    async def predict_long_term(db: AsyncSession, base_year: int):
        """[오른쪽 차트] 무조건 2015~2025년 고정 추세를 바탕으로 2026년 장기 예측"""
        try:
            years = await find_available_years(db)
            # 💡 [장기 예측 핵심] 드롭박스 선택값(base_year) 무시, 무조건 2015~2025년만 사용!
            past_years = [int(y) for y in years if 2015 <= int(y) <= 2025]
            
            if len(past_years) < 2:
                return [{"month": m, "sales": 0} for m in range(1, 13)]

            first_val = await find_yearly_total(db, str(min(past_years)))
            last_val = await find_yearly_total(db, "2025") # 마지막 연도 무조건 2025년 고정
            
            first_year_sales = int(first_val) if first_val else 0
            last_year_sales = int(last_val) if last_val else 0
            
            n = 2025 - min(past_years)
            if first_year_sales > 0 and n > 0:
                cagr = (last_year_sales / first_year_sales) ** (1 / n)
            else:
                cagr = 1.0

            # 2026년 예측 총액 (2025년 기준 1년치 성장)
            predicted_total_2026 = last_year_sales * cagr
            
            # 2025년 월별 비중으로 쪼개기
            sales_2025 = await find_monthly_sales(db, "2025")
            map_2025 = {int(m): int(s) for m, s in sales_2025}
            total_2025 = sum(map_2025.values())
            
            long_term_predictions = []
            for month in range(1, 13):
                m_sales = map_2025.get(month, 0)
                weight = m_sales / total_2025 if total_2025 > 0 else 1/12
                long_term_predictions.append({
                    "month": month,
                    "sales": int(predicted_total_2026 * weight)
                })
                
            return long_term_predictions
        except Exception as e:
            print(f"Long-term Prediction Error: {e}")
            return [{"month": m, "sales": 0} for m in range(1, 13)]