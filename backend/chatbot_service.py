from fastapi import APIRouter
from pydantic import BaseModel
import json
from pathlib import Path
import re

router = APIRouter()


# --- In-memory cache for intents ---
BASE_DIR = Path(__file__).resolve().parent / "chatbot_language"
EN_PATH = BASE_DIR / "en.json"
HI_PATH = BASE_DIR / "hi.json"
_INTENT_CACHE = {}
_INTENT_CACHE_TS = {}
def load_language(lang: str, ttl=1800):
    now = time.time()
    path = HI_PATH if lang == "hi" else EN_PATH
    cache_key = str(path)
    if cache_key in _INTENT_CACHE and now - _INTENT_CACHE_TS[cache_key] < ttl:
        return _INTENT_CACHE[cache_key]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        _INTENT_CACHE[cache_key] = data
        _INTENT_CACHE_TS[cache_key] = now
        return data


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    reply: str
    intent: str


def detect_language(text: str) -> str:
    hindi_chars = set("अआइईउऊऋएऐओऔकखगघङचछजझटठडढणतथदधनपफबभमयरलवशषसहऑऍऎऒ")
    for char in text:
        if char in hindi_chars:
            return "hi"
    return "en"


def match_intent(query: str, intents: dict) -> str:
    q = query.lower().strip()
    best_intent = "unknown"
    best_score = 0

    for intent, obj in intents["intents"].items():
        score = 0
        keywords = obj.get("keywords", [])
        
        for kw in keywords:
            kw_lower = kw.lower()
            # Exact match gets higher score
            if kw_lower == q:
                score += 5
            # Word boundary match
            elif re.search(r'\b' + re.escape(kw_lower) + r'\b', q):
                score += 3
            # Partial/substring match
            elif kw_lower in q:
                score += 2
            # Query is contained in keyword (shorter query matching longer keyword)
            elif q in kw_lower and len(q) > 2:
                score += 1
                
        if score > best_score:
            best_score = score
            best_intent = intent

    return best_intent


@router.post("/message", response_model=ChatResponse)
def chatbot_message(req: ChatRequest):
    lang = detect_language(req.query)
    data = load_language(lang)

    intent = match_intent(req.query, data)
    response = data["intents"].get(intent, data["intents"]["unknown"])['response']

    return ChatResponse(
        reply=response,
        intent=intent
    )
