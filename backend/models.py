from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Notice(BaseModel):
    id: str
    title: str
    category: str  # Examinations, Placements, Events, Fees & Finance, Scholarships, Campus & Hostel, Academics, Sports, General
    department: str  # Computer Science, Electronics, Mechanical, Civil, Management, Biotechnology, All Departments
    target_audience: List[str] = Field(default_factory=lambda: ["All Students"])
    priority: str = "Medium"  # Low, Medium, High, Critical
    content: str
    summary: Optional[str] = ""
    action_required: bool = False
    deadline: Optional[str] = None  # e.g., "2026-11-15T23:59:00" or "2026-11-15"
    published_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    posted_by: str = "Academic Affairs Office"
    tags: List[str] = Field(default_factory=list)
    image_path: Optional[str] = None
    extracted_from_ocr: bool = False
    views_count: int = 0
    bookmarks_count: int = 0
    is_active: bool = True

class NoticeCreate(BaseModel):
    title: str
    category: str
    department: str = "All Departments"
    target_audience: List[str] = Field(default_factory=lambda: ["All Students"])
    priority: str = "Medium"
    content: str
    summary: Optional[str] = ""
    action_required: bool = False
    deadline: Optional[str] = None
    posted_by: str = "Administrative Department"
    tags: List[str] = Field(default_factory=list)
    image_path: Optional[str] = None
    extracted_from_ocr: bool = False

class UserProfile(BaseModel):
    user_id: str
    name: str = "Student User"
    role: str = "student"  # student, faculty, admin
    department: str = "Computer Science"
    year: str = "3rd Year"
    interests: List[str] = Field(default_factory=lambda: ["Hackathons", "Placements", "AI", "Scholarships"])
    bookmarked_notice_ids: List[str] = Field(default_factory=list)
    history_notice_ids: List[str] = Field(default_factory=list)

class SearchQuery(BaseModel):
    query: str
    use_semantic: bool = True
    category: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[str] = None
    only_active_deadlines: bool = False
    limit: int = 10

class RecommendationRequest(BaseModel):
    user_id: Optional[str] = None
    department: Optional[str] = None
    year: Optional[str] = None
    interests: Optional[List[str]] = None
    limit: int = 6

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str

class NoticeChatRequest(BaseModel):
    notice_id: Optional[str] = None
    message: str
    model: str = "gemini"  # "gemini" or "claude"
    history: List[ChatMessage] = Field(default_factory=list)

class NoticeDraftRequest(BaseModel):
    prompt: str
    category: Optional[str] = "General"
    department: Optional[str] = "All Departments"
    urgency: Optional[str] = "Medium"
    model: str = "gemini"
    existing_content: Optional[str] = None

class OCRProcessResponse(BaseModel):
    status: str
    engine: str
    raw_text: str
    detected_title: Optional[str] = None
    detected_category: Optional[str] = None
    detected_department: Optional[str] = None
    detected_deadline: Optional[str] = None
    detected_urgency: Optional[str] = None
    confidence: float = 0.95
    lines: List[str] = Field(default_factory=list)
    suggested_tags: List[str] = Field(default_factory=list)
