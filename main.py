from fastapi import FastAPI

app = FastAPI(title="PipelineIQ", version="0.1.0")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "platform": "PipelineIQ",
        "message": "Data Quality & Pipeline Intelligence Platform is active."
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PipelineIQ Backend Engine"
    }