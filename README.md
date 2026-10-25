# AI-Powered Smart Notice Management & Recommendation System
### *NexusNotice AI — Smart Campus Intelligence Portal*

An intelligent, full-stack campus circular management system built with **FastAPI**, **Tailwind CSS**, and modern AI: **PaddleOCR**, **Sentence Transformers**, **FAISS**, **Google Gemini**, and **Anthropic Claude**.

---

## 🤖 5 Integrated AI Tools & Their Roles

| AI Tool | Architecture & Implementation | Primary Role in System |
| :--- | :--- | :--- |
| **PaddleOCR** | Deep Learning OCR with intelligent vision fallback | Scans uploaded physical circulars and photos. Automatically detects notice titles, dates, departments, deadlines, and urgency. |
| **Sentence Transformers** | 384-dimensional dense semantic embeddings (`all-MiniLM-L6-v2`) | Encodes notice titles, contents, tags, and user preferences into semantic vector representations. |
| **FAISS** | Fast similarity search index (`IndexFlatIP` cosine metric) | Sub-millisecond vector retrieval. Powers natural language semantic search (finding notices even with typos or descriptive queries) and vector recommendations. |
| **Google Gemini** | Google GenAI SDK (`gemini-3.8-flash` / `gemini-2.5-flash`) | Generates concise executive summaries, extracts key deadlines, and powers the interactive NoticeBot assistant. |
| **Anthropic Claude** | Anthropic SDK (`claude-3-5-sonnet`) | Dual-model assistant for official circular drafting, administrative tone refinement, and comparative reasoning. |

---

## 🌟 Key Features

1. **Scanned Notice Upload & OCR Form Auto-Fill**:
   - Drag-and-drop any circular image (JPG, PNG).
   - Includes 1-click sample test notices (`Exam Circular`, `Placement Drive`, `Hackathon Announcement`).
   - Automatically populates title, category, department, priority, and deadline.

2. **Dense Semantic Search**:
   - Search by concept or question: *"When are mid-term exam hall tickets available?"*, *"Google placement eligibility"*, *"Fee penalty deadline"*.
   - Instant search with category filter chips and quick search shortcuts.

3. **Personalized Hybrid Recommendations**:
   - Multimodal ranking combining semantic interest vectors, department/year eligibility, and deadline urgency:
     $$\text{Score} = 0.50 \cdot S_{\text{vector}} + 0.30 \cdot S_{\text{audience}} + 0.20 \cdot S_{\text{urgency}}$$
   - Live persona switcher to test recommendations for students across different branches and years.

4. **NoticeBot AI Assistant**:
   - Click **Read & Chat** on any notice to ask questions about deadlines, eligibility criteria, or rules.
   - Live assistant model toggle between Google Gemini and Anthropic Claude.
   - Built-in intelligent fallback agent ensures immediate offline functionality without API keys.

5. **Official Circular Publishing Studio**:
   - Admin & faculty circular drafting tool powered by Gemini/Claude.
   - Input brief bullet points to generate an official circular complete with reference numbers and guidelines.

6. **Interactive Topic Clustering & Analytics**:
   - 2D scatter plot visualization of notice semantic distribution and topic clusters.
   - Read counters, bookmark tracking, and category distribution breakdown.

7. **Student Productivity Utilities**:
   - **Listen Audio**: Text-to-Speech (TTS) audio read-out.
   - **Add to Calendar**: One-click `.ics` deadline calendar export.
   - **Personal Bookmarks**: Save critical circulars for quick reference.

---

## 🚀 Team Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/smart-notice-system.git
cd smart-notice-system
```

### 2. Set Up a Python Virtual Environment

**On Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application

**Option A (Windows 1-Click):**
Double-click `start_server.bat`

**Option B (Command Line):**
```bash
python run.py
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔑 Configuring API Keys (Optional)

The application includes an **Intelligent Offline Fallback Agent**, meaning all features (FAISS search, OCR processing, hybrid recommendations, and NoticeBot Q&A) work **100% out of the box** even without API keys!

To enable live Google Gemini & Anthropic Claude API inference:
1. Open the portal at `http://127.0.0.1:8000`.
2. Click the **Sliders / Settings** icon in the top right header.
3. Paste your `GEMINI_API_KEY` and/or `ANTHROPIC_API_KEY`.
4. Click **Save Settings** — live inference activates immediately without restarting!

*(Alternatively, copy `.env.example` to `.env` and enter your keys there)*.

---

## 📁 Repository Structure

```text
smart-notice-system/
├── backend/
│   ├── app.py                     # FastAPI application & REST endpoints
│   ├── config.py                  # Configurations & settings manager
│   ├── database.py                # JSON store & user profile database
│   ├── models.py                  # Pydantic data schemas
│   └── services/
│       ├── ocr_service.py         # PaddleOCR + smart vision extractor
│       ├── embedding_service.py   # Sentence Transformers (all-MiniLM-L6-v2)
│       ├── vector_search.py       # FAISS vector similarity search
│       ├── recommendation_service.py # Hybrid recommendation engine
│       └── llm_service.py         # Dual Gemini & Claude AI integration
├── frontend/
│   ├── index.html                 # Clean, modern campus SPA dashboard
│   ├── css/style.css              # Custom styles & pulse animations
│   └── js/app.js                  # Frontend state, search & NoticeBot
├── sample_data/
│   ├── notices.json               # Seed catalog of campus circulars
│   ├── users.json                 # Persona profiles (CSE, ECE, Mech, Faculty)
│   └── sample_notice_images/      # Pre-rendered circulars for OCR testing
├── uploads/                       # Storage for uploaded circular scans
├── run.py                         # Application entrypoint
├── start_server.bat               # Windows one-click launcher
├── requirements.txt               # Python package dependencies
├── settings.example.json          # Template configuration
├── .env.example                   # Environment variable template
├── .gitignore                     # Git exclusion rules (protects API keys)
└── README.md                      # Documentation
```

---

## 🛡️ License & Contributing

Built for modern academic institutions and campus notice management. Contributions and pull requests are welcome!
