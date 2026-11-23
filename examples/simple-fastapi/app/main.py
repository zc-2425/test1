from fastapi import FastAPI

app = FastAPI(title="我的第一次自动部署")


@app.get("/healthz", summary="Check service health", description="Returns the service health status.")
def health():
    return {"status": "ok"}
