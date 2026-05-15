# Legal AI — Document Understanding & Grounded Drafting

An industry-level AI pipeline for processing messy legal documents, extracting structured content, retrieving relevant evidence, generating grounded drafts, and continuously improving from operator edits.

## 🚀 Key Features

- **Multi-format Document Processing**: PDF, TXT, images with OCR fallback
- **Grounded RAG Pipeline**: Evidence-based generation with full traceability
- **Continuous Improvement**: Learns from operator edits to improve future drafts
- **Pluggable LLM Support**: OpenAI GPT-4 or Groq Llama 3.3
- **LangGraph Workflows**: Orchestrated multi-step processes
- **SOLID Architecture**: Industry-standard design patterns
- **React Frontend**: Modern, responsive UI
- **Production-Ready**: PostgreSQL, Docker, comprehensive testing

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [API Documentation](#api-documentation)
- [Frontend Setup](#frontend-setup)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)

---

## 🎯 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- PostgreSQL (or use SQLite for development)
- **Tesseract OCR** (for image/scanned document processing)
- OpenAI API key or Groq API key

### Installing Tesseract OCR

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run `tesseract-ocr-w64-setup-5.x.x.exe`
3. Add to PATH: `C:\Program Files\Tesseract-OCR`
4. Verify: `tesseract --version`

**For Bengali/Bangla Language Support:**
```bash
# Run the helper script (as Administrator)
install_bangla_ocr.bat
```

Or manually:
1. Download: https://github.com/tesseract-ocr/tessdata_best/raw/main/ben.traineddata
2. Copy to: `C:\Program Files\Tesseract-OCR\tessdata\ben.traineddata`
3. Restart backend

**Or with Chocolatey:**
```bash
choco install tesseract
# For Bengali support:
# Download ben.traineddata and copy to tessdata folder
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # For additional languages including Bengali
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-ben  # For Bengali support
```

**Note:** Tesseract is optional. Without it, you can still process PDF files with native text, but image files (.jpg, .png, .tiff) and scanned PDFs will not work.

### Backend Setup

```bash
# 1. Clone and navigate
git clone <your-repo>
cd legal_ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your API keys

# 5. Initialize database
python -c "from src.database.connection import init_db; init_db()"

# 6. Run the API server
python main.py
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env
# Edit if needed (default: http://localhost:8000)

# 4. Start development server
npm run dev
# Frontend available at http://localhost:3000
```

### Docker Setup (Recommended)

```bash
# Build and run everything with Docker Compose
docker-compose up --build

# Services:
# - API: http://localhost:8000
# - Frontend: http://localhost:3000
# - PostgreSQL: localhost:5432
```

---

## 🏗️ Architecture

This project follows **SOLID principles** and industry-standard design patterns. See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                        │
│              (JavaScript + TailwindCSS)                 │
└──────────────────┬──────────────────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                       │
│                    (Python 3.10+)                       │
└──────────────────┬──────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌──────▼──────┐  ┌───▼────────┐
│ LangGraph│  │ LLM Service │  │ Repository │
│ Workflows│  │ (Pluggable) │  │  Pattern   │
└──────────┘  └─────────────┘  └────────────┘
    │              │              │
┌───▼────────────────────────────▼────────────┐
│         PostgreSQL + ChromaDB               │
└─────────────────────────────────────────────┘
```

### Key Components

1. **LLM Service** - Abstraction layer supporting OpenAI/Groq
2. **LangGraph Workflows** - Orchestrates complex pipelines
3. **Repository Pattern** - Clean data access layer
4. **Vector Store** - ChromaDB for semantic search
5. **Improvement Engine** - Learns from operator edits

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangGraph** - Workflow orchestration
- **OpenAI/Groq** - LLM providers
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database
- **ChromaDB** - Vector database
- **PyMuPDF + Tesseract** - Document processing
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Axios** - HTTP client
- **React Router** - Navigation
- **Lucide React** - Icons

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **pytest** - Testing framework

---

## 📚 API Documentation

### Document Endpoints

#### Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data

file: <binary>
```

#### List Documents
```http
GET /documents
```

#### Delete Document
```http
DELETE /documents/{document_id}
```

### Draft Endpoints

#### Generate Draft
```http
POST /drafts/generate
Content-Type: application/json

{
  "document_ids": ["doc-id-1", "doc-id-2"],
  "draft_type": "case_fact_summary",
  "additional_context": "Focus on damages",
  "query_override": "custom retrieval query"
}
```

#### Get Draft
```http
GET /drafts/{draft_id}
```

#### Submit Edit
```http
POST /drafts/{draft_id}/edit
Content-Type: application/json

{
  "original_text": "Original section text",
  "edited_text": "Edited section text",
  "section_label": "Parties",
  "operator_note": "Always include party roles"
}
```

### Pattern Endpoints

#### List Patterns
```http
GET /patterns
```

#### Extract Patterns
```http
POST /patterns/extract
Content-Type: application/json

{
  "draft_type": "case_fact_summary",
  "min_edits": 2
}
```

### Health Check
```http
GET /health
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# LLM Provider (choose one)
LLM_PROVIDER=groq  # or "openai"
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# Models
OPENAI_MODEL=gpt-4o
GROQ_MODEL=llama-3.3-70b-versatile

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/legal_ai
# Or for SQLite: DATABASE_URL=sqlite:///./data/legal_ai.db

# Paths
CHROMA_DB_PATH=./data/chroma_db
OUTPUTS_PATH=./data/outputs

# Server
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# CORS (for frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Draft Types

- `case_fact_summary` - Parties, claims, dates, damages
- `title_review_summary` - Property, ownership, encumbrances
- `notice_summary` - Notice type, deadlines, obligations
- `document_checklist` - Present/missing document analysis
- `internal_memo` - Partner-facing memo with findings

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_pipeline.py -v
```

---

## 🚢 Deployment

### Docker Production Deployment

```bash
# Build production image
docker build -t legal-ai:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

1. Set up PostgreSQL database
2. Configure environment variables
3. Install dependencies: `pip install -r requirements.txt`
4. Initialize database: `python -c "from src.database.connection import init_db; init_db()"`
5. Run with gunicorn: `gunicorn src.api:app -w 4 -k uvicorn.workers.UvicornWorker`

---

## 📖 Usage Examples

### 1. Upload and Process Document

```python
import requests

# Upload document
with open('contract.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/documents/upload',
        files={'file': f}
    )
doc = response.json()
print(f"Document ID: {doc['document_id']}")
```

### 2. Generate Draft

```python
# Generate case fact summary
response = requests.post(
    'http://localhost:8000/drafts/generate',
    json={
        'document_ids': [doc['document_id']],
        'draft_type': 'case_fact_summary'
    }
)
draft = response.json()
print(draft['content'])
```

### 3. Submit Operator Edit

```python
# Submit edit to improve future drafts
response = requests.post(
    f'http://localhost:8000/drafts/{draft["draft_id"]}/edit',
    json={
        'original_text': 'Plaintiff: John Smith',
        'edited_text': 'Plaintiff: John Smith (represented by Smith & Associates)',
        'section_label': 'Parties',
        'operator_note': 'Always include legal representation'
    }
)
```

---

## 🎨 Design Principles

### SOLID Principles

1. **Single Responsibility** - Each module has one clear purpose
2. **Open/Closed** - Easy to extend without modifying existing code
3. **Liskov Substitution** - Implementations are interchangeable
4. **Interface Segregation** - Clean, minimal interfaces
5. **Dependency Inversion** - Depend on abstractions, not concretions

### Design Patterns

- **Strategy Pattern** - LLM service implementations
- **Factory Pattern** - LLM service creation
- **Repository Pattern** - Data access abstraction
- **Singleton Pattern** - Service instances
- **State Machine** - LangGraph workflows
- **Pipeline Pattern** - Document processing

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Built for Pearson Specter Litt AI Engineering Assessment
- Uses OpenAI GPT-4 and Groq Llama 3.3
- Powered by LangGraph, FastAPI, and React

---

## 📧 Contact

For questions or support, please contact the development team.

---

## 🗺️ Roadmap

- [ ] Real-time collaboration with WebSockets
- [ ] Advanced analytics dashboard
- [ ] Multi-language document support
- [ ] Export to PDF/DOCX
- [ ] User authentication and permissions
- [ ] Audit trail and version control
- [ ] Template system for custom drafts
- [ ] Webhook integrations
