

from __future__ import annotations
import re
import json
import logging
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF

from .models import (
    DocumentStatus, ExtractedChunk, ProcessedDocument, new_id
)
from .config import settings

logger = logging.getLogger(__name__)

# Minimum chars per page before we treat it as scanned and apply OCR
# Lowered threshold for better detection of scanned documents
_NATIVE_TEXT_THRESHOLD = 30  # Reduced from 50 to 30


def _try_import_tesseract():
    try:
        import pytesseract
        from PIL import Image
        
        # Set Tesseract path for Windows
        import platform
        if platform.system() == 'Windows':
            # Try common installation paths
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            for path in possible_paths:
                if Path(path).exists():
                    pytesseract.pytesseract.tesseract_cmd = path
                    logger.info(f"Tesseract found at: {path}")
                    break
        
        return pytesseract, Image
    except ImportError:
        return None, None


def _extract_page_native(page: fitz.Page) -> tuple[str, bool]:
    """
    Extract text from a page using PyMuPDF native extraction.
    Tries multiple extraction methods for better results.
    """
    # Try standard text extraction first
    text = page.get_text("text")
    
    # If no text found, try blocks method (better for complex layouts)
    if not text.strip():
        text = page.get_text("blocks")
        if isinstance(text, list):
            text = "\n".join([block[4] for block in text if len(block) > 4])
    
    # If still no text, try dict method (most detailed)
    if not text.strip():
        text_dict = page.get_text("dict")
        blocks = text_dict.get("blocks", [])
        text_parts = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text_parts.append(span.get("text", ""))
        text = " ".join(text_parts)
    
    return text.strip(), True


def _extract_page_ocr(page: fitz.Page) -> tuple[str, float]:
    """
    Render the page to an image and run Tesseract OCR.
    Returns (text, confidence 0-1).
    If Tesseract is not available, returns empty string with 0 confidence.
    Supports multiple languages including Bengali.
    """
    pytesseract, Image = _try_import_tesseract()
    if pytesseract is None:
        logger.warning("pytesseract not available — skipping OCR for this page")
        return "", 0.0

    try:
        # Higher resolution for better OCR accuracy
        mat = fitz.Matrix(3.0, 3.0)  # Increased from 2.0 to 3.0
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pix.tobytes("png")

        import io
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to grayscale for better OCR
        img = img.convert('L')
        
        # Enhance image quality
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)  # Increase contrast
        
        # Try Bengali + English OCR with custom config
        # PSM 6 = Assume a single uniform block of text
        # PSM 3 = Fully automatic page segmentation (default)
        custom_config = r'--oem 3 --psm 6'
        
        try:
            # Try with Bengali + English
            text = pytesseract.image_to_string(
                img, 
                lang='ben+eng',
                config=custom_config
            )
            logger.debug("Using Bengali + English OCR")
            
            # If no text found, try with different PSM mode
            if not text.strip():
                custom_config = r'--oem 3 --psm 3'
                text = pytesseract.image_to_string(
                    img, 
                    lang='ben+eng',
                    config=custom_config
                )
                logger.debug("Retrying with PSM 3")
                
        except Exception as lang_error:
            logger.warning(f"Bengali OCR not available, using English only: {lang_error}")
            text = pytesseract.image_to_string(
                img, 
                config=custom_config
            )
        
        # Get confidence score
        try:
            ocr_data = pytesseract.image_to_data(
                img,
                lang='ben+eng' if 'ben' in pytesseract.get_languages() else 'eng',
                output_type=pytesseract.Output.DICT
            )
            confidences = [int(ocr_data["conf"][i]) / 100.0 
                          for i in range(len(ocr_data["conf"])) 
                          if int(ocr_data["conf"][i]) > 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        except:
            avg_conf = 0.7  # Default confidence if we can't calculate
        
        return text.strip(), avg_conf
        
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return "", 0.0


def _chunk_text(
    text: str,
    document_id: str,
    page_number: Optional[int],
    chunk_size: int,
    overlap: int,
    confidence: float,
) -> list[ExtractedChunk]:
    """Split text into overlapping chunks preserving sentence boundaries where possible."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = []
    current_len = 0
    chunk_index = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current_len + len(sentence) > chunk_size and current:
            chunk_text = " ".join(current)
            chunks.append(ExtractedChunk(
                chunk_id=new_id(),
                document_id=document_id,
                text=chunk_text,
                page_number=page_number,
                chunk_index=chunk_index,
                confidence=confidence,
                metadata={"char_count": len(chunk_text)},
            ))
            chunk_index += 1
            # Keep last N chars worth of sentences for overlap
            overlap_text = chunk_text[-overlap:]
            current = [overlap_text] if overlap_text else []
            current_len = len(overlap_text)

        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        chunk_text = " ".join(current)
        if chunk_text.strip():
            chunks.append(ExtractedChunk(
                chunk_id=new_id(),
                document_id=document_id,
                text=chunk_text,
                page_number=page_number,
                chunk_index=chunk_index,
                confidence=confidence,
                metadata={"char_count": len(chunk_text)},
            ))

    return chunks


def _extract_structured_fields(raw_text: str) -> dict:
    """
    Pull common legal document fields using regex patterns.
    Fast, no API calls. Claude-based extraction is done separately for
    ambiguous fields in the draft generator.
    """
    fields = {}

    # Case / matter references
    case_refs = re.findall(
        r"\b(?:Case|Matter|Docket|Cause)\s*(?:No\.?|Number|#)?\s*:?\s*([\w\-\/]+)",
        raw_text, re.IGNORECASE
    )
    if case_refs:
        fields["case_references"] = list(set(case_refs))

    # Dates
    dates = re.findall(
        r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\b(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b",
        raw_text, re.IGNORECASE
    )
    if dates:
        fields["dates_mentioned"] = list(set(dates))[:10]

    # Party names (simple heuristic: words after "Plaintiff:" / "Defendant:")
    for role in ["Plaintiff", "Defendant", "Petitioner", "Respondent", "Claimant"]:
        match = re.search(rf"{role}\s*:?\s*([A-Z][^\n,\.]+)", raw_text, re.IGNORECASE)
        if match:
            fields[role.lower()] = match.group(1).strip()

    # Dollar amounts
    amounts = re.findall(r"\$[\d,]+(?:\.\d{2})?", raw_text)
    if amounts:
        fields["monetary_amounts"] = list(set(amounts))[:10]

    # Statute / section references
    statutes = re.findall(
        r"\b(?:Section|§|Art\.?|Article)\s*[\d\.\-]+[A-Za-z]?",
        raw_text, re.IGNORECASE
    )
    if statutes:
        fields["statute_references"] = list(set(statutes))[:10]

    return fields


def process_document(file_path: str | Path) -> ProcessedDocument:
    """
    Main entry point. Accepts any file path and returns a fully
    processed document ready for indexing.
    """
    file_path = Path(file_path)
    document_id = new_id()
    filename = file_path.name
    notes = []
    all_chunks: list[ExtractedChunk] = []
    all_text_parts = []
    ocr_applied = False

    logger.info(f"Processing document: {filename}")

    try:
        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            raw_text = file_path.read_text(encoding="utf-8", errors="replace")
            chunks = _chunk_text(
                raw_text, document_id, None,
                settings.chunk_size, settings.chunk_overlap, 1.0
            )
            return ProcessedDocument(
                document_id=document_id,
                filename=filename,
                status=DocumentStatus.READY,
                raw_text=raw_text,
                chunks=chunks,
                structured_fields=_extract_structured_fields(raw_text),
                page_count=1,
                ocr_applied=False,
                processing_notes=[],
            )

        # PDF handling
        doc = fitz.open(str(file_path))
        page_count = len(doc)

        for page_num, page in enumerate(doc, start=1):
            native_text, _ = _extract_page_native(page)
            native_text = native_text.strip()

            if len(native_text) >= _NATIVE_TEXT_THRESHOLD:
                page_text = native_text
                confidence = 1.0
            else:
                # Sparse native text — likely scanned
                logger.debug(f"Page {page_num}: sparse native text, applying OCR")
                ocr_text, ocr_confidence = _extract_page_ocr(page)
                if ocr_text.strip():
                    page_text = ocr_text
                    confidence = ocr_confidence
                    ocr_applied = True
                    if ocr_confidence < 0.6:
                        notes.append(
                            f"Page {page_num}: low OCR confidence ({ocr_confidence:.2f}) — "
                            "content may be partially illegible"
                        )
                else:
                    page_text = native_text  # fallback to whatever we have
                    confidence = 0.3
                    notes.append(f"Page {page_num}: could not extract reliable text")

            if page_text.strip():
                all_text_parts.append(page_text)
                page_chunks = _chunk_text(
                    page_text, document_id, page_num,
                    settings.chunk_size, settings.chunk_overlap, confidence
                )
                all_chunks.extend(page_chunks)

        doc.close()
        raw_text = "\n\n".join(all_text_parts)

        if not raw_text.strip():
            return ProcessedDocument(
                document_id=document_id,
                filename=filename,
                status=DocumentStatus.FAILED,
                raw_text="",
                chunks=[],
                structured_fields={},
                page_count=page_count,
                ocr_applied=ocr_applied,
                processing_notes=["No text could be extracted from this document"],
            )

        structured = _extract_structured_fields(raw_text)

        return ProcessedDocument(
            document_id=document_id,
            filename=filename,
            status=DocumentStatus.READY,
            raw_text=raw_text,
            chunks=all_chunks,
            structured_fields=structured,
            page_count=page_count,
            ocr_applied=ocr_applied,
            processing_notes=notes,
        )

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Failed to process {filename}: {e}")
        
        # Check if it's a Tesseract error
        if "tesseract" in error_msg.lower() or "TesseractNotFoundError" in str(type(e)):
            processing_note = (
                "OCR is not available. To process image files, please install Tesseract OCR. "
                "For now, you can only upload PDF files with native text."
            )
        else:
            processing_note = f"Processing failed: {error_msg}"
        
        return ProcessedDocument(
            document_id=document_id,
            filename=filename,
            status=DocumentStatus.FAILED,
            raw_text="",
            chunks=[],
            structured_fields={},
            page_count=0,
            ocr_applied=False,
            processing_notes=[processing_note],
        )
