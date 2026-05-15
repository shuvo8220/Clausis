"""
Database Models using SQLAlchemy
---------------------------------
Proper persistence layer replacing in-memory storage
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class DocumentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DraftTypeEnum(str, enum.Enum):
    CASE_FACT_SUMMARY = "case_fact_summary"
    TITLE_REVIEW_SUMMARY = "title_review_summary"
    NOTICE_SUMMARY = "notice_summary"
    DOCUMENT_CHECKLIST = "document_checklist"
    INTERNAL_MEMO = "internal_memo"


class Document(Base):
    """Processed document record"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    status = Column(SQLEnum(DocumentStatusEnum), nullable=False)
    raw_text = Column(Text)
    structured_fields = Column(JSON)
    page_count = Column(Integer, default=0)
    ocr_applied = Column(Boolean, default=False)
    processing_notes = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    drafts = relationship("Draft", back_populates="documents", secondary="draft_documents")


class Draft(Base):
    """Generated draft record"""
    __tablename__ = "drafts"
    
    id = Column(String, primary_key=True)
    draft_type = Column(SQLEnum(DraftTypeEnum), nullable=False)
    content = Column(Text, nullable=False)
    grounding_map = Column(JSON)
    model_used = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="drafts", secondary="draft_documents")
    edits = relationship("OperatorEdit", back_populates="draft")


class DraftDocument(Base):
    """Many-to-many relationship between drafts and documents"""
    __tablename__ = "draft_documents"
    
    draft_id = Column(String, ForeignKey("drafts.id"), primary_key=True)
    document_id = Column(String, ForeignKey("documents.id"), primary_key=True)


class OperatorEdit(Base):
    """Operator edit to a draft"""
    __tablename__ = "operator_edits"
    
    id = Column(String, primary_key=True)
    draft_id = Column(String, ForeignKey("drafts.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    edited_text = Column(Text, nullable=False)
    edit_type = Column(String)  # addition, deletion, rewrite, restructure
    section_label = Column(String)
    operator_note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    draft = relationship("Draft", back_populates="edits")


class LearnedPattern(Base):
    """Learned improvement pattern"""
    __tablename__ = "learned_patterns"
    
    id = Column(String, primary_key=True)
    draft_type = Column(SQLEnum(DraftTypeEnum), nullable=False)
    description = Column(Text, nullable=False)
    example_before = Column(Text)
    example_after = Column(Text)
    confidence = Column(Float, default=0.5)
    source_edit_ids = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
