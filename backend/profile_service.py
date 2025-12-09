from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import json
from jose import jwt
from auth_service import JWT_SECRET, JWT_ALGO

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DB = BASE_DIR / "profiles_db.json"
ACTIVITY_DB = BASE_DIR / "activity_db.json"


class Profile(BaseModel):
    email: str
    name: Optional[str] = ""


class ActivityItem(BaseModel):
    type: str  # 'ocr', 'chatbot', 'scam_report', 'scheme_view', 'login'
    description: str
    timestamp: str


class UserStats(BaseModel):
    total_logins: int = 0
    ocr_scans: int = 0
    chat_messages: int = 0
    scam_reports: int = 0
    schemes_viewed: int = 0
    member_since: str = ""
    last_active: str = ""


class DashboardResponse(BaseModel):
    profile: Profile
    stats: UserStats
    recent_activity: List[ActivityItem]


_PROFILE_CACHE = None
_PROFILE_CACHE_TS = 0
def _load_db(ttl=600) -> Dict[str, Dict]:
    global _PROFILE_CACHE, _PROFILE_CACHE_TS
    now = time.time()
    if _PROFILE_CACHE is not None and now - _PROFILE_CACHE_TS < ttl:
        return _PROFILE_CACHE
    if not PROFILE_DB.exists():
        return {}
    try:
        with PROFILE_DB.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                _PROFILE_CACHE = data
                _PROFILE_CACHE_TS = now
                return data
            return {}
    except Exception:
        return {}


def _save_db(data: Dict[str, Dict]):
    with PROFILE_DB.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


_ACTIVITY_CACHE = None
_ACTIVITY_CACHE_TS = 0
def _load_activity_db(ttl=600) -> Dict[str, List[Dict]]:
    global _ACTIVITY_CACHE, _ACTIVITY_CACHE_TS
    now = time.time()
    if _ACTIVITY_CACHE is not None and now - _ACTIVITY_CACHE_TS < ttl:
        return _ACTIVITY_CACHE
    if not ACTIVITY_DB.exists():
        return {}
    try:
        with ACTIVITY_DB.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                _ACTIVITY_CACHE = data
                _ACTIVITY_CACHE_TS = now
                return data
            return {}
    except Exception:
        return {}


def _save_activity_db(data: Dict[str, List[Dict]]):
    with ACTIVITY_DB.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_email_from_auth(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        email = payload.get("email") or payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return email
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def log_activity(email: str, activity_type: str, description: str):
    """Log user activity for analytics"""
    activity_db = _load_activity_db()
    if email not in activity_db:
        activity_db[email] = []
    
    activity_db[email].append({
        "type": activity_type,
        "description": description,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 50 activities per user
    activity_db[email] = activity_db[email][-50:]
    _save_activity_db(activity_db)
    
    # Update stats in profile db
    profile_db = _load_db()
    if email not in profile_db:
        profile_db[email] = {"name": "", "stats": {}, "member_since": datetime.now().isoformat()}
    
    stats = profile_db[email].get("stats", {})
    
    if activity_type == "login":
        stats["total_logins"] = stats.get("total_logins", 0) + 1
    elif activity_type == "ocr":
        stats["ocr_scans"] = stats.get("ocr_scans", 0) + 1
    elif activity_type == "chatbot":
        stats["chat_messages"] = stats.get("chat_messages", 0) + 1
    elif activity_type == "scam_report":
        stats["scam_reports"] = stats.get("scam_reports", 0) + 1
    elif activity_type == "scheme_view":
        stats["schemes_viewed"] = stats.get("schemes_viewed", 0) + 1
    
    stats["last_active"] = datetime.now().isoformat()
    profile_db[email]["stats"] = stats
    _save_db(profile_db)


@router.get("/me", response_model=Profile)
def get_my_profile(authorization: Optional[str] = Header(None)):
    email = _get_email_from_auth(authorization)
    db = _load_db()
    record = db.get(email, {})
    name = record.get("name", "")
    return Profile(email=email, name=name)


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(authorization: Optional[str] = Header(None)):
    email = _get_email_from_auth(authorization)
    
    # Get profile
    profile_db = _load_db()
    record = profile_db.get(email, {})
    name = record.get("name", "")
    
    # Get stats
    stats_data = record.get("stats", {})
    member_since = record.get("member_since", datetime.now().isoformat())
    
    stats = UserStats(
        total_logins=stats_data.get("total_logins", 1),
        ocr_scans=stats_data.get("ocr_scans", 0),
        chat_messages=stats_data.get("chat_messages", 0),
        scam_reports=stats_data.get("scam_reports", 0),
        schemes_viewed=stats_data.get("schemes_viewed", 0),
        member_since=member_since,
        last_active=stats_data.get("last_active", datetime.now().isoformat())
    )
    
    # Get recent activity
    activity_db = _load_activity_db()
    activities = activity_db.get(email, [])
    recent_activity = [
        ActivityItem(
            type=a["type"],
            description=a["description"],
            timestamp=a["timestamp"]
        )
        for a in reversed(activities[-10:])  # Last 10 activities
    ]
    
    return DashboardResponse(
        profile=Profile(email=email, name=name),
        stats=stats,
        recent_activity=recent_activity
    )


class UpdateProfileRequest(BaseModel):
    name: str


@router.post("/me", response_model=Profile)
def update_my_profile(payload: UpdateProfileRequest, authorization: Optional[str] = Header(None)):
    email = _get_email_from_auth(authorization)
    name = (payload.name or "").strip()
    db = _load_db()
    
    if email not in db:
        db[email] = {"member_since": datetime.now().isoformat()}
    
    db[email]["name"] = name
    _save_db(db)
    
    log_activity(email, "profile_update", "Updated profile name")
    
    return Profile(email=email, name=name)


class LogActivityRequest(BaseModel):
    type: str
    description: str


@router.post("/activity")
def log_user_activity(payload: LogActivityRequest, authorization: Optional[str] = Header(None)):
    email = _get_email_from_auth(authorization)
    log_activity(email, payload.type, payload.description)
    return {"status": "logged"}
