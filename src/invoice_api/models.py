from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

TEMPLATE_NAMES = ("professional", "studio", "sidebar", "noir", "swiss", "classic", "modern", "minimal", "bold", "elegant", "compact")
TemplateName = Literal["professional", "studio", "sidebar", "noir", "swiss", "classic", "modern", "minimal", "bold", "elegant", "compact"]


class Party(BaseModel):
    name: str = Field(min_length=1)
    address: str = Field(min_length=1, description="Multi-line allowed (use \\n)")
    email: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None


class LineItem(BaseModel):
    description: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class Adjustment(BaseModel):
    """A tax or discount: either a percentage of the base or a fixed amount."""

    type: Literal["percent", "amount"] = "percent"
    value: Decimal = Field(default=Decimal(0), ge=0)

    @model_validator(mode="after")
    def _pct_cap(self):
        if self.type == "percent" and self.value > 100:
            raise ValueError("percent value cannot exceed 100")
        return self


class InvoiceRequest(BaseModel):
    template: TemplateName = "professional"
    invoice_number: Optional[str] = None
    currency: str = "$"
    biller: Party
    client: Party
    items: list[LineItem] = Field(min_length=1)
    tax: Adjustment = Field(default_factory=Adjustment)
    discount: Adjustment = Field(default_factory=Adjustment)
    issue_date: date
    due_date: date
    notes: Optional[str] = None
    payment_details: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def _cur(cls, v: str) -> str:
        return v.strip() or "$"

    @model_validator(mode="after")
    def _dates(self):
        if self.due_date < self.issue_date:
            raise ValueError("due_date must not be before issue_date")
        return self
