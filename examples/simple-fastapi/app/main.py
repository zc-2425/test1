from fastapi import FastAPI

app = FastAPI()


@app.get("/healthz", summary="Check service health", description="Returns the service health status.")
def health():
    return {"status": "ok"}
