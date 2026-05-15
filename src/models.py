from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DraftType(str, Enum):
    CASE_FACT_SUMMARY = "case_fact_summary"
    TITLE_REVIEW_SUMMARY = "title_review_summary"
    NOTICE_SUMMARY = "notice_summary"
    DOCUMENT_CHECKLIST = "document_checklist"
    INTERNAL_MEMO = "internal_memo"


@dataclass
class ExtractedChunk:
    """A single text chunk extracted from a document."""
    chunk_id: str
    document_id: str
    text: str
    page_number: Optional[int]
    chunk_index: int
    confidence: float = 1.0          # OCR confidence if applicable
    metadata: dict = field(default_factory=dict)


@dataclass
class ProcessedDocument:
    """Full result of document processing."""
    document_id: str
    filename: str
    status: DocumentStatus
    raw_text: str
    chunks: list[ExtractedChunk]
    structured_fields: dict            # extracted entities: dates, parties, case refs
    page_count: int
    ocr_applied: bool
    processing_notes: list[str]        # warnings about quality, partial pages, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RetrievedEvidence:
    """A chunk surfaced by retrieval, with its relevance score."""
    chunk_id: str
    document_id: str
    text: str
    relevance_score: float
    page_number: Optional[int]
    source_filename: str


@dataclass
class GeneratedDraft:
    """A complete generated draft with grounding metadata."""
    draft_id: str
    draft_type: DraftType
    document_ids: list[str]
    content: str
    evidence_used: list[RetrievedEvidence]
    grounding_map: dict                # section_label -> [chunk_ids]
    model_used: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OperatorEdit:
    """A single edit made by an operator to a draft."""
    edit_id: str
    draft_id: str
    original_text: str
    edited_text: str
    edit_type: str                     # addition | deletion | rewrite | restructure
    section_label: Optional[str]
    operator_note: Optional[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LearnedPattern:
    """A reusable pattern extracted from a set of operator edits."""
    pattern_id: str
    draft_type: DraftType
    description: str                   # human-readable instruction
    example_before: str
    example_after: str
    confidence: float
    source_edit_ids: list[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


def new_id() -> str:
    return str(uuid.uuid4())
