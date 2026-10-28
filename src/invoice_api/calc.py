from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .models import Adjustment, InvoiceRequest

CENT = Decimal("0.01")


def q(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass
class Totals:
    line_totals: list[Decimal]
    subtotal: Decimal
    discount: Decimal
    taxable: Decimal
    tax: Decimal
    total: Decimal


def _amount(adj: Adjustment, base: Decimal) -> Decimal:
    if adj.type == "percent":
        return q(base * adj.value / 100)
    return q(adj.value)


def compute(inv: InvoiceRequest) -> Totals:
    lines = [q(i.quantity * i.unit_price) for i in inv.items]
    subtotal = sum(lines, Decimal(0))
    discount = min(_amount(inv.discount, subtotal), subtotal)
    taxable = subtotal - discount
    tax = _amount(inv.tax, taxable)
    return Totals(lines, subtotal, discount, taxable, tax, taxable + tax)
