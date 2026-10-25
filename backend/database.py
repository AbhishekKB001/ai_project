import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid

from .models import Notice, UserProfile
from .config import DATA_DIR

NOTICES_FILE = DATA_DIR / "notices.json"
USERS_FILE = DATA_DIR / "users.json"

DEFAULT_SEED_NOTICES = [
    {
        "id": "notif-001",
        "title": "Mid-Term Examination Schedule & Hall Ticket Issuance - Fall 2026",
        "category": "Examinations",
        "department": "All Departments",
        "target_audience": ["1st Year", "2nd Year", "3rd Year", "4th Year"],
        "priority": "Critical",
        "content": "All undergraduate and postgraduate students are hereby notified that the Mid-Term Examinations for the Fall 2026 semester will commence from November 10, 2026. Hall tickets can be downloaded from the student ERP portal after clearing pending library dues and tuition fees. Students failing to bring physical printed hall tickets and college ID cards will strictly not be permitted inside the examination halls. The detailed time table for each branch has been uploaded on the exam wing notice board.",
        "summary": "Mid-term exams commence November 10, 2026. Download hall tickets from ERP after clearing dues. Physical hall ticket & ID card mandatory for entry.",
        "action_required": True,
        "deadline": (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "Controller of Examinations",
        "tags": ["Exams", "HallTicket", "MidTerm", "Schedule", "Mandatory"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 342,
        "bookmarks_count": 58,
        "is_active": True
    },
    {
        "id": "notif-002",
        "title": "Campus Placement Drive 2027: Microsoft & Google Software Engineering Roles",
        "category": "Placements",
        "department": "Computer Science",
        "target_audience": ["3rd Year", "4th Year"],
        "priority": "High",
        "content": "The Department of Training & Placement is thrilled to announce upcoming campus recruitment drives for Software Development Engineer (SDE-1) and Cloud Solutions Architect roles by Microsoft and Google. Eligibility: B.Tech CSE/IT with CGPA 8.0 and above, with no active backlogs. The initial online coding assessment is scheduled for November 18, 2026 on HackerRank. Interested candidates must register via the placement link and upload their updated resumes by November 12, 2026.",
        "summary": "Recruitment drive for Microsoft & Google SDE-1 roles for 3rd/4th year CSE/IT with CGPA >= 8.0. Register with resume by November 12, 2026.",
        "action_required": True,
        "deadline": (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "Training & Placement Cell",
        "tags": ["Placements", "Google", "Microsoft", "SDE", "Coding", "Jobs"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 520,
        "bookmarks_count": 112,
        "is_active": True
    },
    {
        "id": "notif-003",
        "title": "National Level Hackathon 'HackNova 2026' - $10,000 Prize Pool & Mentorship",
        "category": "Events",
        "department": "Computer Science",
        "target_audience": ["All Students"],
        "priority": "Medium",
        "content": "Innovation and Incubation Cell invites teams to register for 'HackNova 2026', a 36-hour national hackathon focused on Generative AI, Web3, and Green Computing. Winners will receive cash awards up to $10,000, cloud compute credits, and incubation support. Teams of 2 to 4 members from any department can participate. Prototype submission deadline is November 25, 2026.",
        "summary": "36-hour national hackathon on GenAI and Green Computing. Cash prize up to $10,000. Teams of 2-4 members. Submissions close November 25, 2026.",
        "action_required": True,
        "deadline": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "Innovation & Incubation Cell",
        "tags": ["Hackathon", "GenAI", "Innovation", "CashPrize", "Coding"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 410,
        "bookmarks_count": 89,
        "is_active": True
    },
    {
        "id": "notif-004",
        "title": "Merit-cum-Means Post-Matric Scholarship Scheme 2026-27 - Application Window",
        "category": "Scholarships",
        "department": "All Departments",
        "target_audience": ["All Students"],
        "priority": "High",
        "content": "Applications are invited from eligible students for the Government and Institutional Merit-cum-Means Scholarships for the academic year 2026-27. Eligibility criteria: Annual family income less than $40,000 per annum and minimum 75% marks in previous qualifying semester. Applicants must submit income certificates, caste certificates (if applicable), bank passbook copy, and fee receipt to the Financial Aid Desk by November 20, 2026.",
        "summary": "Merit-cum-Means scholarship for students with family income < $40,000 and >= 75% marks. Submit financial documents by November 20, 2026.",
        "action_required": True,
        "deadline": (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "Student Welfare & Financial Aid Cell",
        "tags": ["Scholarship", "FinancialAid", "Merit", "TuitionFee", "Grant"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 289,
        "bookmarks_count": 64,
        "is_active": True
    },
    {
        "id": "notif-005",
        "title": "Semester Tuition Fee Payment Extension & Late Fee Penalty Waiver",
        "category": "Fees & Finance",
        "department": "All Departments",
        "target_audience": ["All Students"],
        "priority": "Critical",
        "content": "In consideration of banking server downtimes reported last week, the Competent Authority has extended the deadline for payment of Semester Tuition and Laboratory Fees up to November 5, 2026 without any late fee penalty. After November 5, a mandatory surcharge of $50 per week will be levied. Payments can be completed online via UPI, NetBanking, or Credit Card through the University Accounts Gateway.",
        "summary": "Tuition fee payment deadline extended to November 5, 2026 without late fee penalty. Surcharge applied after this date.",
        "action_required": True,
        "deadline": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "Finance & Accounts Office",
        "tags": ["Fees", "Finance", "Deadline", "Waiver", "Accounts"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 612,
        "bookmarks_count": 47,
        "is_active": True
    },
    {
        "id": "notif-006",
        "title": "Mandatory Hostel Room Allotment & Biometric Registration for Odd Semester",
        "category": "Campus & Hostel",
        "department": "All Departments",
        "target_audience": ["Hostellers"],
        "priority": "High",
        "content": "All resident hostel students of Block A, B, and C must complete their biometric gate access registration and room inventory verification at the Chief Warden's Office between 4:00 PM and 7:00 PM on or before November 8, 2026. Failure to verify biometric credentials will result in automatic deactivation of RFID hostel turnstile gates. Quiet hours from 10:30 PM to 6:00 AM will be strictly enforced.",
        "summary": "Hostel residents must complete biometric access registration and room check at Warden's office by November 8, 2026.",
        "action_required": True,
        "deadline": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "Chief Hostel Warden",
        "tags": ["Hostel", "Biometric", "CampusLife", "Accommodation", "Residents"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 195,
        "bookmarks_count": 22,
        "is_active": True
    },
    {
        "id": "notif-007",
        "title": "Hands-On Workshop: Deep Learning with PyTorch & NVIDIA Jetson AI Certification",
        "category": "Events",
        "department": "Electronics",
        "target_audience": ["2nd Year", "3rd Year", "4th Year"],
        "priority": "Medium",
        "content": "Department of Electronics & Communication Engineering in association with NVIDIA Deep Learning Institute (DLI) is hosting a 2-day certified workshop on 'Edge AI and Computer Vision with PyTorch'. Participants will get hands-on access to Jetson Nano developer kits, GPU cloud instances, and an official NVIDIA certification upon successful project assessment. Seat limit: 60 students on first-come-first-serve basis.",
        "summary": "2-day NVIDIA certified workshop on Edge AI & PyTorch. Hands-on hardware kits provided. Limited to 60 seats.",
        "action_required": True,
        "deadline": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "ECE Department",
        "tags": ["AI", "NVIDIA", "Workshop", "Certification", "PyTorch", "Electronics"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 310,
        "bookmarks_count": 78,
        "is_active": True
    },
    {
        "id": "notif-008",
        "title": "Central Library Annual Book Return, Clearance & Digital Repository Access",
        "category": "Academics",
        "department": "All Departments",
        "target_audience": ["All Students", "Faculty"],
        "priority": "Low",
        "content": "The Central Library announces its semester book renewal drive. Students possessing books issued prior to September 1, 2026 must either get them physically renewed or return them to avoid an automated fine of $0.50/day. Additionally, all enrolled students have now been granted free 24/7 institutional remote access to IEEE Xplore, ACM Digital Library, and Springer Nature via campus email SSO.",
        "summary": "Renew or return issued library books by November 15 to avoid fines. IEEE & ACM digital library access now active via institutional SSO.",
        "action_required": False,
        "deadline": (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "Chief Librarian",
        "tags": ["Library", "Books", "IEEE", "Research", "Academics"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 180,
        "bookmarks_count": 19,
        "is_active": True
    },
    {
        "id": "notif-009",
        "title": "Annual Inter-Collegiate Athletics Meet 2026 - Selection Trials",
        "category": "Sports",
        "department": "All Departments",
        "target_audience": ["All Students"],
        "priority": "Low",
        "content": "Sports Council invites enthusiastic athletes for selection trials for the upcoming State University Sports Championship. Trials will be conducted for 100m sprint, 400m relay, long jump, badminton, and basketball on November 14, 2026 at the Main Stadium Ground at 7:00 AM sharp. Refreshments and official jersey kits will be provided to shortlisted players.",
        "summary": "Athletics selection trials on November 14, 2026 at 7:00 AM for Track & Field, Badminton, and Basketball at Main Stadium.",
        "action_required": False,
        "deadline": (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "Director of Physical Education",
        "tags": ["Sports", "Athletics", "Trials", "Basketball", "Fitness"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 145,
        "bookmarks_count": 11,
        "is_active": True
    },
    {
        "id": "notif-010",
        "title": "URGENT: Campus Network Upgrade & Central Server Scheduled Maintenance",
        "category": "General",
        "department": "All Departments",
        "target_audience": ["All Students", "Faculty"],
        "priority": "Critical",
        "content": "Central IT Infrastructure Services will perform scheduled core switch replacements and fiber optic cable upgrades this Saturday night between 11:00 PM and 5:00 AM. During this maintenance window, campus Wi-Fi, LMS portal, and local intranet services will experience intermittent connectivity drops. Crucial submissions should be saved locally ahead of time.",
        "summary": "Core network maintenance scheduled Saturday 11:00 PM - 5:00 AM. Intermittent Wi-Fi and LMS portal outages expected.",
        "action_required": False,
        "deadline": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "published_date": (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
        "posted_by": "IT Infrastructure Services",
        "tags": ["Urgent", "Maintenance", "WiFi", "Network", "IT"],
        "image_path": None,
        "extracted_from_ocr": False,
        "views_count": 480,
        "bookmarks_count": 31,
        "is_active": True
    }
]

DEFAULT_USERS = [
    {
        "user_id": "std-001",
        "name": "Alex Chen",
        "role": "student",
        "department": "Computer Science",
        "year": "3rd Year",
        "interests": ["Placements", "Hackathons", "AI", "Coding", "Scholarships"],
        "bookmarked_notice_ids": ["notif-002", "notif-003"],
        "history_notice_ids": ["notif-001", "notif-002", "notif-005"]
    },
    {
        "user_id": "std-002",
        "name": "Priya Sharma",
        "role": "student",
        "department": "Electronics",
        "year": "2nd Year",
        "interests": ["AI", "Workshop", "NVIDIA", "Hostel", "Exams"],
        "bookmarked_notice_ids": ["notif-007", "notif-006"],
        "history_notice_ids": ["notif-007", "notif-001"]
    },
    {
        "user_id": "faculty-001",
        "name": "Dr. Robert Vance",
        "role": "faculty",
        "department": "Computer Science",
        "year": "Faculty",
        "interests": ["Academics", "Research", "Examinations", "Grants"],
        "bookmarked_notice_ids": ["notif-001", "notif-008"],
        "history_notice_ids": ["notif-001", "notif-010"]
    }
]

class Database:
    def __init__(self):
        self._ensure_files()

    def _ensure_files(self):
        if not NOTICES_FILE.exists():
            with open(NOTICES_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SEED_NOTICES, f, indent=2)
        if not USERS_FILE.exists():
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_USERS, f, indent=2)

    def get_all_notices(self) -> List[dict]:
        with open(NOTICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_notice_by_id(self, notice_id: str) -> Optional[dict]:
        notices = self.get_all_notices()
        for n in notices:
            if n["id"] == notice_id:
                return n
        return None

    def save_notices(self, notices: List[dict]):
        with open(NOTICES_FILE, "w", encoding="utf-8") as f:
            json.dump(notices, f, indent=2)

    def create_notice(self, notice_dict: dict) -> dict:
        notices = self.get_all_notices()
        if not notice_dict.get("id"):
            notice_dict["id"] = f"notif-{uuid.uuid4().hex[:6]}"
        if not notice_dict.get("published_date"):
            notice_dict["published_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        if "views_count" not in notice_dict:
            notice_dict["views_count"] = 0
        if "bookmarks_count" not in notice_dict:
            notice_dict["bookmarks_count"] = 0
        if "is_active" not in notice_dict:
            notice_dict["is_active"] = True

        notices.insert(0, notice_dict)
        self.save_notices(notices)
        return notice_dict

    def update_notice(self, notice_id: str, updates: dict) -> Optional[dict]:
        notices = self.get_all_notices()
        for idx, n in enumerate(notices):
            if n["id"] == notice_id:
                notices[idx].update(updates)
                self.save_notices(notices)
                return notices[idx]
        return None

    def delete_notice(self, notice_id: str) -> bool:
        notices = self.get_all_notices()
        filtered = [n for n in notices if n["id"] != notice_id]
        if len(filtered) < len(notices):
            self.save_notices(filtered)
            return True
        return False

    def increment_views(self, notice_id: str):
        notices = self.get_all_notices()
        for n in notices:
            if n["id"] == notice_id:
                n["views_count"] = n.get("views_count", 0) + 1
                self.save_notices(notices)
                return n["views_count"]
        return 0

    def toggle_bookmark(self, user_id: str, notice_id: str) -> bool:
        users = self.get_all_users()
        user = next((u for u in users if u["user_id"] == user_id), None)
        if not user:
            # create user if not exists
            user = {
                "user_id": user_id,
                "name": "Default Student",
                "role": "student",
                "department": "Computer Science",
                "year": "3rd Year",
                "interests": ["Placements", "AI", "Exams"],
                "bookmarked_notice_ids": [],
                "history_notice_ids": []
            }
            users.append(user)

        is_bookmarked = False
        if notice_id in user.get("bookmarked_notice_ids", []):
            user["bookmarked_notice_ids"].remove(notice_id)
            is_bookmarked = False
        else:
            user.setdefault("bookmarked_notice_ids", []).append(notice_id)
            is_bookmarked = True

        self.save_users(users)

        # Update notice bookmark counter
        notices = self.get_all_notices()
        for n in notices:
            if n["id"] == notice_id:
                delta = 1 if is_bookmarked else -1
                n["bookmarks_count"] = max(0, n.get("bookmarks_count", 0) + delta)
                self.save_notices(notices)
                break

        return is_bookmarked

    def add_history(self, user_id: str, notice_id: str):
        users = self.get_all_users()
        for u in users:
            if u["user_id"] == user_id:
                history = u.setdefault("history_notice_ids", [])
                if notice_id in history:
                    history.remove(notice_id)
                history.insert(0, notice_id)
                if len(history) > 20:
                    u["history_notice_ids"] = history[:20]
                self.save_users(users)
                break

    def get_all_users(self) -> List[dict]:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_users(self, users: List[dict]):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)

    def get_user_profile(self, user_id: str) -> Optional[dict]:
        users = self.get_all_users()
        for u in users:
            if u["user_id"] == user_id:
                return u
        return None

db = Database()
