"""Noir layout: a dark page with a lime accent, numbered items and a lime total block."""
import io
from typing import Optional

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from ..calc import Totals
from ..models import InvoiceRequest
from .base import H, M, W, Ctx, Style, adj_label, money, qty_fmt, safe, text, wrap
from .layout import Y, initials, rule, terms, tracked

DESCRIPTION = "Dark page with a lime accent, numbered line items and a lime total block."

BG = HexColor("#0a0b0d")
LINE = HexColor("#22262d")
WHITE = HexColor("#f5f7f9")
SOFT = HexColor("#e6e9ec")
GRAY = HexColor("#9aa1ab")
DIM = HexColor("#6d747e")
LIME = HexColor("#d4ff4f")
INK = HexColor("#0a0b0d")
SANS, SANS_B = "Helvetica", "Helvetica-Bold"
MONO = "Courier"

R = W - M
DESC_X = M + 41
QTY_C = 363
RATE_R = 453
SUMMARY_W = 198
CONTENT_LIMIT = 700
CONT_TOP = 60


def background(ctx: Ctx) -> None:
    ctx.c.setFillColor(BG)
    ctx.c.rect(0, 0, W, H, stroke=0, fill=1)


def page_number(ctx: Ctx) -> None:
    text(ctx, f"{ctx.number}  ·  Page {ctx.page}", W / 2, Y(826), font=SANS, size=7.5, color=DIM, align="center")


def new_page(ctx: Ctx) -> float:
    page_number(ctx)
    ctx.c.showPage()
    ctx.page += 1
    background(ctx)
    text(ctx, f"Invoice {ctx.number} (continued)", M, Y(40), font=SANS_B, size=8, color=DIM)
    rule(ctx, M, R, 50, LINE)
    return CONT_TOP


def header(ctx: Ctx) -> None:
    c, inv = ctx.c, ctx.inv
    c.setFillColor(LIME)
    c.roundRect(M, Y(76), 34, 34, 9, stroke=0, fill=1)
    text(ctx, initials(inv.biller.name), M + 17, Y(63), font=SANS_B, size=12, color=INK, align="center")
    text(ctx, inv.biller.name, M + 44, Y(56), font=SANS_B, size=14, color=WHITE)
    addr = ", ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    text(ctx, wrap(addr, SANS, 8.5, 220)[0], M + 44, Y(70), font=SANS, size=8.5, color=GRAY)

    tracked(ctx, R, 50, "INVOICE", SANS_B, 8, LIME, 4, align="right")
    text(ctx, inv.invoice_number or "", R, Y(72), font=SANS_B, size=22, color=WHITE, align="right")
    text(ctx, f"{inv.currency} · {terms(inv)}", R, Y(86), font=SANS, size=9, color=GRAY, align="right")
    rule(ctx, M, R, 100, LINE)


def meta(ctx: Ctx) -> None:
    inv = ctx.inv
    xs = [M, M + 183, M + 299, M + 415]
    widths = [163, 96, 96, 96]
    for x, w in zip(xs, widths):
        rule(ctx, x, x + w, 108, LINE)

    tracked(ctx, xs[0], 122, "BILLED TO", SANS_B, 6.5, DIM, 1.8)
    text(ctx, inv.client.name, xs[0], Y(140), font=SANS_B, size=15, color=WHITE)
    addr = ", ".join(ln.strip() for ln in inv.client.address.splitlines() if ln.strip())
    for i, ln in enumerate(wrap(addr, SANS, 9, 160)[:2]):
        text(ctx, ln, xs[0], Y(154 + i * 12), font=SANS, size=9, color=GRAY)

    tracked(ctx, xs[1], 122, "ISSUED", SANS_B, 6.5, DIM, 1.8)
    text(ctx, inv.issue_date.strftime("%d %b %Y"), xs[1], Y(140), font=SANS_B, size=10, color=SOFT)
    tracked(ctx, xs[2], 122, "DUE", SANS_B, 6.5, DIM, 1.8)
    text(ctx, inv.due_date.strftime("%d %b %Y"), xs[2], Y(140), font=SANS_B, size=10, color=SOFT)
    tracked(ctx, xs[3], 122, "STATUS", SANS_B, 6.5, DIM, 1.8)
    text(ctx, "Payment due", xs[3], Y(140), font=SANS_B, size=10, color=LIME)


def table_header(ctx: Ctx, top: float) -> float:
    rule(ctx, M, R, top, LIME, 2)
    base = top + 14
    tracked(ctx, M, base, "#", SANS_B, 7.5, DIM, 1.6)
    tracked(ctx, DESC_X, base, "DESCRIPTION", SANS_B, 7.5, DIM, 1.6)
    tracked(ctx, QTY_C, base, "QTY", SANS_B, 7.5, DIM, 1.6, align="center")
    tracked(ctx, RATE_R, base, "RATE", SANS_B, 7.5, DIM, 1.6, align="right")
    tracked(ctx, R, base, "AMOUNT", SANS_B, 7.5, DIM, 1.6, align="right")
    rule(ctx, M, R, top + 21, LINE, 1)
    return top + 21


def items(ctx: Ctx, top: float) -> float:
    inv = ctx.inv
    top = table_header(ctx, top)
    for n, (item, amount) in enumerate(zip(inv.items, ctx.t.line_totals)):
        paras = safe(item.description).splitlines() or [""]
        title = wrap(paras[0], SANS_B, 12.5, 250)
        detail = wrap("\n".join(paras[1:]), SANS, 9, 250) if len(paras) > 1 else []
        h = 30 + 12 * (len(title) - 1) + (13 + 11 * (len(detail) - 1) if detail else 0) + 21
        if top + h > CONTENT_LIMIT:
            top = table_header(ctx, new_page(ctx))
        text(ctx, f"{n + 1:02d}", M, Y(top + 30), font=MONO, size=8.5, color=LIME)
        base = top + 30
        for ln in title:
            text(ctx, ln, DESC_X, Y(base), font=SANS_B, size=12.5, color=WHITE)
            base += 12
        if detail:
            base += 1
        for ln in detail:
            text(ctx, ln, DESC_X, Y(base), font=SANS, size=9, color=GRAY)
            base += 11
        text(ctx, qty_fmt(item.quantity), QTY_C, Y(top + 30), font=SANS, size=10.5, color=SOFT, align="center")
        text(ctx, money(inv, item.unit_price), RATE_R, Y(top + 30), font=SANS, size=10.5, color=GRAY, align="right")
        text(ctx, money(inv, amount), R, Y(top + 30), font=SANS_B, size=10.5, color=WHITE, align="right")
        rule(ctx, M, R, top + h, LINE, 1)
        top += h
    return top


def summary(ctx: Ctx, top: float) -> float:
    c, inv, t = ctx.c, ctx.inv, ctx.t
    notes = [(lab, body) for lab, body in (("NOTES", inv.notes), ("PAYMENT DETAILS", inv.payment_details)) if body]
    notes_h = sum(18 + 15 * len(wrap(body, SANS, 9, 290)) + 12 for _, body in notes)
    rows = [("Subtotal", money(inv, t.subtotal), SOFT)]
    if t.discount > 0:
        rows.append((adj_label("Discount", inv.discount), "-" + money(inv, t.discount), LIME))
    if t.tax > 0:
        rows.append((adj_label("Tax", inv.tax), money(inv, t.tax), SOFT))
    totals_h = 18 * len(rows) + 6 + 64
    if top + 24 + max(notes_h, totals_h) > CONTENT_LIMIT:
        top = new_page(ctx)
    y = top + 24

    base = y
    for label, body in notes:
        tracked(ctx, M, base, label, SANS_B, 6.5, DIM, 1.6)
        base += 16
        for ln in wrap(body, SANS, 9, 290):
            text(ctx, ln, M, Y(base), font=SANS, size=9, color=GRAY)
            base += 15
        base += 12

    x0 = R - SUMMARY_W
    row_base = y + 12
    for label, value, color in rows:
        text(ctx, label, x0, Y(row_base), font=SANS, size=10.5, color=GRAY)
        text(ctx, value, R, Y(row_base), font=SANS_B, size=10.5, color=color, align="right")
        row_base += 18
    box_top = row_base + 6
    c.setFillColor(LIME)
    c.roundRect(x0, Y(box_top + 64), SUMMARY_W, 64, 12, stroke=0, fill=1)
    tracked(ctx, x0 + 16, box_top + 22, "TOTAL DUE", SANS_B, 7.5, INK, 2)
    text(ctx, money(inv, t.total), x0 + 16, Y(box_top + 50), font=SANS_B, size=26, color=INK)
    return max(base, box_top + 64)


def footer(ctx: Ctx) -> None:
    inv = ctx.inv
    rule(ctx, M, R, 728, LINE)
    cols = [
        (M, "CURRENCY", inv.currency),
        (M + 171, "REFERENCE", inv.invoice_number or "-"),
        (M + 342, "PAYMENT TERMS", terms(inv)),
    ]
    for x, label, value in cols:
        tracked(ctx, x, 744, label, SANS_B, 6.5, DIM, 1.8)
        text(ctx, value, x, Y(758), font=SANS_B, size=10.5, color=SOFT)
    tracked(ctx, M, 812, "THANK YOU FOR YOUR BUSINESS", SANS, 8.5, GRAY, 1.6)
    addr = " · ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    tracked(ctx, R, 796, inv.biller.name.upper(), SANS_B, 8, DIM, 1.4, align="right")
    tracked(ctx, R, 810, addr.upper(), SANS, 8, DIM, 1.4, align="right")


def render(inv: InvoiceRequest, totals: Totals, logo: Optional[ImageReader]) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    c.setTitle(f"Invoice {inv.invoice_number}")
    c.setAuthor(safe(inv.biller.name))
    style = Style(font=SANS, bold=SANS_B, size=9.5, text=SOFT, muted=GRAY, line=LINE, accent=LIME)
    ctx = Ctx(c, inv, totals, logo, style)
    background(ctx)
    header(ctx)
    meta(ctx)
    top = items(ctx, 170)
    summary(ctx, top + 0)
    footer(ctx)
    if ctx.page > 1:
        page_number(ctx)
    c.save()
    return buf.getvalue()
