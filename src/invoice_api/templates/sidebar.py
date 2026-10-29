"""Sidebar layout: a dark panel with the invoice details and a cream ledger with numbered items."""
import io
from typing import Optional

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from ..calc import Totals
from ..models import InvoiceRequest
from .base import H, M, W, Ctx, Style, adj_label, draw_logo, money, qty_fmt, safe, text, wrap
from .layout import Y, initials, rule, terms, tracked, tracked_width

DESCRIPTION = "Dark sidebar with the invoice details, and a cream ledger with numbered line items."

PANEL_W = 191
PANEL = HexColor("#111316")
PANEL_LINE = HexColor("#2b2f36")
PANEL_MUTED = HexColor("#8b9099")
ORANGE = HexColor("#e8982e")
CREAM = HexColor("#fcf9f2")
INK = HexColor("#15171a")
BODY = HexColor("#3d3d3d")
MUTED = HexColor("#8b8f96")
ROW_LINE = HexColor("#e6e0d2")
SANS, SANS_B = "Helvetica", "Helvetica-Bold"
MONO = "Courier"

LEFT = 226  # left edge of the cream content area
RIGHT = 558  # right edge of the cream content area
DESC_X = 252
DESC_W = 140
QTY_X, RATE_X = 413, 489
NOTES_W = 150
TOTALS_X = 397
CONTENT_LIMIT = 790
CONT_TOP = 76


def background(ctx: Ctx) -> None:
    c = ctx.c
    c.setFillColor(CREAM)
    c.rect(PANEL_W, 0, W - PANEL_W, H, stroke=0, fill=1)
    c.setFillColor(PANEL)
    c.rect(0, 0, PANEL_W, H, stroke=0, fill=1)


def panel(ctx: Ctx) -> None:
    c, inv = ctx.c, ctx.inv
    lh = draw_logo(ctx, 30, Y(40), max_w=30, max_h=30)
    if not lh:
        c.setFillColor(ORANGE)
        c.roundRect(30, Y(70), 30, 30, 6, stroke=0, fill=1)
        text(ctx, initials(inv.biller.name), 45, Y(59), font=SANS_B, size=11, color=INK, align="center")
    text(ctx, inv.biller.name, 70, Y(56), font=SANS_B, size=12.5, color=white)
    addr = ", ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    for i, ln in enumerate(wrap(addr, SANS, 8, 100)[:2]):
        text(ctx, ln, 70, Y(68 + i * 11), font=SANS, size=8, color=PANEL_MUTED)

    c.setStrokeColor(PANEL_LINE)
    c.setLineWidth(0.6)
    c.line(30, Y(100), 161, Y(100))

    text(ctx, "INVOICE", 30, Y(146), font=SANS_B, size=24, color=white)
    meta = " · ".join(v for v in (inv.invoice_number, inv.currency) if v)
    tracked(ctx, 30, 162, meta, SANS, 8, PANEL_MUTED, 0.8)

    rows = [("Issued", inv.issue_date.strftime("%d %b %Y")),
            ("Due", inv.due_date.strftime("%d %b %Y")),
            ("Terms", terms(inv))]
    for i, (label, value) in enumerate(rows):
        base = 206 + i * 27
        text(ctx, label, 30, Y(base), font=SANS, size=8.5, color=PANEL_MUTED)
        text(ctx, value, 161, Y(base), font=SANS_B, size=8.5, color=white, align="right")
        c.setStrokeColor(PANEL_LINE)
        c.line(30, Y(base + 8), 161, Y(base + 8))

    label = "PAYMENT DUE"
    pw = tracked_width(label, SANS_B, 7, 1.6) + 32
    c.setStrokeColor(ORANGE)
    c.setLineWidth(0.8)
    c.roundRect(30, Y(330), pw, 20, 3, stroke=1, fill=0)
    c.setFillColor(ORANGE)
    c.circle(41, Y(320), 2.5, stroke=0, fill=1)
    tracked(ctx, 50, 323.5, label, SANS_B, 7, ORANGE, 1.6)


def continuation_header(ctx: Ctx) -> None:
    text(ctx, f"Invoice {ctx.number} (continued)", LEFT, Y(44), font=SANS_B, size=9, color=MUTED)
    rule(ctx, LEFT, RIGHT, 52, ROW_LINE)


def new_page(ctx: Ctx) -> float:
    page_number(ctx)
    ctx.c.showPage()
    ctx.page += 1
    background(ctx)
    panel(ctx)
    continuation_header(ctx)
    return CONT_TOP


def page_number(ctx: Ctx) -> None:
    text(ctx, f"{ctx.number}  ·  Page {ctx.page}", (PANEL_W + RIGHT) / 2, Y(826), font=SANS, size=7.5,
         color=MUTED, align="center")


def billed_to(ctx: Ctx) -> None:
    inv = ctx.inv
    tracked(ctx, LEFT, 52, "BILLED TO", SANS_B, 6.5, MUTED, 1.6)
    t = 80
    for ln in wrap(inv.client.name, SANS_B, 18, 220):
        text(ctx, ln, LEFT, Y(t), font=SANS_B, size=18, color=INK)
        t += 22
    lines = wrap(inv.client.address, SANS, 9.5, 220)
    for extra in (inv.client.email, inv.client.phone, f"Tax ID: {inv.client.tax_id}" if inv.client.tax_id else None):
        if extra:
            lines.extend(wrap(extra, SANS, 9.5, 220))
    for ln in lines:
        text(ctx, ln, LEFT, Y(t + 4), font=SANS, size=9.5, color=BODY)
        t += 14
    tracked(ctx, RIGHT, 52, "ISSUE DATE", SANS_B, 6.5, MUTED, 1.6, align="right")
    text(ctx, inv.issue_date.strftime("%d %b %Y"), RIGHT, Y(76), font=SANS_B, size=13, color=INK, align="right")


def table_header(ctx: Ctx, top: float) -> float:
    rule(ctx, LEFT, RIGHT, top, INK, 2.2)
    base = top + 17
    tracked(ctx, LEFT, base, "#", SANS_B, 7, INK, 1.4)
    tracked(ctx, DESC_X, base, "DESCRIPTION", SANS_B, 7, INK, 1.6)
    tracked(ctx, QTY_X, base, "QTY", SANS_B, 7, INK, 1.6, align="center")
    tracked(ctx, RATE_X, base, "RATE", SANS_B, 7, INK, 1.6, align="right")
    tracked(ctx, RIGHT, base, "AMOUNT", SANS_B, 7, INK, 1.6, align="right")
    return top + 22


def items(ctx: Ctx, top: float) -> float:
    inv = ctx.inv
    top = table_header(ctx, top)
    for n, (item, amount) in enumerate(zip(inv.items, ctx.t.line_totals)):
        paras = safe(item.description).splitlines() or [""]
        title = wrap(paras[0], SANS_B, 9.5, DESC_W)
        detail = wrap("\n".join(paras[1:]), SANS, 8.5, DESC_W) if len(paras) > 1 else []
        last = 22 + 12 * (len(title) - 1) + (14 + 12 * (len(detail) - 1) if detail else 0)
        h = max(40, last + 14)
        if top + h > CONTENT_LIMIT:
            top = table_header(ctx, new_page(ctx))
        base = top + 22
        # The number shares the title's baseline, so the two always line up.
        text(ctx, f"{n + 1:02d}", LEFT, Y(base), font=MONO, size=8, color=MUTED)
        for ln in title:
            text(ctx, ln, DESC_X, Y(base), font=SANS_B, size=9.5, color=INK)
            base += 12
        if detail:
            base += 2
        for ln in detail:
            text(ctx, ln, DESC_X, Y(base), font=SANS, size=8.5, color=MUTED)
            base += 12
        text(ctx, qty_fmt(item.quantity), QTY_X, Y(top + 22), font=SANS, size=9.5, color=BODY, align="center")
        text(ctx, money(inv, item.unit_price), RATE_X, Y(top + 22), font=SANS, size=9.5, color=BODY, align="right")
        text(ctx, money(inv, amount), RIGHT, Y(top + 22), font=SANS_B, size=9.5, color=INK, align="right")
        rule(ctx, LEFT, RIGHT, top + h, ROW_LINE, 0.6)
        top += h
    return top


def summary(ctx: Ctx, top: float) -> float:
    inv, t = ctx.inv, ctx.t
    notes = [(lab, body) for lab, body in (("NOTES", inv.notes), ("PAYMENT DETAILS", inv.payment_details)) if body]
    notes_h = sum(16 + 12 * len(wrap(body, SANS, 8.5, NOTES_W)) + 14 for _, body in notes)
    rows = [("Subtotal", money(inv, t.subtotal), INK)]
    if t.discount > 0:
        rows.append((adj_label("Discount", inv.discount), "-" + money(inv, t.discount), ORANGE))
    if t.tax > 0:
        rows.append((adj_label("Tax", inv.tax), money(inv, t.tax), INK))
    totals_h = 14 + 17 * (len(rows) - 1) + 9 + 42 + 8
    if top + 40 + max(notes_h, totals_h) > CONTENT_LIMIT:
        top = new_page(ctx)
    label_top = top + 40

    base = label_top
    for label, body in notes:
        tracked(ctx, LEFT, base, label, SANS_B, 6.5, MUTED, 1.5)
        base += 16
        for ln in wrap(body, SANS, 8.5, NOTES_W):
            text(ctx, ln, LEFT, Y(base), font=SANS, size=8.5, color=BODY)
            base += 12
        base += 14

    row_base = label_top + 14
    for label, value, color in rows:
        text(ctx, label, TOTALS_X, Y(row_base), font=SANS, size=9.5, color=MUTED)
        text(ctx, value, RIGHT, Y(row_base), font=SANS_B, size=9.5, color=color, align="right")
        row_base += 17
    rl = row_base - 9
    rule(ctx, TOTALS_X, RIGHT, rl, INK, 1.2)
    tracked(ctx, RIGHT, rl + 18, "TOTAL DUE", SANS_B, 7, MUTED, 1.6, align="right")
    text(ctx, money(inv, t.total), RIGHT, Y(rl + 42), font=SANS_B, size=24, color=INK, align="right")
    return max(base, rl + 42)


def render(inv: InvoiceRequest, totals: Totals, logo: Optional[ImageReader]) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    c.setTitle(f"Invoice {inv.invoice_number}")
    c.setAuthor(safe(inv.biller.name))
    style = Style(font=SANS, bold=SANS_B, size=9.5, text=BODY, muted=MUTED, line=ROW_LINE, accent=ORANGE)
    ctx = Ctx(c, inv, totals, logo, style)
    background(ctx)
    panel(ctx)
    billed_to(ctx)
    top = items(ctx, 200)
    summary(ctx, top + 26)
    if ctx.page > 1:
        page_number(ctx)
    c.save()
    return buf.getvalue()
