"""
Smart Government Schemes System
- Offline-first with JSON database
- Live MyScheme API integration
- Fuzzy search with rapid fuzz
- Auto-update and merge
- Graceful offline handling
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from pathlib import Path
import os
from typing import List, Optional, Dict, Any, Tuple
import httpx
from datetime import datetime



# --- Lazy import for rapidfuzz (fuzzy search) ---
fuzz = None
FUZZY_AVAILABLE = None
def get_fuzz():
    global fuzz, FUZZY_AVAILABLE
    if fuzz is None:
        try:
            from rapidfuzz import fuzz as rf_fuzz
            fuzz = rf_fuzz
            FUZZY_AVAILABLE = True
        except ImportError:
            FUZZY_AVAILABLE = False
    return fuzz

# --- In-memory schemes DB cache (60 min) ---
_SCHEMES_CACHE = None
_SCHEMES_CACHE_TS = 0
def load_local_schemes(ttl=3600) -> list:
    global _SCHEMES_CACHE, _SCHEMES_CACHE_TS
    now = time.time()
    if _SCHEMES_CACHE is not None and now - _SCHEMES_CACHE_TS < ttl:
        return _SCHEMES_CACHE
    try:
        if SCHEMES_DB_PATH.exists():
            with open(SCHEMES_DB_PATH, "r", encoding="utf-8") as f:
                _SCHEMES_CACHE = json.load(f)
                _SCHEMES_CACHE_TS = now
                return _SCHEMES_CACHE
        return []
    except Exception as e:
        print(f"❌ Error loading local schemes: {e}")
        return []

router = APIRouter()

# Paths
SCHEMES_DB_PATH = Path(__file__).parent / "schemes_db.json"
MYSCHEME_API_BASE = "https://www.myscheme.gov.in/api/v2/search"

# ============================================================
# Request/Response Models
# ============================================================

class SchemeResponse(BaseModel):
    """Response model for a single scheme"""
    id: str
    title: str
    category: str
    state: str
    description: str
    benefits: str
    eligibility: str
    apply_link: str
    keywords: List[str]
    updated_at: Optional[str] = None
    source: str = "local"  # "local" or "online"

class SearchRequest(BaseModel):
    """Search request"""
    query: str
    limit: int = 50

class UpdateRequest(BaseModel):
    """Update request for syncing schemes"""
    query: str = "scheme"
    limit: int = 30

class UpdateResponse(BaseModel):
    """Update response"""
    added: int
    updated: int
    total: int
    message: str
    timestamp: str

class OnlineStatus(BaseModel):
    """Online status response"""
    status: str  # "online" or "offline"
    available_schemes: int
    last_updated: Optional[str] = None

# ============================================================
# Utility Functions
# ============================================================

def load_local_schemes() -> List[Dict[str, Any]]:
    """Load schemes from local JSON file"""
    try:
        if SCHEMES_DB_PATH.exists():
            with open(SCHEMES_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"❌ Error loading local schemes: {e}")
        return []

def save_local_schemes(schemes: List[Dict[str, Any]]) -> bool:
    """Save schemes to local JSON file"""
    try:
        with open(SCHEMES_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(schemes, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(schemes)} schemes to {SCHEMES_DB_PATH}")
        return True
    except Exception as e:
        print(f"❌ Error saving schemes: {e}")
        return False

def check_internet() -> bool:
    """Check if internet is available"""
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get("https://www.myscheme.gov.in/", follow_redirects=True)
            return response.status_code < 500
    except Exception as e:
        print(f"⚠️ Internet check failed: {e}")
        return False

def fetch_online_schemes(query: str, limit: int = 30) -> Optional[List[Dict[str, Any]]]:
    """Fetch schemes from MyScheme API"""
    try:
        if not check_internet():
            print("⚠️ No internet connection")
            return None
        
        with httpx.Client(timeout=10) as client:
            url = f"{MYSCHEME_API_BASE}?q={query}"
            response = client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different API response structures
                schemes = []
                if isinstance(data, dict) and "data" in data:
                    schemes = data["data"][:limit]
                elif isinstance(data, list):
                    schemes = data[:limit]
                
                print(f"✅ Fetched {len(schemes)} schemes from MyScheme API")
                return schemes
            else:
                print(f"⚠️ API returned status {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ Error fetching from MyScheme API: {e}")
        return None

def normalize_scheme(scheme: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize scheme data from various sources"""
    try:
        # Create ID from title if not present
        scheme_id = scheme.get("id") or scheme.get("id_en") or \
                    scheme.get("title", "").lower().replace(" ", "_")[:20]
        
        normalized = {
            "id": scheme_id,
            "title": scheme.get("title") or scheme.get("title_en") or "Unknown",
            "category": scheme.get("category") or scheme.get("sector") or "other",
            "state": scheme.get("state") or scheme.get("state_name") or "central",
            "description": scheme.get("description") or scheme.get("description_en") or "",
            "benefits": scheme.get("benefits") or scheme.get("ben_short_desc_en") or "",
            "eligibility": scheme.get("eligibility") or scheme.get("eligible_desc_en") or "",
            "apply_link": scheme.get("apply_link") or scheme.get("url") or "#",
            "keywords": scheme.get("keywords") or [],
            "updated_at": datetime.now().isoformat(),
            "source": scheme.get("source", "online")
        }
        
        return normalized if normalized["title"] != "Unknown" else None
    except Exception as e:
        print(f"❌ Error normalizing scheme: {e}")
        return None

def merge_schemes(local: List[Dict[str, Any]], 
                 online: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Merge local and online schemes
    Returns: (merged_list, added_count, updated_count)
    """
    added = 0
    updated = 0
    
    # Create local dict for quick lookup
    local_dict = {s["id"]: s for s in local}
    
    # Normalize and merge online schemes
    for online_scheme in online:
        normalized = normalize_scheme(online_scheme)
        if not normalized:
            continue
        
        scheme_id = normalized["id"]
        
        if scheme_id in local_dict:
            # Update existing
            local_dict[scheme_id].update(normalized)
            updated += 1
        else:
            # Add new
            local_dict[scheme_id] = normalized
            added += 1
    
    merged = list(local_dict.values())
    print(f"✅ Merged schemes: {added} added, {updated} updated, {len(merged)} total")
    
    return merged, added, updated

def search_schemes_fuzzy(query: str, schemes: List[Dict[str, Any]], 
                        threshold: int = 60) -> List[Dict[str, Any]]:
    """
    Search schemes using fuzzy matching (requires rapidfuzz)
    Returns matched schemes sorted by score
    """
    if FUZZY_AVAILABLE is None:
        get_fuzz()
    if not FUZZY_AVAILABLE or not query.strip():
        return []
    fuzz_func = get_fuzz()
    results = []
    query_lower = query.lower()
    for scheme in schemes:
        # Search in multiple fields
        fields = [
            (scheme.get("title", ""), 100),      # Title highest weight
            (scheme.get("description", ""), 80),
            (scheme.get("category", ""), 60),
            (" ".join(scheme.get("keywords", [])), 70),
        ]
        max_score = 0
        for field_text, weight in fields:
            score = fuzz_func.partial_ratio(query_lower, field_text.lower()) * weight / 100
            max_score = max(max_score, score)
        if max_score >= threshold:
            results.append((scheme, max_score))
    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results]

def search_schemes_keyword(query: str, schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Search schemes using keyword matching (no dependencies)
    Searches in title, description, category, keywords, state
    """
    if not query.strip():
        return []
    
    query_lower = query.lower()
    results = []
    
    for scheme in schemes:
        # Check multiple fields
        if (query_lower in scheme.get("title", "").lower() or
            query_lower in scheme.get("description", "").lower() or
            query_lower in scheme.get("category", "").lower() or
            query_lower in scheme.get("state", "").lower() or
            any(query_lower in kw.lower() for kw in scheme.get("keywords", []))):
            results.append(scheme)
    
    return results

# ============================================================
# API Endpoints
# ============================================================

@router.get("")
async def list_schemes(q: Optional[str] = None, state: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return schemes as a plain array (frontend expects an array).
    Optional filters: `q` (search), `state`, `category`.
    Gracefully returns [] if database is missing/empty.
    """
    schemes = load_local_schemes()
    if not schemes:
        return []

    def norm(s: str) -> str:
        return (s or "").strip().lower()

    qn = norm(q) if q else None
    st = norm(state) if state else None
    cat = norm(category) if category else None

    def matches(scheme: Dict[str, Any]) -> bool:
        if qn:
            hay = " ".join([
                scheme.get("title", ""),
                scheme.get("description", ""),
                scheme.get("category", ""),
                scheme.get("state", ""),
                " ".join(scheme.get("keywords", [])),
            ]).lower()
            if qn not in hay:
                return False
        if st and norm(scheme.get("state", "")) != st:
            return False
        if cat and norm(scheme.get("category", "")) != cat:
            return False
        return True

    filtered = [s for s in schemes if matches(s)]
    return filtered

@router.get("/local", response_model=Dict[str, Any])
async def get_local_schemes() -> Dict[str, Any]:
    """
    Get schemes from local JSON database (offline mode), with in-memory cache
    Always returns a JSON object with a 'schemes' array for frontend compatibility.
    """
    cache_key = 'schemes_local'
    cached = get_cache(cache_key, ttl=300)
    if cached:
        # Ensure response is always an object with 'schemes' key
        if isinstance(cached, list):
            return {
                "source": "local",
                "total": len(cached),
                "schemes": cached,
                "timestamp": datetime.now().isoformat()
            }
        return cached
    schemes = load_local_schemes()
    # If load_local_schemes returns a list, wrap it
    if isinstance(schemes, list):
        resp = {
            "source": "local",
            "total": len(schemes),
            "schemes": schemes,
            "timestamp": datetime.now().isoformat()
        }
    else:
        # If already a dict/object, use as is
        resp = schemes
    set_cache(cache_key, resp)
    return resp

@router.get("/online", response_model=Dict[str, Any])
async def get_online_schemes(q: str = "scheme") -> Dict[str, Any]:
    """
    Get schemes from MyScheme API (online)
    Returns {"status": "offline"} if no internet
    """
    if not check_internet():
        return {
            "status": "offline",
            "message": "No internet connection available",
            "schemes": []
        }
    
    schemes = fetch_online_schemes(q, limit=50)
    
    if schemes is None:
        return {
            "status": "offline",
            "message": "Failed to fetch from API",
            "schemes": []
        }
    
    # Normalize schemes
    normalized = [normalize_scheme(s) for s in schemes]
    normalized = [s for s in normalized if s is not None]
    
    return {
        "status": "online",
        "total": len(normalized),
        "schemes": normalized,
        "query": q,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/update", response_model=UpdateResponse)
async def update_schemes(request: UpdateRequest) -> UpdateResponse:
    """
    Update local schemes database with online data
    - Fetches from MyScheme API
    - Merges with local data
    - Saves updated JSON
    - Returns merge statistics
    """
    # Load current local schemes
    local_schemes = load_local_schemes()
    
    # Fetch online schemes
    online_schemes = fetch_online_schemes(request.query, request.limit)
    
    if online_schemes is None:
        # No internet - return current state
        return UpdateResponse(
            added=0,
            updated=0,
            total=len(local_schemes),
            message="❌ No internet connection. Using local schemes.",
            timestamp=datetime.now().isoformat()
        )
    
    # Merge schemes
    merged_schemes, added, updated = merge_schemes(local_schemes, online_schemes)
    
    # Save to file
    save_local_schemes(merged_schemes)
    
    return UpdateResponse(
        added=added,
        updated=updated,
        total=len(merged_schemes),
        message=f"🎉 {added} new schemes added, {updated} updated. Total: {len(merged_schemes)}",
        timestamp=datetime.now().isoformat()
    )

@router.get("/search", response_model=Dict[str, Any])
async def search_schemes(q: str, fuzzy: bool = True, limit: int = 50) -> Dict[str, Any]:
    """
    Search schemes using keyword or fuzzy matching
    
    Query Parameters:
    - q: Search query (required)
    - fuzzy: Use fuzzy matching if available (default: true)
    - limit: Max results to return (default: 50)
    
    Returns schemes from local database with search results
    """
    if not q.strip():
        # Graceful empty search response
        return {
            "count": 0,
            "schemes": [],
            "query": q,
            "search_type": "none",
            "timestamp": datetime.now().isoformat(),
            "fuzzy_available": FUZZY_AVAILABLE,
        }
    
    # Load schemes
    schemes = load_local_schemes()
    
    if not schemes:
        return {
            "count": 0,
            "schemes": [],
            "query": q,
            "search_type": "none",
            "timestamp": datetime.now().isoformat(),
            "fuzzy_available": FUZZY_AVAILABLE,
        }
    
    # Search using available method
    if fuzzy and FUZZY_AVAILABLE:
        results = search_schemes_fuzzy(q, schemes, threshold=50)
        search_type = "fuzzy"
    else:
        results = search_schemes_keyword(q, schemes)
        search_type = "keyword"
    
    # Limit results
    results = results[:limit]
    
    return {
        "query": q,
        "search_type": search_type,
        "count": len(results),
        "schemes": results,
        "timestamp": datetime.now().isoformat(),
        "fuzzy_available": FUZZY_AVAILABLE,
    }

@router.get("/status", response_model=OnlineStatus)
async def check_status() -> OnlineStatus:
    """
    Check system status: online/offline + available schemes (cached)
    """
    cache_key = 'schemes_status'
    cached = get_cache(cache_key, ttl=120)
    if cached:
        return cached
    is_online = check_internet()
    schemes = load_local_schemes()
    last_updated = None
    if schemes and "updated_at" in schemes[0]:
        last_updated = schemes[0]["updated_at"]
    resp = OnlineStatus(
        status="online" if is_online else "offline",
        available_schemes=len(schemes),
        last_updated=last_updated
    )
    set_cache(cache_key, resp)
    return resp

@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    schemes = load_local_schemes()
    
    return {
        "status": "healthy",
        "total_schemes": len(schemes),
        "database_path": str(SCHEMES_DB_PATH),
        "fuzzy_search_available": FUZZY_AVAILABLE,
        "api_endpoint": MYSCHEME_API_BASE,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/{scheme_id}", response_model=SchemeResponse)
async def get_scheme(scheme_id: str) -> SchemeResponse:
    """Get a single scheme by ID"""
    schemes = load_local_schemes()
    
    for scheme in schemes:
        if scheme["id"] == scheme_id:
            return SchemeResponse(**scheme)
    
    raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found")

@router.get("/category/{category}", response_model=Dict[str, Any])
async def get_by_category(category: str) -> Dict[str, Any]:
    """Filter schemes by category"""
    schemes = load_local_schemes()
    filtered = [s for s in schemes if s.get("category", "").lower() == category.lower()]
    
    if not filtered:
        raise HTTPException(status_code=404, detail=f"No schemes found in category '{category}'")
    
    return {
        "category": category,
        "total": len(filtered),
        "schemes": filtered
    }

@router.get("/state/{state}", response_model=Dict[str, Any])
async def get_by_state(state: str) -> Dict[str, Any]:
    """Filter schemes by state"""
    schemes = load_local_schemes()
    filtered = [s for s in schemes if s.get("state", "").lower() == state.lower()]
    
    if not filtered:
        raise HTTPException(status_code=404, detail=f"No schemes found for state '{state}'")
    
    return {
        "state": state,
        "total": len(filtered),
        "schemes": filtered
    }
