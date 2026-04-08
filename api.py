"""
FastAPI Backend — Layer 2 (Orchestration)

Receives invoice PDFs, orchestrates the 3-step pipeline:
  1. Extract (Gemini Vision)
  2. Categorize (Ollama local)
  3. Validate (deterministic checks)

Run with:
    uvicorn api:app --reload --port 8000
"""

import os
import uuid
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from execution.extract_invoice import extract_invoice_from_bytes
from execution.categorize_invoice import categorize_with_ollama, categorize_rule_based
from execution.validate_invoice import validate_invoice
from execution.schemas import ExtractedInvoice

app = FastAPI(
    title="Invoice Processing Agent",
    description="Agentic workflow for extracting, categorizing, and validating invoices",
    version="1.0.0",
)

# Allow Streamlit to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for processed invoices (use DB in production)
processed_invoices: list[dict] = []

# Ensure .tmp/ exists
TMP_DIR = Path(".tmp")
TMP_DIR.mkdir(exist_ok=True)

 

@app.post("/process-invoice")
async def process_invoice(file: UploadFile = File(...)):
    """
    Full invoice processing pipeline:
    1. Extract structured data from PDF via Gemini
    2. Categorize using Ollama (with rule-based fallback)
    3. Validate mathematical consistency
    4. Return results with flags for human review
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()

    # ── Step 1: Extraction ───────────────────────────────────
    try:
        invoice = extract_invoice_from_bytes(file_bytes)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Gemini returned invalid JSON. Extraction failed: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {e}"
        )

    # ── Step 2: Categorization ───────────────────────────────
    items_text = ", ".join(item.description for item in invoice.items) if invoice.items else ""
    try:
        category = categorize_with_ollama(invoice.vendor, items_text, invoice.total_amount)
    except Exception:
        # Fallback to rule-based if Ollama is completely down
        category = categorize_rule_based(invoice.vendor, items_text)

    invoice.category = category

    # ── Step 3: Validation ───────────────────────────────────
    validation = validate_invoice(invoice)

    if not validation.is_valid:
        invoice.flagged = True
        invoice.flag_reason = "; ".join(validation.errors)
    elif validation.warnings:
        invoice.flagged = True
        invoice.flag_reason = "Warning: " + "; ".join(validation.warnings)

    # ── Store result ─────────────────────────────────────────
    result = invoice.model_dump()
    result["_id"] = str(uuid.uuid4())
    result["_filename"] = file.filename
    result["_validation"] = validation.model_dump()
    processed_invoices.append(result)

    return JSONResponse(content={
        "status": "success",
        "data": result,
        "validation": validation.model_dump(),
    })


@app.get("/invoices")
async def list_invoices():
    """Return all processed invoices."""
    return {"invoices": processed_invoices, "count": len(processed_invoices)}


@app.delete("/invoices")
async def clear_invoices():
    """Clear all processed invoices from memory."""
    processed_invoices.clear()
    return {"status": "cleared"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "invoices_in_memory": len(processed_invoices)}
