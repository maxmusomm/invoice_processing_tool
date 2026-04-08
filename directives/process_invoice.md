# Directive: Process Invoice

## Goal
Extract structured data from uploaded PDF invoices using a Gemini-powered cloud workflow, categorize expenses, validate totals, and present results for human review through a FastAPI served static interface.

## Workflow Steps

### 1. Receive Invoice (FastAPI native)
- User selects PDF invoices via an HTML UI (`frontend/index.html`) served natively by FastAPI.
- Selected files enter a "Staging Area" where the user can review the queued files, and click a process button to confirm the batch.
- Selected PDFs are then sent to the FastAPI `/process-invoice` endpoint via AJAX.

### 2. Extract Data (Gemini 1.5 Flash)
- **Tool:** `execution/extract_invoice.py`
- **Input:** PDF file bytes (base64-encoded image or raw text)
- **Output:** `ExtractedInvoice` Pydantic model (JSON)
- **Model:** `gemini-1.5-flash` or the `GEMINI_MODEL` specified in `.env` via `langchain-google-genai`
- Gemini reads the PDF visually and returns structured JSON matching the Pydantic schema
- If Gemini fails to extract a field, it returns `null` for that field.

### 3. Categorize Expense (Gemini)
- **Tool:** `execution/categorize_invoice.py`
- **Input:** Extracted invoice JSON (vendor name, items, total)
- **Output:** Accounting category string
- **Model:** `gemini-3.1-flash-lite-preview` via `langchain-google-genai`
- **Categories:** Software & SaaS, Travel & Transport, Office Supplies, Meals & Entertainment, Professional Services, Utilities & Telecom, Marketing & Advertising, Insurance, Rent & Facilities, Other

### 4. Validate Totals
- **Tool:** `execution/validate_invoice.py`
- **Input:** `ExtractedInvoice` with items and totals
- **Output:** Validation result (pass/fail + confidence score)
- **Checks:**
  - Sum of line items ≈ subtotal (within 2% tolerance)
  - Subtotal + tax ≈ total (within 2% tolerance)
  - Date is not in the future
  - Vendor name is not empty
- If validation fails, flag for human review.

### 5. Present Results (Table Component)
- Processed data is fetched via `/invoices` from memory.
- Displayed uniformly on a minimalist UI in a table structure (`Results Ledger`) with columns for Vendor, Date, Category, Total Amount, and Status.
- Allows user to "Clear Data" or batch-export down to a detailed row-level `.csv` file.

## Edge Cases & Learnings
- Scanned PDFs with low resolution may need retry with enhanced prompt.
- The UI handles errors gracefully in case Gemini's extraction JSON triggers a failure block on the endpoint.
- File Staging ensures the user does not mistakenly upload bad files asynchronously.

## Environment
- `GEMINI_API_KEY` in `.env` (required).
- `GEMINI_MODEL` configured centrally in `.env`.
- No separate process is required outside `uvicorn api:app --reload`.
