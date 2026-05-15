
from __future__ import annotations
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from .models import (
    DraftType, GeneratedDraft, LearnedPattern, OperatorEdit, new_id
)
from .config import settings
from .services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

_EDITS_FILE = Path(settings.outputs_path) / "operator_edits.json"
_PATTERNS_FILE = Path(settings.outputs_path) / "learned_patterns.json"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return []
    return []


def _save_json(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# Edit capture
# ---------------------------------------------------------------------------

def _classify_edit(original: str, edited: str) -> str:
    """Simple heuristic to classify edit type."""
    orig_words = len(original.split())
    edit_words = len(edited.split())

    if not original.strip():
        return "addition"
    if not edited.strip():
        return "deletion"
    if edit_words > orig_words * 1.3:
        return "addition"
    if edit_words < orig_words * 0.7:
        return "deletion"
    return "rewrite"


def capture_edit(
    draft: GeneratedDraft,
    original_text: str,
    edited_text: str,
    section_label: Optional[str] = None,
    operator_note: Optional[str] = None,
) -> OperatorEdit:
    """
    Record a single operator edit.
    Call this whenever an operator modifies any part of a generated draft.
    """
    edit_type = _classify_edit(original_text, edited_text)

    edit = OperatorEdit(
        edit_id=new_id(),
        draft_id=draft.draft_id,
        original_text=original_text,
        edited_text=edited_text,
        edit_type=edit_type,
        section_label=section_label,
        operator_note=operator_note,
    )

    edits = _load_json(_EDITS_FILE)
    edits.append({
        "edit_id": edit.edit_id,
        "draft_id": edit.draft_id,
        "draft_type": draft.draft_type.value,
        "original_text": edit.original_text,
        "edited_text": edit.edited_text,
        "edit_type": edit.edit_type,
        "section_label": edit.section_label,
        "operator_note": edit.operator_note,
        "created_at": edit.created_at.isoformat(),
    })
    _save_json(_EDITS_FILE, edits)

    logger.info(f"Captured {edit_type} edit for draft {draft.draft_id[:8]}")
    return edit


# ---------------------------------------------------------------------------
# Pattern extraction
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM_PROMPT = """
You are an AI system analyst. You will be given a set of edits that a human operator
made to AI-generated legal draft documents. Your job is to extract generalizable
improvement patterns from these edits.

For each pattern you find, respond with a JSON array of objects with these fields:
- "description": a clear, actionable instruction for the AI to follow in future drafts
  (written as a direct instruction, e.g. "Always include the case number in the header")
- "example_before": a short representative excerpt of the original text
- "example_after": what the operator changed it to
- "confidence": 0.0 to 1.0 based on how consistently this pattern appears
- "applies_to": brief description of when this pattern applies

Rules:
- Only extract patterns that appear in at least 2 edits OR are clearly significant
- Be specific — "use active voice" is not specific enough; "rewrite passive constructions
  in the Parties section to active voice" is
- Do NOT invent patterns not supported by the edits
- Return ONLY a valid JSON array, no other text
"""


def extract_patterns_from_edits(
    draft_type: DraftType,
    min_edits: int = 2,
) -> list[LearnedPattern]:
    """
    Analyze stored edits for a given draft type and extract reusable patterns.
    Called after enough edits have accumulated (min_edits threshold).
    """
    all_edits = _load_json(_EDITS_FILE)
    relevant = [e for e in all_edits if e["draft_type"] == draft_type.value]

    if len(relevant) < min_edits:
        logger.info(f"Only {len(relevant)} edits for {draft_type.value} — skipping pattern extraction (need {min_edits})")
        return []

    logger.info(f"Extracting patterns from {len(relevant)} edits for {draft_type.value}")

    # Format edits for the model
    edit_text_parts = []
    for i, e in enumerate(relevant[-20:], 1):  # cap at last 20 edits
        part = (
            f"Edit {i} (type: {e['edit_type']})"
            + (f", section: {e['section_label']}" if e.get("section_label") else "")
            + (f", note: {e['operator_note']}" if e.get("operator_note") else "")
            + f"\nBEFORE: {e['original_text'][:300]}"
            + f"\nAFTER:  {e['edited_text'][:300]}"
        )
        edit_text_parts.append(part)

    edit_block = "\n\n---\n\n".join(edit_text_parts)
    user_message = (
        f"Draft type: {draft_type.value}\n\n"
        f"Here are the operator edits:\n\n{edit_block}\n\n"
        "Extract generalizable improvement patterns from these edits."
    )

    llm_service = get_llm_service()
    response = llm_service.generate(
        system_prompt=_EXTRACTION_SYSTEM_PROMPT,
        user_message=user_message,
        temperature=0.0,
        max_tokens=1500,
    )

    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pattern JSON: {e}\nRaw: {raw[:200]}")
        return []

    edit_ids = [e["edit_id"] for e in relevant]
    patterns = []
    for item in extracted:
        pattern = LearnedPattern(
            pattern_id=new_id(),
            draft_type=draft_type,
            description=item.get("description", ""),
            example_before=item.get("example_before", ""),
            example_after=item.get("example_after", ""),
            confidence=float(item.get("confidence", 0.5)),
            source_edit_ids=edit_ids,
        )
        patterns.append(pattern)

    # Persist patterns
    existing = _load_json(_PATTERNS_FILE)
    # Remove old patterns for this draft type (replace with fresh extraction)
    existing = [p for p in existing if p.get("draft_type") != draft_type.value]
    for p in patterns:
        existing.append({
            "pattern_id": p.pattern_id,
            "draft_type": p.draft_type.value,
            "description": p.description,
            "example_before": p.example_before,
            "example_after": p.example_after,
            "confidence": p.confidence,
            "source_edit_ids": p.source_edit_ids,
            "created_at": p.created_at.isoformat(),
        })
    _save_json(_PATTERNS_FILE, existing)

    logger.info(f"Extracted and saved {len(patterns)} patterns for {draft_type.value}")
    return patterns


def get_patterns_for_draft_type(draft_type: DraftType) -> list[str]:
    """
    Return the current set of learned pattern descriptions for a draft type.
    These are injected into the draft generator as additional instructions.
    Only returns patterns with confidence >= 0.5.
    """
    all_patterns = _load_json(_PATTERNS_FILE)
    relevant = [
        p for p in all_patterns
        if p.get("draft_type") == draft_type.value
        and p.get("confidence", 0) >= 0.5
    ]
    # Sort by confidence descending, cap at 5 to avoid prompt bloat
    relevant.sort(key=lambda p: p.get("confidence", 0), reverse=True)
    return [p["description"] for p in relevant[:5]]


def get_edit_count(draft_type: Optional[DraftType] = None) -> int:
    """Return total stored edits, optionally filtered by draft type."""
    all_edits = _load_json(_EDITS_FILE)
    if draft_type:
        return sum(1 for e in all_edits if e.get("draft_type") == draft_type.value)
    return len(all_edits)


def get_all_patterns() -> list[dict]:
    """Return all stored patterns (for inspection/debugging)."""
    return _load_json(_PATTERNS_FILE)
