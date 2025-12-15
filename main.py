# =========================================
# IA ROUPAS ROBLOX - MAIN FINAL BLINDADO
# =========================================

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional
from PIL import Image
from rembg import remove
from io import BytesIO
import uuid
import os
import shutil

# =========================================
# APP
# =========================================

app = FastAPI(
    title="IA Roupas Roblox",
    description="API para gerar roupas Roblox com IA (frente e costas)",
    version="3.0.0"
)

# =========================================
# CORS
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# CONFIG
# =========================================

BASE_DIR = os.getcwd()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = ["image/png", "image/jpeg", "image/jpg"]

PUBLIC_URL = os.getenv("PUBLIC_URL")
if not PUBLIC_URL:
    raise RuntimeError("PUBLIC_URL não configurada")

PUBLIC_URL = PUBLIC_URL.rstrip("/")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# =========================================
# UTILIDADES
# =========================================

def validate_image(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Formato inválido (use PNG ou JPG)")

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "Imagem maior que 10MB")

def remove_background(img: Image.Image) -> Image.Image:
    try:
        out = remove(img)
        return Image.open(BytesIO(out)).convert("RGBA")
    except Exception:
        raise HTTPException(500, "Erro ao remover fundo da imagem")

# =========================================
# ROTAS
# =========================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "IA Roupas Roblox",
        "docs": f"{PUBLIC_URL}/docs"
    }

@app.post("/generate")
async def generate_clothing(
    front_image: UploadFile = File(...),
    back_image: Optional[UploadFile] = File(None),
    tipo: str = "camisa"
):
    validate_image(front_image)
    if back_image:
        validate_image(back_image)

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        # ---------- FRENTE ----------
        front = Image.open(front_image.file).convert("RGBA")
        front = remove_background(front)

        # ---------- COSTAS ----------
        back = None
        if back_image:
            back = Image.open(back_image.file).convert("RGBA")
            back = remove_background(back)

        # ---------- TEMPLATE ----------
        template_path = os.path.join(
            TEMPLATE_DIR,
            "shirt.png" if tipo == "camisa" else "pants.png"
        )

        if not os.path.exists(template_path):
            raise HTTPException(500, "Template Roblox não encontrado")

        template = Image.open(template_path).convert("RGBA")

        # ---------- APLICA ----------
        front = front.resize(template.size)
        template.paste(front, (0, 0), front)

        if back:
            back = back.resize(template.size)
            template.alpha_composite(back)

        # ---------- SALVA ----------
        output_name = f"{job_id}.png"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        template.save(output_path)

        return {
            "success": True,
            "template_url": f"{PUBLIC_URL}/file/{output_name}",
            "preview_url": f"{PUBLIC_URL}/file/{output_name}",
            "job_id": job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erro interno: {str(e)}")

@app.get("/file/{name}")
def get_file(name: str):
    path = os.path.join(OUTPUT_DIR, name)
    if not os.path.exists(path):
        raise HTTPException(404, "Arquivo não encontrado")
    return FileResponse(path, media_type="image/png")

@app.get("/health")
def health():
    return {"status": "ok"}
