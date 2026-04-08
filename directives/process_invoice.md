# Directive: Process Invoice

## Goal
Extract structured data from uploaded PDF invoices using a hybrid AI approach, categorize expenses, validate totals, and present results for human review.

## Workflow Steps

### 1. Receive Invoice (Streamlit → FastAPI)
- User uploads a PDF via Streamlit UI
- File is sent to FastAPI `/process-invoice` endpoint
- File bytes are stored temporarily in `.tmp/`

### 2. Extract Data (Gemini 1.5 Flash)
- **Tool:** `execution/extract_invoice.py`
- **Input:** PDF file bytes (base64-encoded image or raw text via PyMuPDF)
- **Output:** `ExtractedInvoice` Pydantic model (JSON)
- **Model:** `gemini-1.5-flash` via `langchain-google-genai`
- Gemini reads the PDF visually and returns structured JSON matching the Pydantic schema
- If Gemini fails to extract a field, it returns `null` for that field

### 3. Categorize Expense (Ollama / Llama 3)
- **Tool:** `execution/categorize_invoice.py`
- **Input:** Extracted invoice JSON (vendor name, items, total)
- **Output:** Accounting category string
- **Model:** `glm-5:cloud` via Ollama (local)
- **Categories:** Software, Travel, Office Supplies, Meals & Entertainment, Professional Services, Utilities, Other

### 4. Validate Totals
- **Tool:** `execution/validate_invoice.py`
- **Input:** `ExtractedInvoice` with items and totals
- **Output:** Validation result (pass/fail + confidence score)
- **Checks:**
  - Sum of line items ≈ subtotal (within 2% tolerance)
  - Subtotal + tax ≈ total (within 2% tolerance)
  - Date is not in the future
  - Vendor name is not empty
- If validation fails, flag for human review

### 5. Present Results (Streamlit)
- Display extracted data in an editable table
- Highlight flagged rows in red
- Allow user to approve/edit before export
- CSV download button

## Edge Cases & Learnings
- Scanned PDFs with low resolution may need retry with enhanced prompt
- Multi-page invoices: process each page, then merge results
- Non-English invoices: add language hint to Gemini prompt
- Ollama must be running locally (`ollama serve`) before categorization

## Environment
- `GEMINI_API_KEY` in `.env` (required)
- Ollama running on `http://localhost:11434` (required for categorization)
