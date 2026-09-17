from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import io

app = FastAPI(
    title="PipelineIQ API",
    description="Cloud-native Data Quality & Pipeline Intelligence Platform",
    version="0.1.0"
)

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

        return {
            "status": "success",
            "message": "檔案上傳並完成資料品質檢測！",
            "metadata": metadata,
            "quality_report": quality_report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析檔案時發生錯誤: {str(e)}")