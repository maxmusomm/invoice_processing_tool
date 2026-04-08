"""
Invoice Extraction Tool — Layer 3 (Execution)

Uses Google Gemini to extract structured data from invoice PDFs.
Gemini's native vision capability reads the PDF as an image and returns JSON.

Usage as LangChain tool:
    from execution.extract_invoice import extract_invoice_tool
    result = extract_invoice_tool.invoke({"file_path": "/path/to/invoice.pdf"})
"""

import os
import json
import base64
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from execution.schemas import ExtractedInvoice

load_dotenv()

# ── Gemini model ──────────────────────────────────────────────
# Docs: use `api_key` param (not `google_api_key`)
# Env var GOOGLE_API_KEY is also auto-detected
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_MODEL = ChatGoogleGenerativeAI(
    model=model_name,
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
    max_retries=2,
)

# ── Extraction prompt ────────────────────────────────────────
EXTRACTION_PROMPT = """You are a precise invoice data extractor. Analyze the provided invoice image and extract ALL of the following fields into a JSON object.

Return ONLY valid JSON with these exact keys:
{
  "vendor": "Company name on the invoice",
  "vendor_address": "Full address of the vendor or null",
  "invoice_number": "Invoice/reference number or null",
  "date": "Invoice date in YYYY-MM-DD format",
  "due_date": "Due date in YYYY-MM-DD format or null",
  "subtotal": numeric value or null,
  "tax_amount": numeric value or null,
  "total_amount": numeric grand total,
  "currency": "3-letter currency code e.g. USD, EUR, ZAR",
  "items": [
    {
      "description": "Item or service description",
      "quantity": numeric,
      "unit_price": numeric,
      "total": numeric
    }
  ]
}

Rules:
- Return ONLY the JSON object. No markdown, no code fences, no commentary.
- If a field is not found, use null.
- Dates must be YYYY-MM-DD. If the year is ambiguous, assume the current year.
- All monetary values must be plain numbers (no currency symbols).
- Extract EVERY line item you can find.
"""


def pdf_to_images_base64(file_path: str) -> list[str]:
    """Convert each page of a PDF to a base64-encoded PNG image."""
    doc = fitz.open(file_path)
    images = []
    for page in doc:
        # Render at 2x for better OCR quality
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        images.append(b64)
    doc.close()
    return images


def pdf_bytes_to_images_base64(file_bytes: bytes) -> list[str]:
    """Convert PDF bytes to a list of base64-encoded PNG images."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        images.append(b64)
    doc.close()
    return images


def extract_from_images(images_b64: list[str]) -> ExtractedInvoice:
    """Send base64 images to Gemini and parse the structured response."""
    # Build message content: text prompt + all page images
    # Docs: use {"type": "image", "url": ...} or {"type": "image", "base64": ..., "mime_type": ...}
    content = [{"type": "text", "text": EXTRACTION_PROMPT}]
    for img_b64 in images_b64:
        content.append({
            "type": "image",
            "source_type": "base64",
            "data": img_b64,
            "mime_type": "image/png",
        })

    message = HumanMessage(content=content)
    response = GEMINI_MODEL.invoke([message])

    # Parse JSON from response
    raw_text = response.content.strip()
    # Strip markdown fences if Gemini wraps them anyway
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        raw_text = raw_text.rsplit("```", 1)[0]

    data = json.loads(raw_text)
    invoice = ExtractedInvoice(**data)
    return invoice


@tool
def extract_invoice_tool(file_path: str) -> dict:
    """Extract structured data from an invoice PDF using Gemini Vision.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Dictionary of extracted invoice fields.
    """
    images = pdf_to_images_base64(file_path)
    invoice = extract_from_images(images)
    return invoice.model_dump()


def extract_invoice_from_bytes(file_bytes: bytes) -> ExtractedInvoice:
    """Extract invoice data from raw PDF bytes (used by FastAPI endpoint)."""
    images = pdf_bytes_to_images_base64(file_bytes)
    invoice = extract_from_images(images)
    return invoice
