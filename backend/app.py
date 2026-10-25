import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure pydantic doesn't scan locked OneDrive entry points
os.environ["PYDANTIC_DISABLE_PLUGINS"] = "1"

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    BASE_DIR, FRONTEND_DIR, UPLOAD_DIR,
    load_settings, save_settings
)
from .models import (
    Notice, NoticeCreate, UserProfile, SearchQuery,
    RecommendationRequest, NoticeChatRequest, NoticeDraftRequest,
    OCRProcessResponse
)
from .database import db
from .services.embedding_service import embedding_service
from .services.vector_search import vector_search_service, FAISS_AVAILABLE
from .services.recommendation_service import recommendation_service
from .services.llm_service import llm_service
from .services.ocr_service import OCRService, PADDLE_AVAILABLE

app = FastAPI(
    title="AI-Powered Smart Notice Management and Recommendation System",
    description="Advanced Smart Campus Notice Portal powered by PaddleOCR, Sentence Transformers, FAISS, Gemini, and Claude.",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global active user ID (defaults to student Alex Chen)
ACTIVE_USER_ID = "std-001"

def check_official_authority():
    """Verify that current user is an authorized college official, dean, or faculty."""
    user = db.get_user_profile(ACTIVE_USER_ID)
    if not user or user.get("role") not in ["official", "faculty", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Access Restricted: In accordance with university protocol, students are not permitted to publish, modify, or scan circulars. Only authorized College Officials, Dean, and Faculty hold publishing privileges."
        )
    return user

@app.on_event("startup")
async def startup_event():
    """Initialize FAISS Vector Index on application startup."""
    print("Initializing FAISS Vector Index from database...")
    notices = db.get_all_notices()
    vector_search_service.build_index(notices)
    print(f"System ready! Indexed {len(notices)} notices.")

# ----------------- Core API Endpoints ----------------- #

@app.get("/api/status")
async def get_system_status():
    """Check availability and active status of all 5 AI tools."""
    settings = load_settings()
    gemini_key = settings.get("gemini_api_key", "").strip()
    claude_key = settings.get("anthropic_api_key", "").strip()
    total_notices = len(db.get_all_notices())

    return {
        "status": "online",
        "system_name": "AI-Powered Smart Notice Management and Recommendation System",
        "ai_tools": {
            "paddle_ocr": {
                "installed": PADDLE_AVAILABLE,
                "engine": "PaddleOCR v3.7" if PADDLE_AVAILABLE else "Intelligent Vision & Heuristic OCR Engine",
                "status": "active"
            },
            "sentence_transformers": {
                "installed": True,
                "model": "all-MiniLM-L6-v2",
                "dimension": 384,
                "status": "active"
            },
            "faiss": {
                "installed": FAISS_AVAILABLE,
                "type": "IndexFlatIP (Cosine Similarity)" if FAISS_AVAILABLE else "Numpy Vector Dot-Product",
                "indexed_vectors": len(vector_search_service.id_to_notice_id),
                "status": "active"
            },
            "gemini": {
                "configured": bool(gemini_key),
                "model": "gemini-3.8-flash",
                "status": "live" if gemini_key else "simulated_nlp_ready"
            },
            "claude": {
                "configured": bool(claude_key),
                "model": "claude-3-5-sonnet",
                "status": "live" if claude_key else "simulated_nlp_ready"
            }
        },
        "preferred_llm": settings.get("preferred_llm", "gemini"),
        "total_notices": total_notices
    }

@app.get("/api/notices")
async def list_notices(
    category: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    only_active: bool = Query(True)
):
    """Retrieve filtered notices list."""
    notices = db.get_all_notices()
    
    if only_active:
        notices = [n for n in notices if n.get("is_active", True)]
    if category and category != "All":
        notices = [n for n in notices if n.get("category") == category]
    if department and department != "All Departments":
        notices = [n for n in notices if n.get("department") in [department, "All Departments"]]
    if priority and priority != "All":
        notices = [n for n in notices if n.get("priority") == priority]
    if search and search.strip():
        s = search.lower()
        notices = [
            n for n in notices
            if s in n.get("title", "").lower()
            or s in n.get("content", "").lower()
            or any(s in t.lower() for t in n.get("tags", []))
        ]

    return {"count": len(notices), "notices": notices}

@app.get("/api/notices/{notice_id}")
async def get_notice(notice_id: str):
    """Get single notice details and log reading history."""
    notice = db.get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    # Increment views
    db.increment_views(notice_id)
    # Add to current user history
    db.add_history(ACTIVE_USER_ID, notice_id)

    # Check if bookmarked by current user
    user = db.get_user_profile(ACTIVE_USER_ID)
    is_bookmarked = notice_id in (user.get("bookmarked_notice_ids", []) if user else [])

    return {
        "notice": notice,
        "is_bookmarked": is_bookmarked
    }

@app.post("/api/notices")
async def create_notice(payload: NoticeCreate):
    """Create a new notice, generate AI summary if omitted, and update FAISS index."""
    official_user = check_official_authority()

    notice_dict = payload.dict()
    notice_id = f"notif-{uuid.uuid4().hex[:6]}"
    notice_dict["id"] = notice_id
    # Tag publisher with official authority name
    notice_dict["posted_by"] = f"{official_user.get('name')} ({official_user.get('department')})"

    # Auto generate summary using Gemini / Claude if not provided
    if not notice_dict.get("summary") or len(notice_dict["summary"].strip()) == 0:
        settings = load_settings()
        preferred_model = settings.get("preferred_llm", "gemini")
        res = llm_service.summarize_notice(notice_dict, preferred_model=preferred_model)
        notice_dict["summary"] = res.get("summary", "")

    saved = db.create_notice(notice_dict)
    # Add vector to FAISS
    vector_search_service.add_notice(saved)

    return {"message": "Notice created successfully", "notice": saved}

@app.put("/api/notices/{notice_id}")
async def update_notice(notice_id: str, updates: dict):
    """Update existing notice and refresh FAISS index."""
    check_official_authority()
    updated = db.update_notice(notice_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    # Rebuild or update vector index
    vector_search_service.add_notice(updated)
    return {"message": "Notice updated successfully", "notice": updated}

@app.delete("/api/notices/{notice_id}")
async def delete_notice(notice_id: str):
    """Delete notice and rebuild vector index."""
    check_official_authority()
    success = db.delete_notice(notice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    # Rebuild index
    vector_search_service.build_index(db.get_all_notices())
    return {"message": "Notice deleted successfully"}

@app.post("/api/notices/{notice_id}/bookmark")
async def toggle_bookmark(notice_id: str):
    """Toggle bookmark state for current user."""
    is_bookmarked = db.toggle_bookmark(ACTIVE_USER_ID, notice_id)
    return {"notice_id": notice_id, "is_bookmarked": is_bookmarked}

@app.post("/api/notices/{notice_id}/summarize")
async def summarize_notice_endpoint(notice_id: str, model: Optional[str] = "gemini"):
    """Generate on-demand 3-bullet AI summary using Gemini or Claude."""
    notice = db.get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    res = llm_service.summarize_notice(notice, preferred_model=model)
    return res

# ----------------- FAISS & Search Endpoints ----------------- #

@app.post("/api/search")
async def search_notices(query: SearchQuery):
    """
    Semantic Search powered by Sentence Transformers & FAISS index.
    Finds semantically related notices even with natural questions.
    """
    if query.use_semantic:
        results = vector_search_service.search_by_text(
            query_text=query.query,
            top_k=query.limit,
            category=query.category,
            department=query.department,
            priority=query.priority
        )
    else:
        # Classical keyword search
        notices = db.get_all_notices()
        q = query.query.lower()
        matched = []
        for n in notices:
            if q in n.get("title", "").lower() or q in n.get("content", "").lower():
                matched.append({"notice": n, "similarity_score": 1.0})
        results = matched[:query.limit]

    return {
        "query": query.query,
        "engine": "FAISS + Sentence Transformers" if query.use_semantic else "Keyword Match",
        "count": len(results),
        "results": results
    }

# ----------------- Recommendation Endpoints ----------------- #

@app.get("/api/feed")
async def get_dashboard_feed():
    """
    Personalized home feed tailored for current user persona
    combining FAISS vector similarity, deadline urgency, and trending notices.
    """
    user = db.get_user_profile(ACTIVE_USER_ID)
    if not user:
        user = db.get_all_users()[0]

    feed = recommendation_service.get_feed_categories(user)
    return {
        "user": user,
        "feed": feed
    }

@app.post("/api/recommendations")
async def get_recommendations(req: RecommendationRequest):
    """Generate recommendations based on custom profile inputs."""
    user = db.get_user_profile(req.user_id or ACTIVE_USER_ID)
    if not user:
        user = {
            "user_id": "temp",
            "department": req.department or "Computer Science",
            "year": req.year or "3rd Year",
            "interests": req.interests or ["AI", "Hackathons"],
            "bookmarked_notice_ids": [],
            "history_notice_ids": []
        }
    else:
        if req.department:
            user["department"] = req.department
        if req.year:
            user["year"] = req.year
        if req.interests:
            user["interests"] = req.interests

    recs = recommendation_service.get_personalized_recommendations(user, limit=req.limit)
    return {"recommendations": recs}

# ----------------- PaddleOCR Upload ----------------- #

@app.post("/api/ocr/upload")
async def upload_and_ocr(file: UploadFile = File(...)):
    """
    Upload notice image/scanned circular, run PaddleOCR (or vision fallback),
    and extract dates, title, urgency, category, and department.
    """
    check_official_authority()
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".pdf"]:
        raise HTTPException(status_code=400, detail="Supported formats: JPG, PNG, WEBP, BMP, PDF")

    file_id = f"notice_scan_{uuid.uuid4().hex[:8]}{file_ext}"
    saved_path = UPLOAD_DIR / file_id

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    # Process through OCR
    ocr_result = OCRService.process_image(str(saved_path))
    ocr_result["file_url"] = f"/uploads/{file_id}"
    ocr_result["filename"] = file.filename

    return ocr_result

# ----------------- Gemini & Claude LLM Endpoints ----------------- #

@app.post("/api/ai/draft")
async def ai_draft_notice(req: NoticeDraftRequest):
    """Draft formal circular notice using Gemini or Claude."""
    check_official_authority()
    res = llm_service.draft_notice(
        prompt=req.prompt,
        category=req.category,
        department=req.department,
        urgency=req.urgency,
        model=req.model
    )
    return res

@app.post("/api/ai/chat")
async def ai_chat_notice(req: NoticeChatRequest):
    """NoticeBot Q&A chat grounded in specific notice details."""
    notice = db.get_notice_by_id(req.notice_id) if req.notice_id else None
    res = llm_service.chat_with_notice(
        notice=notice,
        user_message=req.message,
        history=[h.dict() for h in req.history],
        model=req.model
    )
    return res

# ----------------- Analytics & Vector Space ----------------- #

@app.get("/api/analytics")
async def get_analytics():
    """Returns analytics data and 2D FAISS vector space projection."""
    notices = db.get_all_notices()

    category_counts = {}
    dept_counts = {}
    priority_counts = {}
    total_views = 0
    total_bookmarks = 0

    for n in notices:
        c = n.get("category", "General")
        category_counts[c] = category_counts.get(c, 0) + 1

        d = n.get("department", "All Departments")
        dept_counts[d] = dept_counts.get(d, 0) + 1

        p = n.get("priority", "Medium")
        priority_counts[p] = priority_counts.get(p, 0) + 1

        total_views += n.get("views_count", 0)
        total_bookmarks += n.get("bookmarks_count", 0)

    # 2D PCA projection of vectors
    vector_points = vector_search_service.get_embedding_space_projection()

    return {
        "total_notices": len(notices),
        "total_views": total_views,
        "total_bookmarks": total_bookmarks,
        "categories": category_counts,
        "departments": dept_counts,
        "priorities": priority_counts,
        "vector_space_2d": vector_points
    }

# ----------------- User Profile & Settings ----------------- #

@app.get("/api/user/profile")
async def get_user_profile_endpoint():
    """Get active user profile."""
    user = db.get_user_profile(ACTIVE_USER_ID)
    all_users = db.get_all_users()
    return {"current_user": user, "available_personas": all_users}

@app.post("/api/user/switch")
async def switch_user(user_id: str = Form(...)):
    """Switch active user persona."""
    global ACTIVE_USER_ID
    user = db.get_user_profile(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    ACTIVE_USER_ID = user_id
    return {"message": f"Switched to user {user['name']}", "current_user": user}

@app.post("/api/user/profile")
async def update_user_profile_endpoint(updates: dict):
    """Update interests, department, or year of current user."""
    users = db.get_all_users()
    for u in users:
        if u["user_id"] == ACTIVE_USER_ID:
            u.update(updates)
            db.save_users(users)
            return {"message": "Profile updated", "user": u}
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/api/settings")
async def get_settings_endpoint():
    """Retrieve application settings (API keys masked for security)."""
    cfg = load_settings()
    masked = cfg.copy()
    if masked.get("gemini_api_key"):
        masked["gemini_api_key"] = masked["gemini_api_key"][:4] + "..." + masked["gemini_api_key"][-4:]
    if masked.get("anthropic_api_key"):
        masked["anthropic_api_key"] = masked["anthropic_api_key"][:4] + "..." + masked["anthropic_api_key"][-4:]
    return masked

@app.post("/api/settings")
async def update_settings_endpoint(payload: dict):
    """Save new API keys and preferred model."""
    current = load_settings()
    if "gemini_api_key" in payload and payload["gemini_api_key"].strip() and not payload["gemini_api_key"].endswith("..."):
        current["gemini_api_key"] = payload["gemini_api_key"].strip()
    if "anthropic_api_key" in payload and payload["anthropic_api_key"].strip() and not payload["anthropic_api_key"].endswith("..."):
        current["anthropic_api_key"] = payload["anthropic_api_key"].strip()
    if "preferred_llm" in payload:
        current["preferred_llm"] = payload["preferred_llm"]

    saved = save_settings(current)
    return {"message": "Settings saved successfully", "preferred_llm": saved.get("preferred_llm")}

# ----------------- Static Files & Frontend ----------------- #

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

@app.get("/")
async def serve_index():
    """Serve modern single page application."""
    index_file = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_file))
