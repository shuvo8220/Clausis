

from __future__ import annotations
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .config import settings
from .document_processor import process_document
from .retrieval import index_document, retrieve_evidence, get_indexed_document_ids, delete_document
from .draft_generator import generate_draft
from .improvement_engine import (
    capture_edit, extract_patterns_from_edits,
    get_patterns_for_draft_type, get_edit_count, get_all_patterns
)
from .models import DraftType, new_id
from .database.connection import get_db, init_db
from .repositories.document_repository import DocumentRepository

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Legal AI — Document Understanding & Grounded Drafting",
    description="Ingests messy legal documents, retrieves evidence, generates grounded drafts, and improves from operator edits.",
    version="2.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and other resources"""
    try:
        init_db()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

# In-memory draft store (TODO: move to database)
_draft_store: dict = {}
_doc_meta_store: dict = {}  # document_id -> {filename, structured_fields, page_count}


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class GenerateDraftRequest(BaseModel):
    document_ids: list[str]
    draft_type: DraftType = DraftType.CASE_FACT_SUMMARY
    additional_context: Optional[str] = None
    query_override: Optional[str] = None  # custom retrieval query


class EditRequest(BaseModel):
    original_text: str
    edited_text: str
    section_label: Optional[str] = None
    operator_note: Optional[str] = None


class ExtractPatternsRequest(BaseModel):
    draft_type: DraftType
    min_edits: int = 2


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "indexed_documents": len(get_indexed_document_ids())}


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, image, or text file. The system will:
    1. Extract text (with OCR fallback for scanned pages)
    2. Chunk and index the content
    3. Return structured metadata
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".tiff"}:
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    # Write to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        doc = process_document(tmp_path)
        # Store original filename
        doc.filename = file.filename

        if doc.status.value == "failed":
            raise HTTPException(422, f"Document processing failed: {doc.processing_notes}")

        n_indexed = index_document(doc)

        _doc_meta_store[doc.document_id] = {
            "document_id": doc.document_id,
            "filename": doc.filename,
            "structured_fields": doc.structured_fields,
            "page_count": doc.page_count,
            "chunk_count": n_indexed,
            "ocr_applied": doc.ocr_applied,
            "processing_notes": doc.processing_notes,
            "status": doc.status.value,
            "raw_text_preview": doc.raw_text[:500] if doc.raw_text else "",  # First 500 chars
            "text_length": len(doc.raw_text) if doc.raw_text else 0,
        }

        return _doc_meta_store[doc.document_id]
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.get("/documents")
def list_documents():
    """List all currently indexed documents."""
    indexed_ids = set(get_indexed_document_ids())
    return [
        meta for doc_id, meta in _doc_meta_store.items()
        if doc_id in indexed_ids
    ]


@app.delete("/documents/{document_id}")
def remove_document(document_id: str):
    deleted = delete_document(document_id)
    _doc_meta_store.pop(document_id, None)
    return {"document_id": document_id, "chunks_deleted": deleted}


@app.post("/drafts/generate")
def generate(req: GenerateDraftRequest):
    """
    Generate a grounded draft for the given documents.

    Steps:
    1. Build a retrieval query from the draft type + any override
    2. Retrieve relevant evidence chunks
    3. Inject learned operator patterns
    4. Generate draft with Claude
    5. Return draft + evidence + grounding map
    """
    if not req.document_ids:
        raise HTTPException(400, "At least one document_id is required")

    # Validate docs are indexed
    indexed = set(get_indexed_document_ids())
    missing = [d for d in req.document_ids if d not in indexed]
    if missing:
        raise HTTPException(404, f"Documents not found in index: {missing}")

    # Retrieval query
    query = req.query_override or _default_query(req.draft_type)

    evidence = retrieve_evidence(
        query=query,
        document_ids=req.document_ids,
        n_results=settings.max_retrieval_results,
    )

    if not evidence:
        raise HTTPException(422, "No evidence could be retrieved for these documents")

    # Gather structured fields from all docs
    combined_fields: dict = {}
    for doc_id in req.document_ids:
        meta = _doc_meta_store.get(doc_id, {})
        for k, v in meta.get("structured_fields", {}).items():
            if k not in combined_fields:
                combined_fields[k] = v
            elif isinstance(v, list):
                combined_fields[k] = list(set(combined_fields[k] + v))

    # Get learned patterns for this draft type
    patterns = get_patterns_for_draft_type(req.draft_type)

    try:
        draft = generate_draft(
            draft_type=req.draft_type,
            evidence=evidence,
            document_ids=req.document_ids,
            structured_fields=combined_fields,
            learned_patterns=patterns,
            additional_context=req.additional_context,
        )
    except ValueError as e:
        logger.error(f"LLM configuration error: {e}")
        raise HTTPException(500, f"LLM service configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"Draft generation failed: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate draft: {str(e)}")

    _draft_store[draft.draft_id] = draft

    return {
        "draft_id": draft.draft_id,
        "draft_type": draft.draft_type.value,
        "content": draft.content,
        "model_used": draft.model_used,
        "created_at": draft.created_at.isoformat(),
        "patterns_applied": patterns,
        "evidence": [
            {
                "chunk_id": e.chunk_id,
                "source_filename": e.source_filename,
                "page_number": e.page_number,
                "relevance_score": e.relevance_score,
                "text_preview": e.text[:200] + "..." if len(e.text) > 200 else e.text,
            }
            for e in evidence
        ],
        "grounding_map": draft.grounding_map,
    }


@app.get("/drafts/{draft_id}")
def get_draft(draft_id: str):
    draft = _draft_store.get(draft_id)
    if not draft:
        raise HTTPException(404, f"Draft {draft_id} not found")
    return {
        "draft_id": draft.draft_id,
        "draft_type": draft.draft_type.value,
        "content": draft.content,
        "created_at": draft.created_at.isoformat(),
        "grounding_map": draft.grounding_map,
    }


@app.post("/drafts/{draft_id}/edit")
def submit_edit(draft_id: str, req: EditRequest):
    """
    Submit an operator edit to a draft. The edit is stored and used
    to improve future drafts via pattern extraction.
    """
    draft = _draft_store.get(draft_id)
    if not draft:
        raise HTTPException(404, f"Draft {draft_id} not found")

    edit = capture_edit(
        draft=draft,
        original_text=req.original_text,
        edited_text=req.edited_text,
        section_label=req.section_label,
        operator_note=req.operator_note,
    )

    edit_count = get_edit_count(draft.draft_type)
    patterns_updated = False

    # Auto-extract patterns every 3 edits
    if edit_count > 0 and edit_count % 3 == 0:
        new_patterns = extract_patterns_from_edits(draft.draft_type, min_edits=2)
        patterns_updated = len(new_patterns) > 0

    return {
        "edit_id": edit.edit_id,
        "edit_type": edit.edit_type,
        "total_edits_for_type": edit_count,
        "patterns_updated": patterns_updated,
        "message": (
            "Patterns updated from your edits — future drafts will reflect these preferences."
            if patterns_updated
            else "Edit captured. Patterns will be updated after more edits accumulate."
        ),
    }


@app.post("/patterns/extract")
def trigger_pattern_extraction(req: ExtractPatternsRequest):
    """Manually trigger pattern extraction for a given draft type."""
    patterns = extract_patterns_from_edits(req.draft_type, min_edits=req.min_edits)
    return {
        "draft_type": req.draft_type.value,
        "patterns_extracted": len(patterns),
        "patterns": [
            {
                "description": p.description,
                "confidence": p.confidence,
                "example_before": p.example_before[:100],
                "example_after": p.example_after[:100],
            }
            for p in patterns
        ],
    }


@app.get("/patterns")
def list_patterns():
    """Return all stored learned patterns."""
    return get_all_patterns()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_DRAFT_TYPE_QUERIES = {
    DraftType.CASE_FACT_SUMMARY: "parties claims facts dates timeline dispute",
    DraftType.TITLE_REVIEW_SUMMARY: "title ownership property encumbrance lien",
    DraftType.NOTICE_SUMMARY: "notice deadline obligation compliance requirement",
    DraftType.DOCUMENT_CHECKLIST: "documents required missing checklist items",
    DraftType.INTERNAL_MEMO: "key facts findings issues recommendations summary",
}


def _default_query(draft_type: DraftType) -> str:
    return _DRAFT_TYPE_QUERIES.get(draft_type, "relevant facts and information")
