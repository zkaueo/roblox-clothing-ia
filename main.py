from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image, ImageEnhance
from rembg import remove
from io import BytesIO
import uuid, os

app = FastAPI()

# ----------------- PASTAS ----------------- #
os.makedirs("output", exist_ok=True)
os.makedirs("templates", exist_ok=True)  # Templates: shirt.png e pants.png

TEMPLATES = {
    "camisa": "templates/shirt.png",
    "calca": "templates/pants.png"
}

# ----------------- ENDPOINT DE PROCESSAMENTO ----------------- #
@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    tipo: str = "camisa",
    brilho: float = 1.1,
    contraste: float = 1.1
):
    tipo = tipo.lower()
    if tipo not in TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Tipo inválido: {tipo}")

    # Abrir imagem
    try:
        img = Image.open(file.file).convert("RGBA")
    except Exception:
        raise HTTPException(status_code=400, detail="Arquivo inválido")

    # Remover fundo
    try:
        img_bytes = remove(img)
        img = Image.open(BytesIO(img_bytes)).convert("RGBA")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover fundo: {str(e)}")

    # Brilho e contraste
    img = ImageEnhance.Brightness(img).enhance(brilho)
    img = ImageEnhance.Contrast(img).enhance(contraste)

    # Template
    template_path = TEMPLATES[tipo]
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail="Template não encontrado")

    template = Image.open(template_path).convert("RGBA")
    img = img.resize(template.size)
    template.paste(img, (0, 0), img)

    # Salvar arquivo final
    uid = str(uuid.uuid4())
    out_path = f"output/{uid}.png"
    template.save(out_path)

    # Retorna JSON e HTML de preview
    file_url = f"/file/{uid}.png"
    html_preview = f"""
    <html>
        <head><title>Preview da roupa</title></head>
        <body style="text-align:center;">
            <h2>Preview - {tipo}</h2>
            <img src="{file_url}" style="max-width:90%;height:auto;"/>
            <p><a href="{file_url}" download>📥 Baixar imagem</a></p>
        </body>
    </html>
    """

    return {
        "template_url": file_url,
        "preview_url": file_url,
        "html_preview": html_preview
    }

# ----------------- ENDPOINT DE ARQUIVOS ----------------- #
@app.get("/file/{name}")
def get_file(name: str):
    file_path = f"output/{name}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(file_path)

# ----------------- ENDPOINT DE PREVIEW NO NAVEGADOR ----------------- #
@app.get("/preview/{name}")
def preview_file(name: str):
    file_path = f"output/{name}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    html_content = f"""
    <html>
        <head><title>Preview</title></head>
        <body style="text-align:center;">
            <img src="/file/{name}" style="max-width:90%;height:auto;"/>
            <p><a href="/file/{name}" download>📥 Baixar imagem</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
