"""
Streamlit Frontend — Human-in-the-Loop Interface

Upload invoices, review extracted data, approve/flag results, export to CSV.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import io
import uuid
import json

from execution.extract_invoice import extract_invoice_from_bytes
from execution.categorize_invoice import categorize_with_gemini, categorize_rule_based
from execution.validate_invoice import validate_invoice

# ── Config ───────────────────────────────────────────────────

st.set_page_config(
    page_title="Invoice Processing Agent",
    page_icon="🧾",
    layout="wide",
)

# ── Custom styling ───────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        background-color: #f7f9fc;
        color: #2c3338;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Public Sans', sans-serif !important;
        color: #123d6c !important;
    }

    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 10px 25px -5px rgba(44, 51, 56, 0.05);
        border: 1px solid #e3e9ee;
    }

    /* Force text colors to be dark inside metric to contrast the white background */
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] div,
    div[data-testid="stMetric"] span,
    div[data-testid="stMetricValue"] {
        color: #2c3338 !important;
    }

    div[data-testid="stMetricDelta"] {
        color: #2c3338 !important;
    }

    /* Force global text color on main containers */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {
        color: #2c3338 !important;
    }

    .stButton>button[kind="primary"] {
        background-color: #3c6091 !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        border: none !important;
        box-shadow: 0 10px 15px -3px rgba(60, 96, 145, 0.3) !important;
        border-radius: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
st.title("🧾 AI Invoice Processing Agent")
st.markdown(
    "Upload PDF invoices → AI extracts & categorizes → you review & export. "
    "**Gemini** handles both extraction and categorization for efficient cloud processing."
)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("Running locally as a unified App.")

    st.divider()

    if st.button("🗑️ Clear All Invoices", type="secondary"):
        st.session_state["invoices"] = []
        st.rerun()

# ── Upload Section ───────────────────────────────────────────
st.header("📤 Upload Invoice")

uploaded_files = st.file_uploader(
    "Drop your invoice PDFs here",
    type=["pdf"],
    accept_multiple_files=True,
    help="Supports single and multi-page PDF invoices",
)

if uploaded_files:
    st.info(f"📎 {len(uploaded_files)} file(s) ready to process")

    if st.button("🚀 Process All Invoices", type="primary"):
        progress = st.progress(0, text="Starting...")
        results = []

        for i, uploaded_file in enumerate(uploaded_files):
            progress.progress(
                (i) / len(uploaded_files),
                text=f"Processing {uploaded_file.name}..."
            )

            try:
                # ── Step 1: Extraction ───────────────────────────────────
                file_bytes = uploaded_file.getvalue()
                invoice = extract_invoice_from_bytes(file_bytes)
                
                # ── Step 2: Categorization ───────────────────────────────
                items_text = ", ".join(item.description for item in invoice.items) if invoice.items else ""
                try:
                    category = categorize_with_gemini(invoice.vendor, items_text, invoice.total_amount)
                except Exception:
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
                else:
                    invoice.flagged = False
                    
                # ── Store Result ─────────────────────────────────────────
                result = invoice.model_dump()
                result["_id"] = str(uuid.uuid4())
                result["_filename"] = uploaded_file.name
                result["_validation"] = validation.model_dump()
                
                results.append(result)
                st.toast(f"✅ {uploaded_file.name} processed", icon="✅")

            except Exception as e:
                st.error(f"❌ {uploaded_file.name}: {e}")

        progress.progress(1.0, text="Done!")

        if results:
            st.session_state["invoices"] = results
            st.rerun()

# ── Results Section ──────────────────────────────────────────
st.header("📊 Processed Invoices")

if "invoices" not in st.session_state:
    st.session_state["invoices"] = []

if st.session_state["invoices"]:
    invoices = st.session_state["invoices"]

    # Build display DataFrame
    display_data = []
    for inv in invoices:
        row = {
            "File": inv.get("_filename", "—"),
            "Vendor": inv.get("vendor", "—"),
            "Date": inv.get("date", "—"),
            "Total": inv.get("total_amount", 0),
            "Tax": inv.get("tax_amount", "—"),
            "Currency": inv.get("currency", "—"),
            "Category": inv.get("category", "—"),
            "Items": len(inv.get("items", [])),
            "Flagged": "🚩" if inv.get("flagged") else "✅",
            "Flag Reason": inv.get("flag_reason", "—") if inv.get("flagged") else "—",
        }
        display_data.append(row)

    df = pd.DataFrame(display_data)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Invoices", len(invoices))
    with col2:
        total_value = sum(inv.get("total_amount", 0) for inv in invoices)
        st.metric("Total Value", f"${total_value:,.2f}")
    with col3:
        flagged = sum(1 for inv in invoices if inv.get("flagged"))
        st.metric("Flagged", flagged, delta=f"-{len(invoices) - flagged} clean", delta_color="inverse")
    with col4:
        categories = set(inv.get("category", "Other") for inv in invoices)
        st.metric("Categories", len(categories))

    # Display table
    st.dataframe(df, width="stretch", hide_index=True)

    # ── Detailed view ────────────────────────────────────────
    with st.expander("📋 Detailed Line Items"):
        for inv in invoices:
            st.subheader(f"{inv.get('vendor', 'Unknown')} — {inv.get('date', '')}")
            if inv.get("items"):
                items_df = pd.DataFrame(inv["items"])
                st.dataframe(items_df, width="stretch", hide_index=True)
            else:
                st.caption("No line items extracted")
            st.divider()

    # ── CSV Export ───────────────────────────────────────────
    st.header("💾 Export")

    # Flatten for CSV
    csv_rows = []
    for inv in invoices:
        base = {
            "vendor": inv.get("vendor"),
            "invoice_number": inv.get("invoice_number"),
            "date": inv.get("date"),
            "due_date": inv.get("due_date"),
            "subtotal": inv.get("subtotal"),
            "tax_amount": inv.get("tax_amount"),
            "total_amount": inv.get("total_amount"),
            "currency": inv.get("currency"),
            "category": inv.get("category"),
            "flagged": inv.get("flagged"),
            "flag_reason": inv.get("flag_reason"),
        }
        if inv.get("items"):
            for item in inv["items"]:
                row = {**base, **item}
                csv_rows.append(row)
        else:
            csv_rows.append(base)

    export_df = pd.DataFrame(csv_rows)
    csv_data = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name="processed_invoices.csv",
        mime="text/csv",
        type="primary",
    )

else:
    st.info("No invoices processed yet. Upload a PDF above to get started.")
