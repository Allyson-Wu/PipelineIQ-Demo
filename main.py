from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import io
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

app = FastAPI(
    title="PipelineIQ API",
    description="Cloud-native Data Quality & Pipeline Intelligence Platform",
    version="1.0.0"  # 僅將版本號更新為 1.0.0 正式版
)

# 載入 Supabase 設定
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("找不到 SUPABASE_URL 或 SUPABASE_KEY，請檢查 .env 設定檔。")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "platform": "PipelineIQ",
        "message": "PipelineIQ API is running"
    }


@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    # 檢查副檔名是否合規
    filename = file.filename
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="只支援 CSV 或 Excel 檔案 (.csv, .xlsx, .xls)")

    try:
        # 讀取上傳的檔案內容進記憶體
        contents = await file.read()
        
        # 依據副檔名用 Pandas 讀取資料
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        total_rows = len(df)
        total_cols = len(df.columns)

        # ------------------- Data Quality Engine -------------------
        # 1. 統計各欄位的缺失值
        null_counts = df.isnull().sum().to_dict()
        null_ratios = {col: round(count / total_rows, 4) if total_rows > 0 else 0 
                       for col, count in null_counts.items()}

        # 2. 統計重複列數量
        duplicate_rows = int(df.duplicated().sum())

        # 3. 計算基礎 Data Health Score (資料健康分數)
        avg_null_ratio = sum(null_ratios.values()) / total_cols if total_cols > 0 else 0
        duplicate_ratio = duplicate_rows / total_rows if total_rows > 0 else 0
        
        health_score = max(0, round(100 - (avg_null_ratio * 50 + duplicate_ratio * 50), 2))
        # -----------------------------------------------------------

        metadata = {
            "file_name": filename,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "column_names": list(df.columns),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }

        quality_report = {
            "health_score": health_score,
            "duplicate_rows": duplicate_rows,
            "null_counts": null_counts,
            "null_ratios": null_ratios
        }

        # ------------------- Save to Supabase -------------------
        audit_data = {
            "file_name": filename,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "health_score": health_score,
            "duplicate_rows": duplicate_rows,
            "null_counts": null_counts,
            "null_ratios": null_ratios
        }

        # 將組裝好的資料真正寫入 Supabase 中的 "quality_audits" table
        db_response = supabase.table("quality_audits").insert(audit_data).execute()
        # 寫入成功後，Supabase 會自動生成一組 UUID (id)，這行把它抓出來回傳給前端
        audit_id = db_response.data[0]["id"] if db_response.data else None
        # -----------------------------------------------------------

        return {
            "status": "success",
            "message": "檔案上傳完成，品質報告已成功寫入資料庫！",
            "audit_id": audit_id,
            "metadata": metadata,
            "quality_report": quality_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理或寫入資料庫時發生錯誤: {str(e)}")


# ==================== Day 8 新增的歷史查詢 API ====================

@app.get("/api/v1/audits")
def get_all_audits():
    """
    取得所有歷史審計紀錄列表（按建立時間由新到舊排序）
    """
    try:
        response = supabase.table("quality_audits") \
            .select("id, file_name, total_rows, total_columns, health_score, created_at") \
            .order("created_at", desc=True) \
            .execute()
            
        return {
            "status": "success",
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查詢歷史紀錄失敗: {str(e)}")


@app.get("/api/v1/audits/{audit_id}")
def get_audit_by_id(audit_id: str):
    """
    依據 audit_id (UUID) 取得單筆詳細品質報告
    """
    try:
        response = supabase.table("quality_audits") \
            .select("*") \
            .eq("id", audit_id) \
            .execute()
            
        if not response.data:
            raise HTTPException(status_code=404, detail=f"找不到 ID 為 {audit_id} 的審計紀錄。")
            
        return {
            "status": "success",
            "data": response.data[0]
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"查詢單筆紀錄失敗: {str(e)}")