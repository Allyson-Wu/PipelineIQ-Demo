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

        # 提取基礎 Metadata（元資料）
        metadata = {
            "file_name": filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "column_names": list(df.columns),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }

        return {
            "status": "success",
            "message": "檔案上傳並解析成功！",
            "metadata": metadata
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析檔案時發生錯誤: {str(e)}")