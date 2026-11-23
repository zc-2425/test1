from fastapi import FastAPI

app = FastAPI()


@app.get("/healthz", summary="Check service health")
def health():
    return {"status": "ok"}
