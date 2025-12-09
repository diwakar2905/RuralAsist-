from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path
from datetime import datetime

def get_cache(key, ttl=120):
def set_cache(key, value):
# --- In-memory response cache ---
import time
_RESPONSE_CACHE = {}
def get_cache(key, ttl=120):
    now = time.time()
    entry = _RESPONSE_CACHE.get(key)
    if entry and now - entry['ts'] < ttl:
        return entry['value']
    return None
def set_cache(key, value):
    _RESPONSE_CACHE[key] = {'value': value, 'ts': time.time()}

# --- In-memory FAQ dataset cache (30 min) ---
_FAQ_CACHE = None
_FAQ_CACHE_TS = 0
def load_faqs(ttl=1800) -> list:
    global _FAQ_CACHE, _FAQ_CACHE_TS
    now = time.time()
    if _FAQ_CACHE is not None and now - _FAQ_CACHE_TS < ttl:
        return _FAQ_CACHE
    if not FAQ_DB_PATH.exists():
        raise HTTPException(status_code=404, detail="FAQ database not found")
    try:
        with FAQ_DB_PATH.open("r", encoding="utf-8") as f:
            _FAQ_CACHE = json.load(f)
            _FAQ_CACHE_TS = now
            return _FAQ_CACHE
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid FAQ database format")

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
FAQ_DB_PATH = BASE_DIR / "faq_db.json"


class FAQSearchRequest(BaseModel):
    query: str
    limit: int = 20
    category: Optional[str] = None


class FAQVoteRequest(BaseModel):
    faq_id: str
    vote_type: str  # 'helpful' or 'unhelpful'


class FAQResponse(BaseModel):
    id: str
    category: str
    question: str
    answer: str
    keywords: List[str]
    helpful_count: int
    unhelpful_count: int


class SearchResponse(BaseModel):
    count: int
    results: List[dict]
    query: str
    categories: List[str]



_FAQ_CACHE = None
_FAQ_CACHE_TS = 0
def load_faqs(ttl=1800) -> List[dict]:
    """Load FAQs from JSON database with in-memory cache"""
    global _FAQ_CACHE, _FAQ_CACHE_TS
    now = time.time()
    if _FAQ_CACHE is not None and now - _FAQ_CACHE_TS < ttl:
        return _FAQ_CACHE
    if not FAQ_DB_PATH.exists():
        raise HTTPException(status_code=404, detail="FAQ database not found")
    try:
        with FAQ_DB_PATH.open("r", encoding="utf-8") as f:
            _FAQ_CACHE = json.load(f)
            _FAQ_CACHE_TS = now
            return _FAQ_CACHE
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid FAQ database format")


def save_faqs(faqs: List[dict]) -> bool:
    """Save FAQs to JSON database"""
    try:
        with FAQ_DB_PATH.open("w", encoding="utf-8") as f:
            json.dump(faqs, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving FAQs: {e}")
        return False


def advanced_match_score(query: str, item: dict) -> int:
    """Advanced scoring algorithm for FAQ matching"""
    q = query.lower().strip()
    score = 0
    
    # Question title match (highest priority)
    question_text = item.get("question", "").lower()
    if q in question_text:
        score += 100
        # Bonus for exact phrase match
        if q == question_text:
            score += 50
    
    # Answer content match
    answer_text = item.get("answer", "").lower()
    if q in answer_text:
        score += 60
    
    # Keywords exact match
    keywords = item.get("keywords", [])
    for keyword in keywords:
        if q == keyword.lower():
            score += 80
        elif q in keyword.lower():
            score += 40
    
    # Category match
    category = item.get("category", "").lower()
    if q in category:
        score += 30
    
    # Token-based fuzzy matching
    q_tokens = set(q.split())
    
    # Check question tokens
    question_tokens = set(question_text.split())
    overlap = len(q_tokens & question_tokens)
    score += overlap * 15
    
    # Check answer tokens
    answer_tokens = set(answer_text.split())
    overlap = len(q_tokens & answer_tokens)
    score += overlap * 10
    
    # Partial word matching
    all_text = f"{question_text} {answer_text} {' '.join(keywords)}".lower()
    for token in q_tokens:
        if len(token) >= 3:  # Only for meaningful tokens
            partial_matches = sum(1 for word in all_text.split() if token in word)
            score += partial_matches * 5
    
    # Popularity boost (based on helpful votes)
    helpful_count = item.get("helpful_count", 0)
    unhelpful_count = item.get("unhelpful_count", 0)
    if helpful_count > unhelpful_count:
        score += min(helpful_count - unhelpful_count, 20)  # Max 20 point boost
    
    return score


@router.get("/")
async def get_all_faqs():
    """Get all FAQs"""
    faqs = load_faqs()
    return {
        "count": len(faqs),
        "faqs": faqs,
        "categories": list(set(faq.get("category", "general") for faq in faqs))
    }


@router.get("/categories")
async def get_categories():
    """Get all available FAQ categories"""
    faqs = load_faqs()
    categories = list(set(faq.get("category", "general") for faq in faqs))
    return {
        "categories": categories,
        "count": len(categories)
    }


@router.get("/category/{category}")
async def get_faqs_by_category(category: str):
    """Get FAQs by category"""
    faqs = load_faqs()
    filtered = [faq for faq in faqs if faq.get("category", "").lower() == category.lower()]
    
    if not filtered:
        return {"count": 0, "faqs": [], "category": category}
    
    return {
        "count": len(filtered),
        "faqs": filtered,
        "category": category
    }


@router.post("/search")
async def search_faqs(req: FAQSearchRequest) -> SearchResponse:
    """Advanced FAQ search with scoring and filtering (cached by query/category/limit)"""
    cache_key = f"faq_search:{req.query.lower()}:{req.category or ''}:{req.limit}"
    cached = get_cache(cache_key, ttl=180)
    if cached:
        return cached
    faqs = load_faqs()
    # Filter by category if specified
    if req.category and req.category.lower() != "all":
        faqs = [faq for faq in faqs if faq.get("category", "").lower() == req.category.lower()]
    # Score and rank results
    ranked = []
    for faq in faqs:
        score = advanced_match_score(req.query, faq)
        if score > 0:
            faq_copy = faq.copy()
            faq_copy["_score"] = score
            ranked.append((score, faq_copy))
    ranked.sort(key=lambda x: x[0], reverse=True)
    # Limit results
    results = [faq for _, faq in ranked[:req.limit]]
    # Get available categories
    categories = list(set(faq.get("category", "general") for faq in faqs))
    resp = SearchResponse(
        count=len(results),
        results=results,
        query=req.query,
        categories=categories
    )
    set_cache(cache_key, resp)
    return resp


@router.post("/vote")
async def vote_faq(req: FAQVoteRequest):
    """Vote on FAQ helpfulness"""
    faqs = load_faqs()
    
    # Find the FAQ
    faq_index = None
    for i, faq in enumerate(faqs):
        if faq.get("id") == req.faq_id:
            faq_index = i
            break
    
    if faq_index is None:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    # Update vote count
    if req.vote_type == "helpful":
        faqs[faq_index]["helpful_count"] = faqs[faq_index].get("helpful_count", 0) + 1
    elif req.vote_type == "unhelpful":
        faqs[faq_index]["unhelpful_count"] = faqs[faq_index].get("unhelpful_count", 0) + 1
    else:
        raise HTTPException(status_code=400, detail="Invalid vote type")
    
    # Add timestamp
    faqs[faq_index]["last_voted_at"] = datetime.now().isoformat()
    
    # Save updated FAQs
    if save_faqs(faqs):
        return {
            "message": "Vote recorded successfully",
            "faq_id": req.faq_id,
            "vote_type": req.vote_type,
            "helpful_count": faqs[faq_index]["helpful_count"],
            "unhelpful_count": faqs[faq_index]["unhelpful_count"]
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save vote")


@router.get("/popular")
async def get_popular_faqs(limit: int = 10):
    """Get most helpful FAQs"""
    faqs = load_faqs()
    
    # Sort by helpfulness ratio
    def helpfulness_score(faq):
        helpful = faq.get("helpful_count", 0)
        unhelpful = faq.get("unhelpful_count", 0)
        total = helpful + unhelpful
        
        if total == 0:
            return 0
        
        # Calculate Wilson score interval for better ranking
        # This handles FAQs with few votes better than simple ratio
        p = helpful / total
        n = total
        z = 1.96  # 95% confidence
        
        if n == 0:
            return 0
            
        return (p + z*z/(2*n) - z * ((p*(1-p)+z*z/(4*n))/n)**0.5) / (1 + z*z/n)
    
    # Sort by helpfulness score
    sorted_faqs = sorted(faqs, key=helpfulness_score, reverse=True)
    
    return {
        "count": len(sorted_faqs[:limit]),
        "faqs": sorted_faqs[:limit],
        "type": "popular"
    }


@router.get("/stats")
async def get_faq_stats():
    """Get FAQ statistics"""
    faqs = load_faqs()
    
    total_faqs = len(faqs)
    total_helpful = sum(faq.get("helpful_count", 0) for faq in faqs)
    total_unhelpful = sum(faq.get("unhelpful_count", 0) for faq in faqs)
    total_votes = total_helpful + total_unhelpful
    
    categories = {}
    for faq in faqs:
        cat = faq.get("category", "general")
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total_faqs": total_faqs,
        "total_votes": total_votes,
        "helpful_votes": total_helpful,
        "unhelpful_votes": total_unhelpful,
        "helpfulness_ratio": total_helpful / total_votes if total_votes > 0 else 0,
        "categories": categories,
        "most_popular_category": max(categories.items(), key=lambda x: x[1])[0] if categories else None
    }


@router.get("/{faq_id}")
async def get_faq_by_id(faq_id: str):
    """Get specific FAQ by ID"""
    faqs = load_faqs()
    
    for faq in faqs:
        if faq.get("id") == faq_id:
            return faq
    
    raise HTTPException(status_code=404, detail="FAQ not found")
