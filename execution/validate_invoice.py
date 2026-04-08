"""
Invoice Validation Tool — Layer 3 (Execution)

Performs deterministic sanity checks on extracted invoice data:
  - Line items sum ≈ subtotal
  - Subtotal + tax ≈ total
  - Date is not in the future
  - Required fields are present

Usage as LangChain tool:
    from execution.validate_invoice import validate_invoice_tool
    result = validate_invoice_tool.invoke({"invoice_data": {...}})
"""

from datetime import datetime, date
from langchain_core.tools import tool
from execution.schemas import ExtractedInvoice, ValidationResult


TOLERANCE = 0.02  # 2% tolerance for floating-point rounding


def _check_items_sum(invoice: ExtractedInvoice) -> tuple[bool, str | None]:
    """Check if the sum of line item totals roughly matches subtotal or total."""
    if not invoice.items:
        return True, None  # No items to check

    items_sum = sum(item.total for item in invoice.items)

    # Compare against subtotal if available, otherwise total
    reference = invoice.subtotal if invoice.subtotal is not None else invoice.total_amount
    if reference == 0:
        return True, None

    diff_pct = abs(items_sum - reference) / reference
    if diff_pct > TOLERANCE:
        return False, (
            f"Line items sum ({items_sum:.2f}) differs from "
            f"{'subtotal' if invoice.subtotal else 'total'} ({reference:.2f}) "
            f"by {diff_pct:.1%}"
        )
    return True, None


def _check_total_matches(invoice: ExtractedInvoice) -> tuple[bool, str | None]:
    """Check if subtotal + tax ≈ total."""
    if invoice.subtotal is None or invoice.tax_amount is None:
        return True, None  # Can't verify without both values

    expected = invoice.subtotal + invoice.tax_amount
    if invoice.total_amount == 0:
        return True, None

    diff_pct = abs(expected - invoice.total_amount) / invoice.total_amount
    if diff_pct > TOLERANCE:
        return False, (
            f"Subtotal ({invoice.subtotal:.2f}) + Tax ({invoice.tax_amount:.2f}) = "
            f"{expected:.2f}, but total is {invoice.total_amount:.2f} "
            f"(diff: {diff_pct:.1%})"
        )
    return True, None


def _check_date_not_future(invoice: ExtractedInvoice) -> tuple[bool, str | None]:
    """Check that the invoice date is not in the future."""
    try:
        inv_date = datetime.strptime(invoice.date, "%Y-%m-%d").date()
        if inv_date > date.today():
            return False, f"Invoice date {invoice.date} is in the future"
    except ValueError:
        return False, f"Invalid date format: {invoice.date} (expected YYYY-MM-DD)"
    return True, None


def _check_required_fields(invoice: ExtractedInvoice) -> tuple[bool, str | None]:
    """Check that essential fields are present."""
    errors = []
    if not invoice.vendor or invoice.vendor.strip() == "":
        errors.append("Vendor name is missing")
    if invoice.total_amount == 0:
        errors.append("Total amount is zero")
    if not invoice.date:
        errors.append("Date is missing")

    if errors:
        return False, "; ".join(errors)
    return True, None


def validate_invoice(invoice: ExtractedInvoice) -> ValidationResult:
    """Run all validation checks on an extracted invoice."""
    checks = {}
    errors = []
    warnings = []

    # Run each check
    for check_name, check_fn in [
        ("items_sum", _check_items_sum),
        ("total_matches", _check_total_matches),
        ("date_valid", _check_date_not_future),
        ("required_fields", _check_required_fields),
    ]:
        passed, message = check_fn(invoice)
        checks[check_name] = passed
        if not passed and message:
            # Items sum mismatch is a warning, others are errors
            if check_name == "items_sum":
                warnings.append(message)
            else:
                errors.append(message)

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        checks=checks,
        errors=errors,
        warnings=warnings,
    )


@tool
def validate_invoice_tool(invoice_data: dict) -> dict:
    """Validate extracted invoice data for mathematical and logical consistency.

    Args:
        invoice_data: Dictionary of extracted invoice fields.

    Returns:
        Dictionary with validation results including is_valid, checks, errors, warnings.
    """
    invoice = ExtractedInvoice(**invoice_data)
    result = validate_invoice(invoice)
    return result.model_dump()
