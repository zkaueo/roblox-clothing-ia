from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image, ImageEnhance
from rembg import remove
from io import BytesIO
import uuid, os

app = FastAPI()

os.makedirs("output", exist_ok=True)
os.makedirs("templates", exist_ok=True)

TEMPLATES = {
    "camisa": "templates/shirt.png",
    "calca": "templates/pants.png"
}

# ---------------- PROCESSAMENTO ---------------- #
@app.post("/process")
async def process_image(
    request: Request,
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

    # Remover fundo
    try:
        img_bytes = remove(img)
        img = Image.open(BytesIO(img_bytes)).convert("RGBA")
    except:
        raise HTTPException(status_code=500, detail="Erro ao remover fundo")

    # Ajustes
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

    # 🔥 URL ABSOLUTA (CORREÇÃO PRINCIPAL)
    base_url = str(request.base_url).rstrip("/")
    file_url = f"{base_url}/file/{uid}"
    preview_url = f"{base_url}/preview/{uid}"

    return {
        "template_url": file_url,
        "preview_url": preview_url
    }

# ---------------- ARQUIVO ---------------- #
@app.get("/file/{name}")
def get_file(name: str):
    path = f"output/{name}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    return FileResponse(path)

# ---------------- PREVIEW WEB ---------------- #
@app.get("/preview/{name}")
def preview(name: str):
    path = f"output/{name}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404)

    return HTMLResponse(f"""
    <html>
      <body style="text-align:center;background:#111;color:white">
        <h2>Preview da roupa</h2>
        <img src="/file/{name}" style="max-width:90%"/>
        <br><br>
        <a href="/file/{name}" download style="color:#0f0">📥 Baixar</a>
      </body>
    </html>
    """)
