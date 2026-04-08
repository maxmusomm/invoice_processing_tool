"""
Pydantic schemas for the invoice processing workflow.
Shared across all execution scripts for consistency.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class InvoiceItem(BaseModel):
    """A single line item on an invoice."""
    description: str = Field(description="Description of the item or service")
    quantity: float = Field(default=1.0, description="Quantity of the item")
    unit_price: float = Field(default=0.0, description="Price per unit")
    total: float = Field(default=0.0, description="Line item total (quantity * unit_price)")


class ExtractedInvoice(BaseModel):
    """Structured data extracted from an invoice PDF."""
    vendor: str = Field(description="Name of the company sending the invoice")
    vendor_address: Optional[str] = Field(default=None, description="Address of the vendor")
    invoice_number: Optional[str] = Field(default=None, description="Invoice reference number")
    date: str = Field(description="Invoice date in YYYY-MM-DD format")
    due_date: Optional[str] = Field(default=None, description="Payment due date in YYYY-MM-DD format")
    subtotal: Optional[float] = Field(default=None, description="Subtotal before tax")
    tax_amount: Optional[float] = Field(default=None, description="Total tax amount")
    total_amount: float = Field(description="Grand total amount due")
    currency: str = Field(default="USD", description="Currency code (e.g. USD, EUR, ZAR)")
    items: List[InvoiceItem] = Field(default_factory=list, description="Line items on the invoice")
    category: Optional[str] = Field(default=None, description="Accounting category (filled by categorizer)")
    confidence: Optional[float] = Field(default=None, description="Extraction confidence score 0-1")
    flagged: bool = Field(default=False, description="Whether this invoice needs human review")
    flag_reason: Optional[str] = Field(default=None, description="Reason for flagging")


class ValidationResult(BaseModel):
    """Result of the invoice validation step."""
    is_valid: bool = Field(description="Whether the invoice passed all checks")
    checks: dict = Field(default_factory=dict, description="Individual check results")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
