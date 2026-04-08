"""
Invoice Categorization Tool — Layer 3 (Execution)

Uses Ollama (via ChatOllama from langchain-ollama) running locally to classify
an invoice into an accounting category. Keeps sensitive financial data off the cloud.

Falls back to a rule-based categorizer if Ollama is unavailable.

Usage as LangChain tool:
    from execution.categorize_invoice import categorize_invoice_tool
    result = categorize_invoice_tool.invoke({"vendor": "AWS", "items_text": "Cloud hosting", "total": 450.00})
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
import os

# ── Accounting categories ────────────────────────────────────
CATEGORIES = [
    "Software & SaaS",
    "Travel & Transport",
    "Office Supplies",
    "Meals & Entertainment",
    "Professional Services",
    "Utilities & Telecom",
    "Marketing & Advertising",
    "Insurance",
    "Rent & Facilities",
    "Other",
]

CATEGORIZATION_PROMPT = """You are an accounting assistant. Classify the following invoice into exactly ONE accounting category.

Vendor: {vendor}
Items/Description: {items_text}
Total Amount: {total}

Available categories:
{categories}

Return ONLY the category name. No explanation, no extra text.
"""

# ── Rule-based fallback ──────────────────────────────────────
KEYWORD_MAP = {
    "Software & SaaS": ["software", "saas", "cloud", "hosting", "subscription", "license", "aws", "azure", "google cloud", "digital ocean"],
    "Travel & Transport": ["travel", "flight", "hotel", "uber", "lyft", "taxi", "airfare", "rental car", "mileage"],
    "Office Supplies": ["office", "supplies", "paper", "printer", "ink", "toner", "stationery", "desk"],
    "Meals & Entertainment": ["meal", "restaurant", "food", "coffee", "catering", "lunch", "dinner"],
    "Professional Services": ["consulting", "legal", "accounting", "advisory", "audit", "attorney"],
    "Utilities & Telecom": ["electricity", "water", "internet", "phone", "telecom", "mobile", "fiber"],
    "Marketing & Advertising": ["marketing", "advertising", "ads", "campaign", "social media", "seo"],
    "Insurance": ["insurance", "premium", "coverage", "policy"],
    "Rent & Facilities": ["rent", "lease", "facilities", "maintenance", "cleaning"],
}


def categorize_rule_based(vendor: str, items_text: str) -> str:
    """Simple keyword-based fallback categorizer."""
    combined = f"{vendor} {items_text}".lower()
    for category, keywords in KEYWORD_MAP.items():
        if any(kw in combined for kw in keywords):
            return category
    return "Other"


def categorize_with_gemini(vendor: str, items_text: str, total: float) -> str:
    """Use Gemini for intelligent categorization via ChatGoogleGenerativeAI."""
    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
        prompt = CATEGORIZATION_PROMPT.format(
            vendor=vendor,
            items_text=items_text,
            total=total,
            categories="\n".join(f"- {c}" for c in CATEGORIES),
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()

        # Validate response is one of our categories
        for cat in CATEGORIES:
            if cat.lower() in response_text.lower():
                return cat

        # If Gemini returned something unexpected, fall back
        return categorize_rule_based(vendor, items_text)

    except Exception as e:
        print(f"[categorize] Gemini unavailable ({e}), using rule-based fallback.")
        return categorize_rule_based(vendor, items_text)


@tool
def categorize_invoice_tool(vendor: str, items_text: str, total: float) -> str:
    """Categorize an invoice into an accounting category using Gemini (Cloud LLM).

    Args:
        vendor: Name of the invoice vendor.
        items_text: Concatenated description of all line items.
        total: Total amount on the invoice.

    Returns:
        Accounting category string.
    """
    return categorize_with_gemini(vendor, items_text, total)
