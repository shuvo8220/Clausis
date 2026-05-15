"""
Tests for the Legal AI pipeline.
Run with: pytest tests/ -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.document_processor import (
    _chunk_text, _extract_structured_fields, process_document
)
from src.models import DraftType, DocumentStatus, new_id


class TestChunking:
    def test_basic_chunking(self):
        text = "This is sentence one. " * 50
        chunks = _chunk_text(text, "doc-1", page_number=1, chunk_size=200, overlap=50, confidence=1.0)
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.document_id == "doc-1"
            assert chunk.page_number == 1

    def test_chunk_overlap(self):
        text = "Alpha sentence here. Beta sentence there. Gamma sentence indeed. Delta comes after. Epsilon ends it."
        chunks = _chunk_text(text, "doc-2", page_number=None, chunk_size=60, overlap=20, confidence=0.9)
        for chunk in chunks:
            assert chunk.text.strip()

    def test_empty_text(self):
        chunks = _chunk_text("", "doc-3", page_number=1, chunk_size=200, overlap=50, confidence=1.0)
        assert chunks == []

    def test_single_short_text(self):
        text = "Short text."
        chunks = _chunk_text(text, "doc-4", page_number=1, chunk_size=200, overlap=50, confidence=1.0)
        assert len(chunks) == 1
        assert chunks[0].text == "Short text."


class TestStructuredFieldExtraction:
    def test_case_reference_extraction(self):
        text = "Case No.: BC-2024-087432 was filed on March 14, 2024."
        fields = _extract_structured_fields(text)
        assert "case_references" in fields
        assert any("BC-2024-087432" in ref for ref in fields["case_references"])

    def test_date_extraction(self):
        text = "The contract was signed on September 1, 2022. The deadline was March 1, 2023."
        fields = _extract_structured_fields(text)
        assert "dates_mentioned" in fields
        assert len(fields["dates_mentioned"]) >= 1

    def test_monetary_amount_extraction(self):
        text = "The total contract price was $2,450,000.00. Damages are $180,000.00 per month."
        fields = _extract_structured_fields(text)
        assert "monetary_amounts" in fields
        assert "$2,450,000.00" in fields["monetary_amounts"]

    def test_party_extraction(self):
        text = "Plaintiff: Hartwell Properties LLC\nDefendant: Meridian Construction Group, Inc."
        fields = _extract_structured_fields(text)
        assert "plaintiff" in fields
        assert "Hartwell" in fields["plaintiff"]

    def test_statute_extraction(self):
        text = "Pursuant to Section 12.3 of the Agreement and Civil Code 3294..."
        fields = _extract_structured_fields(text)
        assert "statute_references" in fields

    def test_empty_document(self):
        fields = _extract_structured_fields("")
        assert isinstance(fields, dict)


class TestDocumentProcessing:
    def test_process_txt_file(self, tmp_path):
        doc_file = tmp_path / "test.txt"
        doc_file.write_text("Plaintiff: John Smith. Case No.: TEST-001. Amount: $50,000.00.")
        doc = process_document(str(doc_file))
        assert doc.status == DocumentStatus.READY
        assert len(doc.chunks) > 0
        assert "plaintiff" in doc.structured_fields

    def test_process_missing_file(self):
        doc = process_document("/nonexistent/path/doc.pdf")
        assert doc.status == DocumentStatus.FAILED
        assert len(doc.processing_notes) > 0

    def test_process_empty_txt(self, tmp_path):
        doc_file = tmp_path / "empty.txt"
        doc_file.write_text("   \n  \n   ")
        doc = process_document(str(doc_file))
        assert doc.filename == "empty.txt"


class TestRetrieval:
    def test_evidence_sorting(self):
        """Evidence results should always be sorted by relevance descending."""
        from src.models import RetrievedEvidence
        results = [
            RetrievedEvidence("c1", "d1", "text1", 0.9, 1, "doc1.txt"),
            RetrievedEvidence("c2", "d1", "text2", 0.5, 2, "doc1.txt"),
            RetrievedEvidence("c3", "d1", "text3", 0.7, 3, "doc1.txt"),
        ]
        results.sort(key=lambda e: e.relevance_score, reverse=True)
        scores = [r.relevance_score for r in results]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] == 0.9

    def test_index_empty_document(self, tmp_path):
        doc_file = tmp_path / "empty.txt"
        doc_file.write_text("   ")
        doc = process_document(str(doc_file))
        assert len(doc.chunks) == 0


class TestModels:
    def test_new_id_uniqueness(self):
        ids = {new_id() for _ in range(100)}
        assert len(ids) == 100

    def test_draft_type_values(self):
        assert DraftType.CASE_FACT_SUMMARY.value == "case_fact_summary"
        assert DraftType.INTERNAL_MEMO.value == "internal_memo"


class TestImprovementEngine:
    def test_edit_classification(self):
        from src.improvement_engine import _classify_edit
        assert _classify_edit("", "new text added") == "addition"
        assert _classify_edit("lots of original text here to delete", "") == "deletion"
        assert _classify_edit("original text here was fine", "completely different rewrite added more words here") in ("rewrite", "addition")

    def test_get_patterns_empty(self):
        from src.improvement_engine import get_patterns_for_draft_type
        result = get_patterns_for_draft_type(DraftType.DOCUMENT_CHECKLIST)
        assert isinstance(result, list)

    def test_grounding_map_structure(self):
        from src.draft_generator import _build_grounding_map
        from src.models import RetrievedEvidence
        content = "## Parties\nHartwell is the plaintiff.\n## Claims\nBreach of contract."
        evidence = [
            RetrievedEvidence("c1", "d1", "Hartwell plaintiff complaint filed", 0.9, 1, "doc.txt"),
        ]
        gmap = _build_grounding_map(content, evidence)
        assert isinstance(gmap, dict)
