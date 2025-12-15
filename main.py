from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image, ImageEnhance
from rembg import remove
from io import BytesIO
import uuid, os

# ================= APP =================
app = FastAPI()

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

MAX_SIZE = (1024, 1024)

# ================= FUNÇÕES =================
def safe_remove_bg(img: Image.Image) -> Image.Image:
    """Remove fundo sem quebrar a IA"""
    try:
        img_bytes = remove(img)
        return Image.open(BytesIO(img_bytes)).convert("RGBA")
    except Exception as e:
        print("⚠️ rembg falhou, usando imagem original:", e)
        return img.convert("RGBA")

def split_front_back(img: Image.Image):
    """Divide imagem frente + costas automaticamente"""
    w, h = img.size
    half = w // 2
    front = img.crop((0, 0, half, h))
    back = img.crop((half, 0, w, h))
    return front, back

def apply_template(img: Image.Image, tipo: str) -> Image.Image:
    template = Image.open(TEMPLATES[tipo]).convert("RGBA")
    img = img.resize(template.size)
    template.paste(img, (0, 0), img)
    return template

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

    try:
        img = Image.open(file.file).convert("RGBA")
    except:
        raise HTTPException(status_code=400, detail="Imagem inválida")

    # Reduz tamanho (anti-502)
    img.thumbnail(MAX_SIZE)

    # Decide se é frente + costas
    is_double = img.width > img.height * 1.3

    results = []

    if is_double:
        parts = split_front_back(img)
    else:
        parts = [img]

    for part in parts:
        part = safe_remove_bg(part)
        part = ImageEnhance.Brightness(part).enhance(brilho)
        part = ImageEnhance.Contrast(part).enhance(contraste)
        final_img = apply_template(part, tipo)

        uid = f"{uuid.uuid4()}.png"
        out_path = f"output/{uid}"
        final_img.save(out_path)

        results.append({
            "template_url": f"{PUBLIC_URL}/file/{uid}",
            "preview_url": f"{PUBLIC_URL}/preview/{uid}"
        })

    # Se tiver frente + costas, retorna lista
    if len(results) > 1:
        return {
            "mode": "front_back",
            "results": results
        }

    return results[0]

# ================= DOWNLOAD =================
@app.get("/file/{name}")
def get_file(name: str):
    path = f"output/{name}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="image/png")

# ================= PREVIEW =================
@app.get("/preview/{name}")
def preview(name: str):
    path = f"output/{name}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404)

    return HTMLResponse(f"""
    <html>
      <body style="background:#111;color:white;text-align:center">
        <h2>Preview da Roupa Roblox</h2>
        <img src="{PUBLIC_URL}/file/{name}" style="max-width:90%"/>
        <br><br>
        <a href="{PUBLIC_URL}/file/{name}" download style="color:#0f0;font-size:18px">
          📥 Baixar Template
        </a>
      </body>
    </html>
    """)
