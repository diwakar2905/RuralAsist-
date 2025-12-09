from fastapi import APIRouter, HTTPException, Request, Header
import time
from jose import jwt

from auth_service import JWT_SECRET, JWT_ALGO

# --- In-memory response cache ---
_RESPONSE_CACHE = {}
def get_cache(key, ttl=120):
    now = time.time()
    entry = _RESPONSE_CACHE.get(key)
    if entry and now - entry['ts'] < ttl:
        return entry['value']
    return None

def set_cache(key, value):
    _RESPONSE_CACHE[key] = {'value': value, 'ts': time.time()}

# --- Scam keywords/common scams JSON cache (30 min) ---
_SCAM_KEYWORDS_CACHE = None
_SCAM_KEYWORDS_CACHE_TS = 0
def load_scam_keywords(ttl=1800):
    global _SCAM_KEYWORDS_CACHE, _SCAM_KEYWORDS_CACHE_TS
    now = time.time()
    if _SCAM_KEYWORDS_CACHE is not None and now - _SCAM_KEYWORDS_CACHE_TS < ttl:
        return _SCAM_KEYWORDS_CACHE
    if not SCAM_KEYWORDS_PATH.exists():
        _SCAM_KEYWORDS_CACHE = {"high_risk": [], "medium_risk": [], "low_risk": []}
        return _SCAM_KEYWORDS_CACHE
    with SCAM_KEYWORDS_PATH.open("r", encoding="utf-8") as f:
        _SCAM_KEYWORDS_CACHE = json.load(f)
        _SCAM_KEYWORDS_CACHE_TS = now
        return _SCAM_KEYWORDS_CACHE

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
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
SCAM_KEYWORDS_PATH = BASE_DIR / "scam_keywords.json"
COMMON_SCAMS_PATH = BASE_DIR / "common_scams.json"
SCAM_REPORTS_DB_PATH = BASE_DIR / "scam_reports_db.json"


# --- Request/Response Models ---
class ScamReportRequest(BaseModel):
    description: str
    scam_type: Optional[str] = None
    location: Optional[str] = None
    anonymous: bool = False


class ScamAnalysisResponse(BaseModel):
    risk_level: str
    risk_score: float
    keywords_detected: List[str]
    analysis_text: str


class ScamReportResponse(BaseModel):
    report_id: str
    risk_level: str
    message: str


# --- Risk Keywords & Patterns ---
SCAM_KEYWORDS_CACHE = None
SAFE_KEYWORDS = {
    "official",
    "verified",
    "secure",
    "trusted",
    "legitimate",
    "government",
    "authentic",
    "real",
    "valid",
}


def load_scam_keywords():
    global SCAM_KEYWORDS_CACHE
    if SCAM_KEYWORDS_CACHE is not None:
        return SCAM_KEYWORDS_CACHE

    if not SCAM_KEYWORDS_PATH.exists():
        SCAM_KEYWORDS_CACHE = {"high_risk": [], "medium_risk": [], "low_risk": []}
        return SCAM_KEYWORDS_CACHE

    with SCAM_KEYWORDS_PATH.open("r", encoding="utf-8") as f:
        SCAM_KEYWORDS_CACHE = json.load(f)
        return SCAM_KEYWORDS_CACHE


# --- Risk Scoring Function ---
def calculate_risk_score(description: str):
    # Defensive: limit input length
    if not description or not description.strip():
        return "Low", 0, [], "No scam-like content detected."
    if len(description) > 10000:
        description = description[:2000]
    text = description.lower()
    score = 0
    detected = []

    data = load_scam_keywords()

    for item in data.get("high_risk", []):
        for pat in item.get("patterns", []):
            if item["keyword"].lower() in text or pat.lower().strip(".*") in text:
                score += item.get("risk_score", 85) / 5
                detected.append(item["keyword"])
                break

    for item in data.get("medium_risk", []):
        for pat in item.get("patterns", []):
            if item["keyword"].lower() in text or pat.lower().strip(".*") in text:
                score += item.get("risk_score", 55) / 10
                detected.append(item["keyword"])
                break

    for keyword in SAFE_KEYWORDS:
        if keyword in text:
            score -= 10

    word_count = len(text.split())
    if word_count < 10:
        score -= 10
    elif word_count > 50:
        score += 5

    if any(pattern in text for pattern in ["http://", "https://", ".com", ".in"]):
        score += 10
    if any(char.isdigit() for char in text) and len(text) > 20:
        score += 5

    score = max(0, min(100, score))

    if score >= 70:
        risk_level = "High"
        analysis_text = "🚨 HIGH-RISK SCAM — Do NOT share OTP, passwords, or bank details. Do NOT click any links. Contact your bank immediately if money was involved."
    elif score >= 40:
        risk_level = "Medium"
        analysis_text = "⚠️ MEDIUM-RISK — Be cautious. Verify by contacting official sources directly. Never share personal/financial information via unsolicited messages."
    else:
        risk_level = "Low"
        analysis_text = "✅ LOW-RISK — Appears low risk, but stay cautious. Always verify unexpected requests."

    return risk_level, score, list(set(detected)), analysis_text


# --- Endpoints ---
@router.post("/analyze", response_model=ScamAnalysisResponse)
def analyze_scam(request: ScamReportRequest, req: Request):
    import concurrent.futures
    import threading
    client_ip = req.client.host
    check_rate_limit(client_ip, 'scam-analyze')
    result = {}
    def analysis():
        rl, rs, kw, at = calculate_risk_score(request.description)
        result['risk_level'] = rl
        result['risk_score'] = rs
        result['keywords'] = kw
        result['analysis_text'] = at
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(analysis)
            future.result(timeout=3)
    except concurrent.futures.TimeoutError:
        raise HTTPException(status_code=504, detail="Scam analysis timed out. Please try again.")
    return ScamAnalysisResponse(
        risk_level=result['risk_level'],
        risk_score=result['risk_score'],
        keywords_detected=result['keywords'][:5],
        analysis_text=result['analysis_text'],
    )


@router.post("/report", response_model=ScamReportResponse)
def submit_scam_report(request: ScamReportRequest, authorization: Optional[str] = Header(None)):
    risk_level, risk_score, _, _ = calculate_risk_score(request.description)
    report_id = f"SCAM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    # --- JSON Persistence ---
    try:
        with SCAM_REPORTS_DB_PATH.open("r", encoding="utf-8") as f:
            db = json.load(f)
            reports = db.get("reports", [])
    except (FileNotFoundError, json.JSONDecodeError):
        reports = []

    email = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            email = payload.get("email")
        except jwt.JWTError:
            email = None

    # Compose new report dict
    new_report = {
        "report_id": report_id,
        "email": email,
        "description": request.description,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "scam_type": request.scam_type,
        "location": request.location,
        "created_at": datetime.utcnow().isoformat()
    }
    reports.append(new_report)

    # Save back to disk
    with SCAM_REPORTS_DB_PATH.open("w", encoding="utf-8") as f:
        json.dump({"reports": reports}, f, ensure_ascii=False, indent=2)

    return ScamReportResponse(
        report_id=report_id,
        risk_level=risk_level,
        message=f"Report submitted successfully! Risk Level: {risk_level}",
    )


@router.get("/common-scams")
def get_common_scams():
    cache_key = 'common_scams'
    cached = get_cache(cache_key, ttl=300)
    if cached:
        return cached
    # In-memory cache for common scams JSON
    now = time.time()
    if not hasattr(get_common_scams, '_COMMON_SCAMS_CACHE') or not hasattr(get_common_scams, '_COMMON_SCAMS_CACHE_TS'):
        get_common_scams._COMMON_SCAMS_CACHE = None
        get_common_scams._COMMON_SCAMS_CACHE_TS = 0
    if get_common_scams._COMMON_SCAMS_CACHE is not None and now - get_common_scams._COMMON_SCAMS_CACHE_TS < 1800:
        resp = get_common_scams._COMMON_SCAMS_CACHE
        set_cache(cache_key, resp)
        return resp
    if not COMMON_SCAMS_PATH.exists():
        raise HTTPException(status_code=404, detail="Common scams data not found")
    with COMMON_SCAMS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    adapted = []
    for item in data:
        adapted.append(
            {
                "type": item.get("title", "Scam"),
                "description": item.get("description", ""),
                "warning": "Be cautious and verify through official channels.",
                "examples": item.get("examples", []),
            }
        )
    resp = {"common_scams": adapted}
    get_common_scams._COMMON_SCAMS_CACHE = resp
    get_common_scams._COMMON_SCAMS_CACHE_TS = now
    set_cache(cache_key, resp)
    return resp
