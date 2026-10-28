from decimal import Decimal

from invoice_api.calc import compute
from invoice_api.models import InvoiceRequest

BASE = {
    "biller": {"name": "A", "address": "x"},
    "client": {"name": "B", "address": "y"},
    "items": [{"description": "w", "quantity": 3, "unit_price": "10.005"}],
    "issue_date": "2026-01-01",
    "due_date": "2026-01-31",
}


def calc(**kw):
    return compute(InvoiceRequest.model_validate({**BASE, **kw}))


def test_plain():
    t = calc()
    assert t.subtotal == Decimal("30.02") and t.total == Decimal("30.02")


def test_discount_then_tax_percent():
    t = calc(items=[{"description": "w", "quantity": 1, "unit_price": 100}],
             discount={"type": "percent", "value": 10}, tax={"type": "percent", "value": 20})
    assert (t.discount, t.tax, t.total) == (Decimal("10.00"), Decimal("18.00"), Decimal("108.00"))


def test_fixed_amounts_and_discount_capped():
    t = calc(items=[{"description": "w", "quantity": 1, "unit_price": 50}],
             discount={"type": "amount", "value": 80}, tax={"type": "amount", "value": 5})
    assert (t.discount, t.total) == (Decimal("50.00"), Decimal("5.00"))
