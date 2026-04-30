import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db

router = APIRouter(prefix="/total", tags=["total"])

@router.get("", response_class=HTMLResponse)
async def get_total_page():
    return """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>보고서 센터</title>
        <style>
            body { font-family: 'Malgun Gothic', sans-serif; background-color: #f8f9fa; padding: 20px; text-align: center; }
            .box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 60%; margin: 0 auto 30px auto; }
            h2 { color: #2c3e50; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
            select { padding: 8px; font-size: 16px; border-radius: 5px; border: 1px solid #ccc; margin: 0 5px; }
            .row { margin: 15px 0; }
            button { padding: 12px 25px; font-size: 16px; font-weight: bold; color: white; border: none; border-radius: 5px; cursor: pointer; transition: 0.3s; }
            .btn-blue { background-color: #1e3a8a; }
            .btn-green { background-color: #059669; }
            button:hover { opacity: 0.8; }
        </style>
    </head>
    <body>
        <h1>📊 통합 보고서 및 사업보고서 센터</h1>
        
        <div class="box">
            <h2>기본 보고서 (11개년 고정)</h2>
            <p>11개년(2015~2025) 전체 포괄손익계산서만 단일 시트로 생성합니다.</p>
            <button class="btn-blue" onclick="location.href='/total/download'">📥 11개년 포괄손익계산서 다운로드</button>
        </div>

        <div class="box">
            <h2>맞춤형 통합 보고서 (범위 설정)</h2>
            <p>선택한 기간의 데이터로 <strong>포괄손익계산서 + 사업보고서(2개 시트)</strong>를 생성합니다.</p>
            
            <div class="row">
                <label>📅 연도: </label>
                <select id="s_year">
                    """ + "".join([f"<option value='{y}'>{y}년</option>" for y in range(2015, 2026)]) + """
                </select> ~ 
                <select id="e_year">
                    """ + "".join([f"<option value='{y}' {'selected' if y==2025 else ''}>{y}년</option>" for y in range(2015, 2026)]) + """
                </select>
            </div>
            
            <div class="row">
                <label>🗓️ 월별: </label>
                <select id="s_month">
                    """ + "".join([f"<option value='{m}'>{m}월</option>" for m in range(1, 13)]) + """
                </select> ~ 
                <select id="e_month">
                    """ + "".join([f"<option value='{m}' {'selected' if m==12 else ''}>{m}월</option>" for m in range(1, 13)]) + """
                </select>
            </div>
            
            <button class="btn-green" onclick="downloadCustom()">📅 선택 범위 통합 보고서 생성</button>
        </div>

        <script>
            function downloadCustom() {
                const sy = document.getElementById('s_year').value;
                const ey = document.getElementById('e_year').value;
                const sm = document.getElementById('s_month').value;
                const em = document.getElementById('e_month').value;
                window.location.href = `/total/report/custom?s_year=${sy}&e_year=${ey}&s_month=${sm}&e_month=${em}`;
            }
        </script>
    </body>
    </html>
    """

@router.get("/download")
async def download_excel(db: AsyncSession = Depends(get_db)):
    # 기존 11개년 단일 시트 생성 함수 호출
    try:
        from service.total_service import generate_excel_report
        save_dir = os.path.join("static", "reports")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "Full_Report_11Years.xlsx")
        await generate_excel_report(db, "2025", save_path)
        return FileResponse(path=save_path, filename="Full_Report_11Years.xlsx")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/custom")
async def download_custom_report(s_year: int, e_year: int, s_month: int, e_month: int, db: AsyncSession = Depends(get_db)):
    # 새로 만든 맞춤형 범위 생성 함수 호출
    try:
        from service.total_service import generate_custom_range_report
        save_dir = os.path.join("static", "reports")
        os.makedirs(save_dir, exist_ok=True)
        filename = f"Custom_Report_{s_year}to{e_year}.xlsx"
        save_path = os.path.join(save_dir, filename)
        
        await generate_custom_range_report(db, s_year, e_year, s_month, e_month, save_path)
        return FileResponse(path=save_path, filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))