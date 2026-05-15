
from __future__ import annotations
import json
import logging
from typing import Optional

from .models import (
    DraftType, GeneratedDraft, RetrievedEvidence, new_id
)
from .config import settings
from .services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Draft-type-specific prompts
# ---------------------------------------------------------------------------

_DRAFT_PROMPTS: dict[DraftType, str] = {
    DraftType.CASE_FACT_SUMMARY: """
You are a legal analyst at a law firm preparing an internal case fact summary.
Using ONLY the provided evidence passages, write a structured fact summary with:

1. **Parties** — who is involved
2. **Background** — key facts leading to the dispute
3. **Core Claims / Allegations** — what is being claimed
4. **Key Dates & Deadlines** — critical timeline items
5. **Monetary Figures** — any dollar amounts mentioned
6. **Open Questions** — facts that are unclear or missing from the documents

Rules:
- Every factual statement must be traceable to a specific evidence passage.
- If a section cannot be filled from the evidence, write "Not established by available documents."
- Do NOT add information not present in the evidence.
- Be concise. This is a first-pass internal document, not a brief.
""",

    DraftType.TITLE_REVIEW_SUMMARY: """
You are a paralegal reviewing title documents for a real estate or legal matter.
Using ONLY the provided evidence passages, write a title review summary covering:

1. **Property / Subject Matter Identification**
2. **Title Chain / Ownership History** — as evidenced in documents
3. **Encumbrances & Liens** — mortgages, judgments, or claims noted
4. **Exceptions & Exclusions** — anything excluded from coverage
5. **Defects or Concerns** — issues needing attention
6. **Recommendation** — clear / requires further review / unacceptable (based only on what is in the documents)

If any section cannot be answered from the evidence, say so explicitly.
""",

    DraftType.NOTICE_SUMMARY: """
You are a legal assistant summarizing notices found in the provided documents.
Using ONLY the evidence passages, produce a notice summary covering:

1. **Type of Notice** — what kind of notice this is
2. **Issuing Party** — who issued it
3. **Recipient** — who it is addressed to
4. **Date Issued / Effective Date**
5. **Core Obligation or Action Required**
6. **Deadline for Response or Compliance**
7. **Consequences of Non-Compliance** — as stated in the documents
8. **Supporting References** — statute sections or contract clauses cited

Missing information must be flagged, not guessed.
""",

    DraftType.DOCUMENT_CHECKLIST: """
You are a legal assistant reviewing a document set for completeness.
Using ONLY the provided evidence, generate a checklist covering:

For each document or category mentioned or implied:
- ✅ Present — if the document is clearly evidenced in the passages
- ⚠️ Partial — if only partial information is available
- ❌ Missing — if expected but not found
- ❓ Unclear — if the evidence is ambiguous

End with a **Summary** section listing total present / partial / missing counts
and a brief note on the most critical gaps.
""",

    DraftType.INTERNAL_MEMO: """
You are a senior associate at a law firm drafting an internal memo to the supervising partner.
Using ONLY the provided evidence passages, write a memo covering:

**TO:** Supervising Partner
**FROM:** AI Document Review System
**RE:** [Derive from document content]
**DATE:** [Use dates from documents if available]

---

**Purpose** — why this memo is being written

**Summary of Key Findings** — the most important facts and issues

**Analysis** — what the documents show and what is uncertain

**Recommended Next Steps** — what the team should do based on available information

**Caveats** — limitations of this review (what was not available or unclear)

Be direct and precise. Avoid filler. Every claim must come from the evidence.
""",
}


def _build_evidence_context(evidence: list[RetrievedEvidence]) -> str:
    """Format evidence chunks into a clear context block for the model."""
    if not evidence:
        return "No relevant evidence was retrieved for this query."

    lines = ["=== SOURCE EVIDENCE ===\n"]
    for i, ev in enumerate(evidence, start=1):
        page_ref = f"page {ev.page_number}" if ev.page_number else "page unknown"
        lines.append(
            f"[Evidence {i}] Source: {ev.source_filename} ({page_ref}) "
            f"| Relevance: {ev.relevance_score:.2f}\n"
            f"{ev.text.strip()}\n"
        )
    lines.append("=== END OF EVIDENCE ===")
    return "\n".join(lines)


def _build_user_message(
    draft_type: DraftType,
    evidence: list[RetrievedEvidence],
    structured_fields: dict,
    learned_patterns: list[str],
    additional_context: Optional[str],
) -> str:
    parts = []

    if structured_fields:
        parts.append("=== STRUCTURED FIELDS EXTRACTED FROM DOCUMENTS ===")
        for k, v in structured_fields.items():
            parts.append(f"{k}: {json.dumps(v)}")
        parts.append("")

    parts.append(_build_evidence_context(evidence))

    if learned_patterns:
        parts.append("\n=== OPERATOR PREFERENCES (learned from past edits) ===")
        for i, pattern in enumerate(learned_patterns, 1):
            parts.append(f"{i}. {pattern}")
        parts.append("")

    if additional_context:
        parts.append(f"\n=== ADDITIONAL CONTEXT ===\n{additional_context}")

    parts.append(f"\nPlease generate a {draft_type.value.replace('_', ' ')} based strictly on the evidence above.")
    return "\n".join(parts)


def generate_draft(
    draft_type: DraftType,
    evidence: list[RetrievedEvidence],
    document_ids: list[str],
    structured_fields: Optional[dict] = None,
    learned_patterns: Optional[list[str]] = None,
    additional_context: Optional[str] = None,
) -> GeneratedDraft:
    """
    Generate a grounded draft using the configured LLM service.

    Args:
        draft_type: the type of draft to produce
        evidence: retrieved chunks to ground the draft
        document_ids: source document IDs (for traceability)
        structured_fields: regex-extracted fields from document processor
        learned_patterns: instructions derived from past operator edits
        additional_context: optional free-text instructions from the operator
    """
    llm_service = get_llm_service()

    system_prompt = _DRAFT_PROMPTS[draft_type]
    user_message = _build_user_message(
        draft_type,
        evidence,
        structured_fields or {},
        learned_patterns or [],
        additional_context,
    )

    logger.info(f"Generating {draft_type.value} draft for {len(document_ids)} document(s)")

    response = llm_service.generate(
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=0.0,
        max_tokens=2000,
    )

    content = response.content

    # Build grounding map: identify which evidence items are referenced
    # We do this heuristically — a more robust approach would use tool use
    grounding_map = _build_grounding_map(content, evidence)

    return GeneratedDraft(
        draft_id=new_id(),
        draft_type=draft_type,
        document_ids=document_ids,
        content=content,
        evidence_used=evidence,
        grounding_map=grounding_map,
        model_used=response.model,
    )


def _build_grounding_map(content: str, evidence: list[RetrievedEvidence]) -> dict:
    """
    Map draft sections to the evidence chunks that likely support them.
    Heuristic: find evidence text fragments appearing near section headers.
    """
    import re

    # Split content into sections by markdown headers
    sections = re.split(r"\n(?=#+\s|\*\*\d+\.)", content)
    grounding = {}

    for section in sections:
        # Get section title
        title_match = re.match(r"[#*\d]+\.?\s*\*?\*?([^\n*]+)", section)
        if not title_match:
            continue
        title = title_match.group(1).strip()

        # Find which evidence chunks share key terms with this section
        section_lower = section.lower()
        supporting = []
        for ev in evidence:
            # Check if key phrases from this evidence appear in the section
            key_phrases = [p.strip() for p in ev.text.split(".") if len(p.strip()) > 20][:3]
            if any(phrase.lower()[:30] in section_lower for phrase in key_phrases):
                supporting.append(ev.chunk_id)
            # Also match on relevance — top-scored evidence likely supports every section
            elif ev.relevance_score > 0.75:
                supporting.append(ev.chunk_id)

        if supporting:
            grounding[title] = list(set(supporting))

    return grounding
