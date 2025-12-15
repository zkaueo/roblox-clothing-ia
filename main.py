from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image, ImageEnhance
from rembg import remove
from io import BytesIO
import uuid, os

# ================= APP (TEM QUE SER PRIMEIRO) =================
app = FastAPI()

# ================= ROOT (OBRIGATÓRIO NO RAILWAY) =================
@app.get("/")
def root():
    return {"status": "IA Roblox Online"}

# ================= PASTAS =================
os.makedirs("output", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# ================= CONFIG =================
TEMPLATES = {
    "camisa": "templates/shirt.png",
    "calca": "templates/pants.png"
}

PUBLIC_URL = os.getenv("PUBLIC_URL")
if not PUBLIC_URL:
    raise RuntimeError("❌ PUBLIC_URL não configurada")

PUBLIC_URL = PUBLIC_URL.rstrip("/")

# ================= PROCESSAMENTO =================
@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    tipo: str = "camisa",
    brilho: float = 1.1,
    contraste: float = 1.1
):
    tipo = tipo.lower()
    if tipo not in TEMPLATES:
        raise HTTPException(status_code=400, detail="Tipo inválido")

    # Abrir imagem
    try:
        img = Image.open(file.file).convert("RGBA")
    except:
        raise HTTPException(status_code=400, detail="Imagem inválida")

    # 🔽 REDUZ TAMANHO (EVITA 502)
    img.thumbnail((1024, 1024))

    # 🔥 REMBG BLINDADO (NÃO DERRUBA IA)
    try:
        img_bytes = remove(img)
        img = Image.open(BytesIO(img_bytes)).convert("RGBA")
    except Exception as e:
        print("⚠️ rembg falhou, usando imagem original:", e)
        img = img.convert("RGBA")

    # Ajustes visuais
    img = ImageEnhance.Brightness(img).enhance(brilho)
    img = ImageEnhance.Contrast(img).enhance(contraste)

    # Aplicar template
    template = Image.open(TEMPLATES[tipo]).convert("RGBA")
    img = img.resize(template.size)
    template.paste(img, (0, 0), img)

    # Salvar
    uid = f"{uuid.uuid4()}.png"
    out_path = f"output/{uid}"
    template.save(out_path)

    return {
        "template_url": f"{PUBLIC_URL}/file/{uid}",
        "preview_url": f"{PUBLIC_URL}/preview/{uid}"
    }

# ================= DOWNLOAD =================
@app.get("/file/{name}")
def get_file(name: str):
    path = f"output/{name}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="image/png")

# ================= PREVIEW WEB =================
@app.get("/preview/{name}")
def preview(name: str):
    path = f"output/{name}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404)

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Preview da Roupa</title>
        <style>
            body {{
                background: #111;
                color: white;
                text-align: center;
                font-family: Arial;
            }}
            img {{
                max-width: 90%;
                margin-top: 20px;
            }}
            a {{
                display: inline-block;
                margin-top: 20px;
                color: #00ff88;
                font-size: 18px;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <h2>Preview da Roupa Roblox</h2>
        <img src="{PUBLIC_URL}/file/{name}" />
        <br>
        <a href="{PUBLIC_URL}/file/{name}" download>📥 Baixar Template</a>
    </body>
    </html>
    """)
