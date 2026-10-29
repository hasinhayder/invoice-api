"""Swiss layout: a large black title, a boxed meta grid and a black total block on white."""
import io
from decimal import Decimal
from typing import Optional

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from ..calc import Totals
from ..models import InvoiceRequest
from .base import H, M, W, Ctx, Style, adj_label, draw_logo, money, qty_fmt, safe, text, wrap
from .layout import Y, rule, terms, tracked

DESCRIPTION = "Black and white: a large title, a boxed details grid and a black total block."

INK = HexColor("#000000")
BODY = HexColor("#333333")
GRAY = HexColor("#6b6b6b")
LINE = HexColor("#d8d8d8")
SANS, SANS_B = "Helvetica", "Helvetica-Bold"

R = W - M
QTY_C = 308
RATE_R = 441
SUMMARY_W = 204
CONTENT_LIMIT = 664
CONT_TOP = 60

_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
         "sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else "-" + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + _words(n % 100))
    for value, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (10 ** 3, "thousand")):
        if n >= value:
            return _words(n // value) + " " + name + ("" if n % value == 0 else " " + _words(n % value))
    return str(n)


def amount_words(inv: InvoiceRequest, amount: Decimal) -> str:
    whole = int(amount)
    cents = int(round((amount - whole) * 100))
    name = "US dollars" if inv.currency.upper() in ("USD", "$") else inv.currency
    s = f"{_words(whole).capitalize()} {name}"
    if cents:
        s += f" and {cents:02d}/100"
    return s + " only"


def background(ctx: Ctx) -> None:
    ctx.c.setFillColor(white)
    ctx.c.rect(0, 0, W, H, stroke=0, fill=1)


def page_number(ctx: Ctx) -> None:
    text(ctx, f"{ctx.number}  ·  Page {ctx.page}", W / 2, Y(826), font=SANS, size=7.5, color=GRAY, align="center")


def new_page(ctx: Ctx) -> float:
    page_number(ctx)
    ctx.c.showPage()
    ctx.page += 1
    background(ctx)
    text(ctx, f"Invoice {ctx.number} (continued)", M, Y(44), font=SANS_B, size=8, color=INK)
    rule(ctx, M, R, 52, INK, 1)
    return CONT_TOP


def header(ctx: Ctx) -> None:
    inv = ctx.inv
    lh = draw_logo(ctx, M, Y(40), max_w=36, max_h=36)
    x = M + 50 if lh else M
    tracked(ctx, x, 58, inv.biller.name.upper(), SANS_B, 13, INK, 0.6)
    addr = ", ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    text(ctx, wrap(addr, SANS, 9, 220)[0], x, Y(72), font=SANS, size=9, color=GRAY)
    tracked(ctx, R, 56, inv.invoice_number or "", SANS_B, 9, INK, 1, align="right")
    tracked(ctx, R, 70, f"{inv.currency} · {terms(inv)}".upper(), SANS, 9, INK, 1, align="right")
    rule(ctx, M, R, 83, INK, 1)

    tracked(ctx, M, 162, "INVOICE", SANS_B, 66, INK, -3)
    tracked(ctx, R, 146, "Original for recipient", SANS, 8, GRAY, 2, align="right")
    tracked(ctx, R, 160, f"Currency · {inv.currency}", SANS, 8, GRAY, 2, align="right")


def details(ctx: Ctx) -> None:
    inv = ctx.inv
    c = ctx.c
    top, height = 186, 90
    c.setStrokeColor(INK)
    c.setLineWidth(1.5)
    c.rect(M, Y(top + height), R - M, height, stroke=1, fill=0)
    c.line(M + 178, Y(top), M + 178, Y(top + height))
    c.line(M + 356, Y(top), M + 356, Y(top + height))

    cols = [(M + 14, "FROM", inv.biller), (M + 192, "BILLED TO", inv.client)]
    for x, label, p in cols:
        tracked(ctx, x, top + 14, label, SANS_B, 7.5, INK, 2)
        text(ctx, p.name, x, Y(top + 30), font=SANS_B, size=12, color=INK)
        addr = ", ".join(ln.strip() for ln in p.address.splitlines() if ln.strip())
        for i, ln in enumerate(wrap(addr, SANS, 9.5, 150)[:2]):
            text(ctx, ln, x, Y(top + 44 + i * 12), font=SANS, size=9.5, color=BODY)

    x = M + 370
    tracked(ctx, x, top + 14, "DETAILS", SANS_B, 7.5, INK, 2)
    rows = [("Issued", inv.issue_date.strftime("%d %b %Y")),
            ("Due", inv.due_date.strftime("%d %b %Y")),
            ("Terms", terms(inv)),
            ("Status", "Due")]
    for i, (label, value) in enumerate(rows):
        base = top + 32 + i * 14
        text(ctx, label, x, Y(base), font=SANS, size=9, color=GRAY)
        text(ctx, value, R - 14, Y(base), font=SANS_B, size=9, color=INK, align="right")


def table_header(ctx: Ctx, top: float) -> float:
    base = top + 12
    tracked(ctx, M, base, "DESCRIPTION", SANS_B, 7.5, INK, 1.8)
    tracked(ctx, QTY_C, base, "QTY", SANS_B, 7.5, INK, 1.8, align="center")
    tracked(ctx, RATE_R, base, "RATE", SANS_B, 7.5, INK, 1.8, align="right")
    tracked(ctx, R, base, "AMOUNT", SANS_B, 7.5, INK, 1.8, align="right")
    rule(ctx, M, R, top + 18, INK, 2.5)
    return top + 20


def items(ctx: Ctx, top: float) -> float:
    inv = ctx.inv
    top = table_header(ctx, top)
    for item, amount in zip(inv.items, ctx.t.line_totals):
        paras = safe(item.description).splitlines() or [""]
        title = wrap(paras[0], SANS_B, 12, 290)
        detail = wrap("\n".join(paras[1:]), SANS, 9, 290) if len(paras) > 1 else []
        h = 30 + 12 * (len(title) - 1) + (13 + 11 * (len(detail) - 1) if detail else 0) + 20
        if top + h > CONTENT_LIMIT:
            top = table_header(ctx, new_page(ctx))
        base = top + 30
        for ln in title:
            text(ctx, ln, M, Y(base), font=SANS_B, size=12, color=INK)
            base += 12
        if detail:
            base += 1
        for ln in detail:
            text(ctx, ln, M, Y(base), font=SANS, size=9, color=GRAY)
            base += 11
        text(ctx, qty_fmt(item.quantity), QTY_C, Y(top + 30), font=SANS, size=10.5, color=INK, align="center")
        text(ctx, money(inv, item.unit_price), RATE_R, Y(top + 30), font=SANS, size=10.5, color=INK, align="right")
        text(ctx, money(inv, amount), R, Y(top + 30), font=SANS_B, size=10.5, color=INK, align="right")
        rule(ctx, M, R, top + h, LINE, 1)
        top += h
    return top


def summary(ctx: Ctx, top: float) -> float:
    c, inv, t = ctx.c, ctx.inv, ctx.t
    notes = [(lab, body) for lab, body in (("NOTES", inv.notes), ("PAYMENT DETAILS", inv.payment_details)) if body]
    notes_h = sum(16 + 13 * len(wrap(body, SANS, 9, 290)) + 12 for _, body in notes)
    rows = [("Subtotal", money(inv, t.subtotal), INK)]
    if t.discount > 0:
        rows.append((adj_label("Discount", inv.discount), "-" + money(inv, t.discount), INK))
    if t.tax > 0:
        rows.append((adj_label("Tax", inv.tax), money(inv, t.tax), INK))
    totals_h = 18 * len(rows) + 6 + 60
    if top + 22 + max(notes_h, totals_h) > CONTENT_LIMIT:
        top = new_page(ctx)
    y = top + 22

    base = y
    for label, body in notes:
        tracked(ctx, M, base, label, SANS_B, 7.5, INK, 1.8)
        base += 16
        for ln in wrap(body, SANS, 9, 290):
            text(ctx, ln, M, Y(base), font=SANS, size=9, color=BODY)
            base += 13
        base += 12

    x0 = R - SUMMARY_W
    row_base = y + 12
    for label, value, color in rows:
        tracked(ctx, x0, row_base, label.upper(), SANS, 8, GRAY, 0.8)
        text(ctx, value, R, Y(row_base), font=SANS_B, size=10, color=color, align="right")
        row_base += 18
    box_top = row_base + 6
    c.setFillColor(INK)
    c.rect(x0, Y(box_top + 60), SUMMARY_W, 60, stroke=0, fill=1)
    tracked(ctx, x0 + 16, box_top + 24, "TOTAL DUE", SANS_B, 8, white, 2)
    text(ctx, money(inv, t.total), R - 16, Y(box_top + 46), font=SANS_B, size=24, color=white, align="right")
    return max(base, box_top + 60)


def footer(ctx: Ctx) -> None:
    inv, c = ctx.inv, ctx.c
    c.setStrokeColor(INK)
    c.setLineWidth(1.5)
    c.rect(M, Y(744), R - M, 44, stroke=1, fill=0)
    c.line(M + 315, Y(700), M + 315, Y(744))
    tracked(ctx, M + 14, 714, "AMOUNT IN WORDS", SANS_B, 7.5, INK, 1.8)
    text(ctx, amount_words(inv, ctx.t.total), M + 14, Y(730), font=SANS, size=9.5, color=BODY)
    tracked(ctx, M + 329, 714, "PAYMENT", SANS_B, 7.5, INK, 1.8)
    text(ctx, f"Due {inv.due_date.strftime('%d %b %Y')} · {terms(inv)}", M + 329, Y(730), font=SANS, size=9.5, color=BODY)
    rule(ctx, M, R, 762, INK, 1.5)
    tracked(ctx, M, 784, "THANK YOU FOR YOUR BUSINESS", SANS_B, 8.5, INK, 1.6)
    addr = " · ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    tracked(ctx, R, 778, inv.biller.name.upper(), SANS, 8, GRAY, 1.4, align="right")
    tracked(ctx, R, 792, addr.upper(), SANS, 8, GRAY, 1.4, align="right")


def render(inv: InvoiceRequest, totals: Totals, logo: Optional[ImageReader]) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    c.setTitle(f"Invoice {inv.invoice_number}")
    c.setAuthor(safe(inv.biller.name))
    style = Style(font=SANS, bold=SANS_B, size=9.5, text=BODY, muted=GRAY, line=LINE, accent=INK)
    ctx = Ctx(c, inv, totals, logo, style)
    background(ctx)
    header(ctx)
    details(ctx)
    top = items(ctx, 290)
    summary(ctx, top)
    footer(ctx)
    if ctx.page > 1:
        page_number(ctx)
    c.save()
    return buf.getvalue()
