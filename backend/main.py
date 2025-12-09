from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from pathlib import Path
import os

import models
from database import engine

# Routers
from ocr_service import router as ocr_router
from chatbot_service import router as chatbot_router
from schemes_service import router as schemes_router
from scam_service import router as scam_router
from faq_service import router as faq_router
from auth_service import router as auth_router
from profile_service import router as profile_router


BASE_DIR = Path(__file__).resolve().parent

# Create DB tables
models.Base.metadata.create_all(bind=engine)


app = FastAPI(title="RuralAssist Backend", version="1.0.0")
app.add_middleware(GZipMiddleware, minimum_size=500)

# Upload directory
UPLOADS_DIR = BASE_DIR / "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# CORS

# Read allowed origins from environment variable, fallback to defaults
frontend_urls_str = os.environ.get(
    "FRONTEND_URLS",
    "http://localhost:5500,http://127.0.0.1:5500,https://ruralassist.vercel.app,https://ruralasist-beta.vercel.app"
)
origins = [url.strip() for url in frontend_urls_str.split(",")]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers with prefixes
# Include all routers with prefixes
app.include_router(ocr_router, prefix="/ocr")
app.include_router(chatbot_router, prefix="/chatbot")
app.include_router(schemes_router, prefix="/schemes")
app.include_router(scam_router, prefix="/scam")
app.include_router(auth_router, prefix="/auth")
app.include_router(faq_router, prefix="/faq")
app.include_router(profile_router, prefix="/profile")

# --- Global 500 Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


@app.get("/")
def root():
    return {
        "message": "RuralAssist Backend Running Successfully!",
        "routes": [
            "/ocr",
            "/chatbot",
            "/schemes",
            "/scam",
            "/auth",
            "/faq",
            "/profile",
        ]
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
