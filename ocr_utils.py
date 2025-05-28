
import os
import tempfile
from typing import Tuple
from PIL import Image
from pdf2image import convert_from_bytes
import numpy as np
import shutil

import easyocr
import pytesseract

# Initiera EasyOCR-läsare
reader = easyocr.Reader(['sv', 'en'], gpu=False)

# Kontrollera om Tesseract är installerat i systemet
TESSERACT_INSTALLED = shutil.which("tesseract") is not None

def extract_text_easyocr(file) -> Tuple[str, str]:
    suffix = os.path.splitext(file.name)[1].lower()
    text = ""
    temp_path = ""

    if suffix in [".jpg", ".jpeg", ".png"]:
        image = Image.open(file)
        result = reader.readtext(np.array(image), detail=0)
        text = "\n".join(result)

    elif suffix == ".pdf":
        pages = convert_from_bytes(file.read(), dpi=300)
        for page_img in pages:
            result = reader.readtext(np.array(page_img), detail=0)
            text += "\n".join(result) + "\n"

        # För temp_path (för visning eller logg)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            pages[0].save(temp_file.name, "JPEG")
            temp_path = temp_file.name

    return text, temp_path

def extract_text_pytesseract(file) -> str:
    if not TESSERACT_INSTALLED:
        raise RuntimeError("❌ Tesseract OCR är inte installerat i miljön. Installera det eller använd EasyOCR.")

    suffix = os.path.splitext(file.name)[1].lower()
    text = ""

    if suffix in [".jpg", ".jpeg", ".png"]:
        image = Image.open(file)
        text = pytesseract.image_to_string(image, lang="swe")

    elif suffix == ".pdf":
        pages = convert_from_bytes(file.read(), dpi=300)
        for page_img in pages:
            text += pytesseract.image_to_string(page_img, lang="swe") + "\n"

    return text
