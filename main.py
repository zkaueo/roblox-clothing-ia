# ==============================
# IA ROUPAS ROBLOX - MAIN FINAL
# ==============================

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
import os
import shutil

# ==============================
# APP
# ==============================

app = FastAPI(
    title="IA Roupas Roblox",
    description="API para gerar roupas Roblox a partir de imagens (frente e costas)",
    version="2.0.0"
)

# ==============================
# CORS
# ==============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# PASTAS
# ==============================

BASE_DIR = os.getcwd()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==============================
# ROTAS
# ==============================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "IA Roupas Roblox",
        "docs": "/docs"
    }

@app.post("/generate")
async def generate_clothing(
    front_image: UploadFile = File(...),
    back_image: Optional[UploadFile] = File(None)
):
    try:
        job_id = str(uuid.uuid4())
        job_dir = os.path.join(UPLOAD_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        # --------- SALVA FRENTE ----------
        front_path = os.path.join(job_dir, "front.png")
        with open(front_path, "wb") as f:
            shutil.copyfileobj(front_image.file, f)

        # --------- SALVA COSTAS ----------
        back_path = None
        if back_image:
            back_path = os.path.join(job_dir, "back.png")
            with open(back_path, "wb") as f:
                shutil.copyfileobj(back_image.file, f)

        # --------- AQUI ENTRA A IA DEPOIS ----------
        # Por enquanto só valida e responde

        return {
            "success": True,
            "job_id": job_id,
            "front": "recebido",
            "back": "recebido" if back_image else "não enviado",
            "message": "Imagens processadas com sucesso"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================
# HEALTH CHECK
# ==============================

@app.get("/health")
def health():
    return {"status": "ok"}
