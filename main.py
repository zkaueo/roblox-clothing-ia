from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image, ImageEnhance
from rembg import remove
import uuid, os

app = FastAPI()

os.makedirs("output", exist_ok=True)

@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    type: str = "shirt"
):
    img = Image.open(file.file).convert("RGBA")

    # remove fundo
    img = Image.open(remove(img)).convert("RGBA")

    # brilho e contraste
    img = ImageEnhance.Brightness(img).enhance(1.1)
    img = ImageEnhance.Contrast(img).enhance(1.2)

    # tamanho Roblox
    img = img.resize((585, 559))

    # template
    template_path = f"templates/{'shirt' if type == 'shirt' else 'pants'}.png"
    template = Image.open(template_path).convert("RGBA")
    template.paste(img, (0, 0), img)

    uid = str(uuid.uuid4())
    out_path = f"output/{uid}.png"
    template.save(out_path)

    return {
        "template_url": f"/file/{uid}.png",
        "preview_url": f"/file/{uid}.png"
    }

@app.get("/file/{name}")
def get_file(name: str):
    return FileResponse(f"output/{name}")
