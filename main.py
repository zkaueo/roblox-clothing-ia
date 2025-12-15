from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="IA Roupas Roblox - TESTE")

@app.get("/")
def root():
    return {"status": "online"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/process")
def process():
    return {
        "template_url": "https://example.com/test.png",
        "preview_url": "https://example.com/preview"
    }
