"""Ledger layout: a navy masthead, a boxed item table with totals inside it, and a payment box."""
import io
from typing import Optional

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from ..calc import Totals
from ..models import InvoiceRequest
from .base import H, M, W, Ctx, Style, adj_label, money, qty_fmt, safe, text, wrap
from .layout import Y, initials, rule, terms, tracked

DESCRIPTION = "Navy masthead, a boxed ledger table with totals inside it, and a payment details box."

NAVY = HexColor("#1f2a37")
INK = HexColor("#1b2430")
BODY = HexColor("#414c59")
MUTED = HexColor("#78838f")
LIGHT = HexColor("#a2adb9")
LINE = HexColor("#dce2e8")
TINT = HexColor("#f4f6f8")
HEAD = HexColor("#5d6975")
GRAND_LABEL = HexColor("#bfc9d3")
SANS, SANS_B = "Helvetica", "Helvetica-Bold"

R = W - M
DIV_RATE = R - 204   # left edge of the rate column
DIV_QTY = R - 270    # left edge of the qty column
DIV_AMOUNT = R - 107  # left edge of the amount column
QTY_C = (DIV_QTY + DIV_RATE) / 2
RATE_R = DIV_AMOUNT - 10
PAY_W = 210
TABLE_TOP = 246
CONTENT_LIMIT = 700
LOWER_LIMIT = 760
CONT_TOP = 76


def background(ctx: Ctx) -> None:
    ctx.c.setFillColor(white)
    ctx.c.rect(0, 0, W, H, stroke=0, fill=1)


def masthead(ctx: Ctx) -> None:
    c, inv = ctx.c, ctx.inv
    c.setFillColor(NAVY)
    c.rect(0, Y(110), W, 110, stroke=0, fill=1)
    c.setFillColor(white)
    c.rect(M, Y(68), 31, 31, stroke=0, fill=1)
    text(ctx, initials(inv.biller.name), M + 15.5, Y(56), font=SANS_B, size=11, color=NAVY, align="center")
    text(ctx, inv.biller.name, M + 41, Y(52), font=SANS_B, size=14, color=white)
    addr = ", ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    text(ctx, wrap(addr, SANS, 8.5, 220)[0], M + 41, Y(66), font=SANS, size=8.5, color=LIGHT)

    tracked(ctx, R, 52, "INVOICE", SANS_B, 15, white, 5, align="right")
    tracked(ctx, R, 68, f"{inv.invoice_number or ''} · {inv.currency}", SANS, 9, LIGHT, 0.7, align="right")


def meta(ctx: Ctx) -> None:
    inv = ctx.inv
    gap = 25.5
    span = R - M - 2 * gap
    w1, w2 = span * 1.35 / 2.95, span * 0.8 / 2.95
    xs = [M, M + w1 + gap, M + w1 + gap + w2 + gap]

    tracked(ctx, xs[0], 163, "BILLED TO", SANS_B, 7.5, MUTED, 1.8)
    text(ctx, inv.client.name, xs[0], Y(183), font=SANS_B, size=17, color=INK)
    addr = ", ".join(ln.strip() for ln in inv.client.address.splitlines() if ln.strip())
    for i, ln in enumerate(wrap(addr, SANS, 9.5, 200)[:2]):
        text(ctx, ln, xs[0], Y(197 + i * 13), font=SANS, size=9.5, color=BODY)

    tracked(ctx, xs[1], 163, "ISSUED", SANS_B, 7.5, MUTED, 1.8)
    text(ctx, inv.issue_date.strftime("%d %b %Y"), xs[1], Y(183), font=SANS_B, size=10.5, color=INK)

    tracked(ctx, xs[2], 163, "DUE", SANS_B, 7.5, MUTED, 1.8)
    text(ctx, inv.due_date.strftime("%d %b %Y"), xs[2], Y(183), font=SANS_B, size=10.5, color=INK)
    text(ctx, f"{terms(inv)} · Payment due", xs[2], Y(197), font=SANS, size=8.5, color=MUTED)


def grid(ctx: Ctx, y0: float, y1: float, dividers_to: float) -> None:
    """Outline a table segment; the column dividers stop at dividers_to so summary rows stay open."""
    c = ctx.c
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.rect(M, Y(y1), R - M, y1 - y0, stroke=1, fill=0)
    for x in (DIV_QTY, DIV_RATE, DIV_AMOUNT):
        c.line(x, Y(y0), x, Y(dividers_to))


def new_page(ctx: Ctx) -> float:
    page_number(ctx)
    ctx.c.showPage()
    ctx.page += 1
    background(ctx)
    text(ctx, f"Invoice {ctx.number} (continued)", M, Y(44), font=SANS_B, size=9, color=MUTED)
    rule(ctx, M, R, 52, LINE, 1)
    return CONT_TOP


def page_number(ctx: Ctx) -> None:
    text(ctx, f"{ctx.number}  ·  Page {ctx.page}", W / 2, Y(826), font=SANS, size=7.5, color=MUTED, align="center")


def table_header(ctx: Ctx, top: float) -> float:
    c = ctx.c
    c.setFillColor(TINT)
    c.rect(M, Y(top + 22), R - M, 22, stroke=0, fill=1)
    tracked(ctx, M + 10, top + 15, "DESCRIPTION", SANS_B, 7.5, HEAD, 1.4)
    tracked(ctx, QTY_C, top + 15, "QTY", SANS_B, 7.5, HEAD, 1.4, align="center")
    tracked(ctx, RATE_R, top + 15, "RATE", SANS_B, 7.5, HEAD, 1.4, align="right")
    tracked(ctx, R - 10, top + 15, "AMOUNT", SANS_B, 7.5, HEAD, 1.4, align="right")
    rule(ctx, M, R, top + 22, LINE, 1)
    return top + 22


def items(ctx: Ctx, top: float):
    inv = ctx.inv
    seg_top = top
    top = table_header(ctx, top)
    for n, (item, amount) in enumerate(zip(inv.items, ctx.t.line_totals)):
        paras = safe(item.description).splitlines() or [""]
        title = wrap(paras[0], SANS_B, 11.5, 230)
        detail = wrap("\n".join(paras[1:]), SANS, 8.8, 230) if len(paras) > 1 else []
        last = 30 + 12 * (len(title) - 1) + (14 + 11 * (len(detail) - 1) if detail else 0)
        h = last + 20
        if top + h > CONTENT_LIMIT:
            grid(ctx, seg_top, top, top)
            top = new_page(ctx)
            seg_top = top
            top = table_header(ctx, top)
        base = top + 30
        for ln in title:
            text(ctx, ln, M + 10, Y(base), font=SANS_B, size=11.5, color=INK)
            base += 12
        if detail:
            base += 2
        for ln in detail:
            text(ctx, ln, M + 10, Y(base), font=SANS, size=8.8, color=MUTED)
            base += 11
        text(ctx, qty_fmt(item.quantity), QTY_C, Y(top + 30), font=SANS, size=10.5, color=BODY, align="center")
        text(ctx, money(inv, item.unit_price), RATE_R, Y(top + 30), font=SANS, size=10.5, color=BODY, align="right")
        text(ctx, money(inv, amount), R - 10, Y(top + 30), font=SANS_B, size=10.5, color=INK, align="right")
        rule(ctx, M, R, top + h, LINE, 0.6)
        top += h
    return top, seg_top


def summary(ctx: Ctx, top: float, seg_top: float, items_end: float) -> float:
    inv, t = ctx.inv, ctx.t
    rows = [("Subtotal", money(inv, t.subtotal), INK)]
    if t.discount > 0:
        rows.append((adj_label("Discount", inv.discount), "-" + money(inv, t.discount), NAVY))
    if t.tax > 0:
        rows.append((adj_label("Tax", inv.tax), money(inv, t.tax), INK))
    need = 24 * len(rows) + 40
    if top + need > CONTENT_LIMIT:
        grid(ctx, seg_top, top, items_end)
        top = new_page(ctx)
        seg_top = top
        items_end = top

    for label, value, color in rows:
        rule(ctx, M, R, top, LINE, 0.6)
        text(ctx, label, RATE_R, Y(top + 16), font=SANS, size=10, color=BODY, align="right")
        text(ctx, value, R - 10, Y(top + 16), font=SANS_B, size=10, color=color, align="right")
        top += 24
    ctx.c.setFillColor(NAVY)
    ctx.c.rect(M, Y(top + 40), R - M, 40, stroke=0, fill=1)
    tracked(ctx, M + 10, top + 25, "TOTAL DUE", SANS_B, 8, GRAND_LABEL, 2)
    text(ctx, money(inv, t.total), R - 10, Y(top + 27), font=SANS_B, size=18, color=white, align="right")
    top += 40
    grid(ctx, seg_top, top, items_end)
    return top


def lower(ctx: Ctx, top: float) -> float:
    inv = ctx.inv
    notes = [(lab, body) for lab, body in (("NOTES", inv.notes), ("PAYMENT DETAILS", inv.payment_details)) if body]
    notes_w = R - M - PAY_W - 28
    notes_h = sum(16 + 15 * len(wrap(body, SANS, 9, notes_w)) + 12 for _, body in notes)
    pay_h = 100
    top += 26
    if top + max(notes_h, pay_h) > LOWER_LIMIT:
        top = new_page(ctx)

    base = top + 8
    for label, body in notes:
        tracked(ctx, M, base, label, SANS_B, 7.5, MUTED, 1.8)
        base += 16
        for ln in wrap(body, SANS, 9, notes_w):
            text(ctx, ln, M, Y(base), font=SANS, size=9, color=BODY)
            base += 15
        base += 12

    x0 = R - PAY_W
    ctx.c.setFillColor(TINT)
    ctx.c.setStrokeColor(LINE)
    ctx.c.setLineWidth(1)
    ctx.c.rect(x0, Y(top + pay_h), PAY_W, pay_h, stroke=1, fill=1)
    tracked(ctx, x0 + 17, top + 25, "PAYMENT DETAILS", SANS_B, 7.5, MUTED, 1.8)
    rows = [("Currency", inv.currency), ("Reference", inv.invoice_number or "-"),
            ("Terms", terms(inv)), ("Due date", inv.due_date.strftime("%d %b %Y"))]
    for i, (label, value) in enumerate(rows):
        b = top + 46 + i * 15
        text(ctx, label, x0 + 17, Y(b), font=SANS, size=9.5, color=MUTED)
        text(ctx, value, R - 17, Y(b), font=SANS_B, size=9.5, color=INK, align="right")
    return max(base, top + pay_h)


def footer(ctx: Ctx) -> None:
    inv = ctx.inv
    rule(ctx, M, R, 774, LINE, 1)
    text(ctx, "Thank you for your business.", M, Y(794), font=SANS, size=9, color=BODY)
    addr = " · ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    tracked(ctx, R, 790, f"{inv.biller.name} · {addr}".upper(), SANS, 8, MUTED, 1.2, align="right")
    tracked(ctx, R, 804, f"Invoice {inv.invoice_number or ''}".upper(), SANS, 8, MUTED, 1.2, align="right")


def render(inv: InvoiceRequest, totals: Totals, logo: Optional[ImageReader]) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    c.setTitle(f"Invoice {inv.invoice_number}")
    c.setAuthor(safe(inv.biller.name))
    style = Style(font=SANS, bold=SANS_B, size=9.5, text=BODY, muted=MUTED, line=LINE, accent=NAVY)
    ctx = Ctx(c, inv, totals, logo, style)
    background(ctx)
    masthead(ctx)
    meta(ctx)
    top, seg_top = items(ctx, TABLE_TOP)
    top = summary(ctx, top, seg_top, top)
    top = lower(ctx, top)
    footer(ctx)
    if ctx.page > 1:
        page_number(ctx)
    c.save()
    return buf.getvalue()
