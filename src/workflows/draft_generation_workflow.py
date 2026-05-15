

from __future__ import annotations
import logging
from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from ..models import DraftType, RetrievedEvidence
from ..services.llm_service import get_llm_service
from ..retrieval import retrieve_evidence
from ..repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class DraftGenerationState(TypedDict):
    """State object passed through the workflow"""
    # Inputs
    document_ids: List[str]
    draft_type: DraftType
    additional_context: Optional[str]
    query_override: Optional[str]
    
    # Intermediate state
    documents: List[Dict]
    structured_fields: Dict
    retrieval_query: str
    evidence: List[RetrievedEvidence]
    learned_patterns: List[str]
    
    # Outputs
    draft_content: str
    grounding_map: Dict
    model_used: str
    
    # Error handling
    error: Optional[str]


class DraftGenerationWorkflow:
    """
    LangGraph-based workflow for draft generation
    Provides clear separation of concerns and testability
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construct the workflow graph"""
        workflow = StateGraph(DraftGenerationState)
        
        # Add nodes
        workflow.add_node("validate_inputs", self._validate_inputs)
        workflow.add_node("fetch_documents", self._fetch_documents)
        workflow.add_node("build_query", self._build_retrieval_query)
        workflow.add_node("retrieve_evidence", self._retrieve_evidence)
        workflow.add_node("load_patterns", self._load_learned_patterns)
        workflow.add_node("generate_draft", self._generate_draft)
        workflow.add_node("build_grounding", self._build_grounding_map)
        
        # Define edges (flow)
        workflow.set_entry_point("validate_inputs")
        workflow.add_edge("validate_inputs", "fetch_documents")
        workflow.add_edge("fetch_documents", "build_query")
        workflow.add_edge("build_query", "retrieve_evidence")
        workflow.add_edge("retrieve_evidence", "load_patterns")
        workflow.add_edge("load_patterns", "generate_draft")
        workflow.add_edge("generate_draft", "build_grounding")
        workflow.add_edge("build_grounding", END)
        
        return workflow.compile()
    
    def _validate_inputs(self, state: DraftGenerationState) -> DraftGenerationState:
        """Validate input parameters"""
        logger.info("Validating inputs...")
        
        if not state.get("document_ids"):
            state["error"] = "No document IDs provided"
            return state
        
        if not state.get("draft_type"):
            state["error"] = "No draft type specified"
            return state
        
        logger.info(f"Inputs valid: {len(state['document_ids'])} documents, type: {state['draft_type']}")
        return state
    
    def _fetch_documents(self, state: DraftGenerationState) -> DraftGenerationState:
        """Fetch document metadata and structured fields"""
        logger.info("Fetching documents...")
        
        # In a real implementation, fetch from database
        # For now, we'll use a placeholder
        state["documents"] = []
        state["structured_fields"] = {}
        
        return state
    
    def _build_retrieval_query(self, state: DraftGenerationState) -> DraftGenerationState:
        """Build the retrieval query based on draft type"""
        logger.info("Building retrieval query...")
        
        if state.get("query_override"):
            state["retrieval_query"] = state["query_override"]
        else:
            # Default queries per draft type
            queries = {
                DraftType.CASE_FACT_SUMMARY: "parties claims facts dates timeline dispute",
                DraftType.TITLE_REVIEW_SUMMARY: "title ownership property encumbrance lien",
                DraftType.NOTICE_SUMMARY: "notice deadline obligation compliance requirement",
                DraftType.DOCUMENT_CHECKLIST: "documents required missing checklist items",
                DraftType.INTERNAL_MEMO: "key facts findings issues recommendations summary",
            }
            state["retrieval_query"] = queries.get(
                state["draft_type"],
                "relevant facts and information"
            )
        
        logger.info(f"Query: {state['retrieval_query']}")
        return state
    
    def _retrieve_evidence(self, state: DraftGenerationState) -> DraftGenerationState:
        """Retrieve relevant evidence from vector store"""
        logger.info("Retrieving evidence...")
        
        evidence = retrieve_evidence(
            query=state["retrieval_query"],
            document_ids=state["document_ids"],
            n_results=6,
        )
        
        state["evidence"] = evidence
        logger.info(f"Retrieved {len(evidence)} evidence chunks")
        return state
    
    def _load_learned_patterns(self, state: DraftGenerationState) -> DraftGenerationState:
        """Load learned patterns for this draft type"""
        logger.info("Loading learned patterns...")
        
        # Import here to avoid circular dependency
        from ..improvement_engine import get_patterns_for_draft_type
        
        patterns = get_patterns_for_draft_type(state["draft_type"])
        state["learned_patterns"] = patterns
        logger.info(f"Loaded {len(patterns)} patterns")
        return state
    
    def _generate_draft(self, state: DraftGenerationState) -> DraftGenerationState:
        """Generate the draft using LLM"""
        logger.info("Generating draft...")
        
        # Build system prompt
        system_prompt = self._get_system_prompt(state["draft_type"])
        
        # Build user message with evidence and patterns
        user_message = self._build_user_message(
            state["evidence"],
            state["structured_fields"],
            state["learned_patterns"],
            state.get("additional_context")
        )
        
        # Generate
        response = self.llm_service.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.0,
            max_tokens=2000,
        )
        
        state["draft_content"] = response.content
        state["model_used"] = response.model
        logger.info(f"Draft generated using {response.model}")
        return state
    
    def _build_grounding_map(self, state: DraftGenerationState) -> DraftGenerationState:
        """Build grounding map linking draft sections to evidence"""
        logger.info("Building grounding map...")
        
        # Import here to avoid circular dependency
        from ..draft_generator import _build_grounding_map
        
        grounding_map = _build_grounding_map(
            state["draft_content"],
            state["evidence"]
        )
        
        state["grounding_map"] = grounding_map
        logger.info(f"Grounding map built with {len(grounding_map)} sections")
        return state
    
    def _get_system_prompt(self, draft_type: DraftType) -> str:
        """Get system prompt for draft type"""
        prompts = {
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
        
        return prompts.get(draft_type, "Generate a professional legal document based on the evidence.")
    
    def _build_user_message(
        self,
        evidence: List[RetrievedEvidence],
        structured_fields: Dict,
        learned_patterns: List[str],
        additional_context: Optional[str]
    ) -> str:
        """Build the user message with all context"""
        parts = []
        
        if structured_fields:
            parts.append("=== STRUCTURED FIELDS EXTRACTED FROM DOCUMENTS ===")
            import json
            for k, v in structured_fields.items():
                parts.append(f"{k}: {json.dumps(v)}")
            parts.append("")
        
        # Evidence
        parts.append("=== SOURCE EVIDENCE ===\n")
        for i, ev in enumerate(evidence, start=1):
            page_ref = f"page {ev.page_number}" if ev.page_number else "page unknown"
            parts.append(
                f"[Evidence {i}] Source: {ev.source_filename} ({page_ref}) "
                f"| Relevance: {ev.relevance_score:.2f}\n"
                f"{ev.text.strip()}\n"
            )
        parts.append("=== END OF EVIDENCE ===")
        
        if learned_patterns:
            parts.append("\n=== OPERATOR PREFERENCES (learned from past edits) ===")
            for i, pattern in enumerate(learned_patterns, 1):
                parts.append(f"{i}. {pattern}")
            parts.append("")
        
        if additional_context:
            parts.append(f"\n=== ADDITIONAL CONTEXT ===\n{additional_context}")
        
        parts.append("\nPlease generate the draft based strictly on the evidence above.")
        return "\n".join(parts)
    
    def execute(self, **inputs) -> DraftGenerationState:
        """Execute the workflow"""
        logger.info("Starting draft generation workflow...")
        
        try:
            result = self.graph.invoke(inputs)
            
            if result.get("error"):
                logger.error(f"Workflow error: {result['error']}")
            else:
                logger.info("Workflow completed successfully")
            
            return result
            
        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            return {
                **inputs,
                "error": str(e),
                "draft_content": "",
                "grounding_map": {},
                "model_used": "",
            }
