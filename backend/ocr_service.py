from fastapi import APIRouter, File, UploadFile, HTTPException
import asyncio
from pydantic import BaseModel
from pathlib import Path
import cv2
import numpy as np
import tempfile
import fitz  # PyMuPDF

router = APIRouter()

# Lazy import for EasyOCR to avoid slow startup
_reader = None

def get_ocr_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en", "hi"], gpu=False)
    return _reader


class OCRResponse(BaseModel):
    text: str


def extract_pdf_text(pdf_path: str) -> str:
    text_out = []
    doc = fitz.open(pdf_path)
    for page in doc:
        text_out.append(page.get_text())
    return "\n".join(text_out)


from fastapi import Request
# --- Lightweight Rate Limiting ---
import time
RATE_LIMIT = {}  # (ip, endpoint): [timestamps]
def check_rate_limit(ip, endpoint, max_req=3, window=10):
    now = time.time()
    key = (ip, endpoint)
    timestamps = RATE_LIMIT.get(key, [])
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= max_req:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    timestamps.append(now)
    RATE_LIMIT[key] = timestamps

@router.post("/extract", response_model=OCRResponse)
async def extract_text(file: UploadFile = File(...), request: Request = None):
    if request:
        client_ip = request.client.host
        check_rate_limit(client_ip, 'ocr-extract')
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
        raise HTTPException(status_code=400, detail="Invalid file format. Upload JPG, PNG, or PDF.")

    temp = tempfile.NamedTemporaryFile(delete=False)
    try:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            temp.write(chunk)
        temp.close()
        file_path = temp.name
    except Exception:
        temp.close()
        Path(temp.name).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
    async def ocr_task():
        try:
            # If PDF → try text extraction first
            if file.filename.lower().endswith(".pdf"):
                pdf_text = extract_pdf_text(file_path)
                if pdf_text.strip():
                    return {"text": pdf_text}
            # Otherwise → OCR image
            img = cv2.imread(file_path)
            if img is None:
                raise HTTPException(status_code=500, detail="Failed to read image.")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)[1]
            try:
                reader = get_ocr_reader()
                result = reader.readtext(gray, detail=0)
                extracted_text = "\n".join(result)
            except Exception:
                raise HTTPException(status_code=500, detail="OCR processing failed. Please upload a valid image or PDF.")
            return {"text": extracted_text if extracted_text.strip() else "No readable text found."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")
    try:
        return await asyncio.wait_for(ocr_task(), timeout=10)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="OCR processing timed out. Please try again with a clearer image.")
    finally:
        Path(file_path).unlink(missing_ok=True)
