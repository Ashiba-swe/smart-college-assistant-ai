# Smart College Assistant AI

> **An Intelligent and Adaptive College Information System Powered by Retrieval-Augmented Generation (RAG).**

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Backend-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![Vector DB](https://img.shields.io/badge/Vector%20DB-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![AI LLM](https://img.shields.io/badge/AI%20Model-Google%20Gemini%202.5%20Flash-teal.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests Status](https://img.shields.io/badge/Tests-23%20Passed-brightgreen.svg)](#automated-testing)

---

## 🏛️ Project Overview

**Smart College Assistant AI** is an enterprise-grade academic information retrieval platform built for engineering colleges and universities. Traditional LLMs frequently hallucinate policies, dates, and administrative regulations. This system solves that problem by implementing a strict **Retrieval-Augmented Generation (RAG)** pipeline backed by **ChromaDB** and **PyMuPDF**, grounding every student answer in official, approved institutional documents with page-level citations.

---

## 🌟 Key Features

### 1. Real RAG & Anti-Hallucination Pipeline
- **Document Extractors:** Multi-format ingestion supporting `.pdf` (PyMuPDF / fitz), `.docx` (python-docx), and `.txt`.
- **Semantic Text Chunking:** Overlapping text chunker (600 characters / 100 char overlap) preserving rich metadata (Document Title, Page, File, Category, Department).
- **Persistent Vector Indexing:** ChromaDB persistent storage powered by ONNX `all-MiniLM-L6-v2` embeddings.
- **Strict Grounding Prompts:** Enforces zero-hallucination. When an answer is absent from official college records, the assistant explicitly states it cannot find official information and directs the user to the administration.
- **Prompt Injection Defense:** Neutralizes malicious adversarial prompts embedded in untrusted documents.
- **Verifiable Source Citations:** Every response includes clickable source badges displaying document titles, exact page numbers, similarity scores, and excerpts.

### 2. Adaptive Knowledge Feedback Loop
- **Student Reporting:** Students can flag answers as `Incorrect`, `Missing Information`, `Outdated`, or `Unhelpful`.
- **Admin Review Queue:** Administrators review reported questions and formulate verified corrections.
- **Instant Knowledge Vectorization:** Approved corrections are instantly converted into verified FAQs and indexed into ChromaDB—improving future answers without retraining the foundation LLM.

### 3. Role-Based Access Control (RBAC)
- **Student Role:** Ask questions, browse verified FAQs, inspect citations, review conversation history, share feedback.
- **Faculty Role:** Submit departmental circulars and laboratory manuals for approval, submit verified FAQs, track submission statuses.
- **Administrator Role:** Approve/reject documents, manage user accounts and roles, direct document uploads, inspect audit logs, trigger full vector re-indexing, view RAG evaluation metrics.

---

## 🏗️ System Architecture

```
Student / User Question
          │
          ▼
Text Cleaning & Normalization
          │
          ▼
Vector Search in ChromaDB (Persistent Index)
          │
          ├──> Top-k Verified Context Chunks
          ├──> Page & File Citations
          │
          ▼
Prompt Assembly (Strict Grounding Rules + Injection Filter)
          │
          ▼
Google Gemini LLM (gemini-2.5-flash)
          │
          ▼
Grounded AI Response + Verifiable Citations
          │
          ▼
Adaptive Feedback Loop ──> Admin Verification ──> Vector Indexing
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla ES6+), Bootstrap 5.3, Bootstrap Icons |
| **Backend** | Python Flask 3.1, Jinja2, Werkzeug Security |
| **Relational Database** | PostgreSQL (Production) / SQLite (Local Development) via SQLAlchemy 2.0 |
| **Vector Database** | ChromaDB Persistent Client |
| **Embeddings** | all-MiniLM-L6-v2 ONNX Model (Local, high speed) |
| **LLM Provider** | Google Gemini API (`gemini-2.5-flash` or configurable via `.env`) |
| **Document Processing** | PyMuPDF (fitz) for PDF, python-docx for DOCX, ReportLab for generation |
| **Authentication** | Flask-Login with secure session cookies and password hashing |
| **Deployment** | Render, Gunicorn, Docker, Cloudflare |

---

## 📁 Repository Structure

```
smart-college-assistant-ai/
├── app/
│   ├── __init__.py                # App factory & blueprint registration
│   ├── config.py                  # Environment configuration classes
│   ├── models.py                  # SQLAlchemy ORM database models
│   ├── auth/                      # Authentication & RBAC blueprints
│   ├── main/                      # Public routes (Landing, Sources, FAQs, Health)
│   ├── chat/                      # Interactive RAG chat endpoints
│   ├── student/                   # Student dashboard & profile
│   ├── faculty/                   # Faculty submissions
│   ├── admin/                     # Admin control console & approvals
│   ├── rag/                       # RAG core (extractor, chunker, vector_store, llm, engine)
│   ├── static/                    # CSS SaaS styling, JS engines, SVG icons
│   └── templates/                 # 26 Responsive Jinja2 templates
├── data/
│   ├── sample_docs/               # 8 demo PDFs, 2 DOCX files, 1 TXT document
│   └── uploads/                   # Uploaded documents directory
├── scripts/
│   ├── generate_sample_docs.py    # ReportLab script generating demo college PDFs
│   ├── seed_database.py           # DB initialization & ChromaDB indexing
│   └── evaluate_rag.py            # 21-question automated RAG benchmark
├── tests/                         # Pytest automated test suite (23 passing tests)
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git ignore rules
├── Procfile                       # Production web process definition
├── render.yaml                    # Render deployment manifest
├── Dockerfile                     # Container deployment definition
├── requirements.txt               # Pinned Python package dependencies
├── run.py                         # Application local runner
└── README.md                      # Comprehensive documentation
```

---

## 🚀 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Ashiba-swe/smart-college-assistant-ai.git
cd smart-college-assistant-ai
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to include your secrets and optional Google Gemini API key:
```ini
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-here
PORT=5000

# Optional: Add your Google Gemini API key for live generative synthesis
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
```
*(Note: If no API key is provided, the system seamlessly operates in direct grounded synthesis mode, extracting verified document text and citations from ChromaDB without external API calls.)*

### 5. Generate Sample Documents & Seed Knowledge Base
```bash
# Generate the 8 official PDF handbooks, 2 DOCX manuals, and 1 TXT contact guide
python scripts/generate_sample_docs.py

# Seed database and index all chunks into ChromaDB
python scripts/seed_database.py
```

### 6. Run the Application
```bash
python run.py
```
Open your browser and navigate to: **`http://localhost:5000`**

---

## 🔑 Default Demo Accounts

The database seeding script creates three demo accounts:

| Role | Username | Password | Purpose |
|---|---|---|---|
| **Administrator** | `admin` | `AdminSecure@2026` | Master console, document approvals, user management |
| **Faculty** | `faculty_cse` | `FacultySecure@2026` | Department notice uploads, FAQ submissions |
| **Student** | `student_ashiba` | `StudentSecure@2026` | RAG chat assistant, source citations, reporting |

---

## 🧪 Automated Testing

The project includes an automated test suite verifying models, authentication, security boundaries, document extraction, ChromaDB vector indexing, and the feedback loop.

Run the test suite with `pytest`:
```bash
python -m pytest tests/ -v
```

### Test Suite Coverage:
- `tests/test_auth.py`: Registration, password hashing, role enforcement, login/logout.
- `tests/test_document_processor.py`: Multi-format PDF, DOCX, TXT extraction, text chunker with metadata.
- `tests/test_vector_store.py`: ChromaDB CRUD, cosine similarity search, chunk deletion.
- `tests/test_rag_pipeline.py`: Grounded context injection, source citations, no-answer detection, prompt injection defense.
- `tests/test_feedback_loop.py`: Student report submission, admin conversion into verified FAQ, instant re-indexing.
- `tests/test_security.py`: Role boundary protection, CSRF, file extension validation.
- `tests/test_api_endpoints.py`: `/health`, `/api/chat/send`, `/api/chat/conversations`.

### RAG Benchmark Evaluation:
To execute the 21-question automated college accuracy benchmark:
```bash
python scripts/evaluate_rag.py
```
- **Retrieval Accuracy:** 100% (21/21 questions correctly matched)
- **Grounding Fidelity:** >85%
- **No-Answer Refusal Accuracy:** 100% (Accurately refuses unanswerable/out-of-scope queries without hallucination)

---

## 🌐 Live Deployment Guide (Render)

This project is pre-configured for one-click deployment on **Render**:

1. Fork or push this repository to your GitHub account (`Ashiba-swe/smart-college-assistant-ai`).
2. Log into [Render](https://dashboard.render.com/).
3. Click **New +** -> **Blueprint**.
4. Select your `smart-college-assistant-ai` repository. Render will automatically detect `render.yaml`.
5. Render will provision:
   - Python Web Service with persistent disk for ChromaDB vector embeddings (`/data/chroma_db`).
   - Managed PostgreSQL database service (`smart-college-db`).
6. Set the `GEMINI_API_KEY` environment variable in the Render dashboard.
7. Click **Deploy**. The health check endpoint at `/health` monitors application availability.

---

## 📄 License

This project is developed for final-year engineering evaluation and released under the MIT License.
