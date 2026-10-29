"""Card layout: light info card, dark table header and a full-width balance band."""
import io
from typing import Optional

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas

from ..calc import Totals
from ..models import InvoiceRequest
from .base import H, M, W, Ctx, Style, adj_label, draw_logo, money, qty_fmt, safe, text, wrap
from .layout import Y, initials, rule, terms, tracked, tracked_width

DESCRIPTION = "Card layout: a light info panel, a dark item header and a full-width balance band."

ACCENT = HexColor("#2350e0")
INK = HexColor("#111418")
BODY = HexColor("#3a3f47")
MUTED = HexColor("#6b7280")
CARD = HexColor("#f2f5fa")
CARD_LINE = HexColor("#dfe6f1")
ZEBRA = HexColor("#f8fafc")
ROW_LINE = HexColor("#e6eaf0")
PILL = HexColor("#e3eafd")
BAND_MUTED = HexColor("#9aa3b2")
SANS, SANS_B = "Helvetica", "Helvetica-Bold"

R = W - M
CARD_TOP, CARD_BOT = 140, 238
TABLE_TOP = 271
COLS_QTY, COLS_RATE = 326, 439
DESC_X = M + 14
DESC_W = 250
BAND_TOP = 745
CONTENT_LIMIT = 722
CONT_TOP = 76


def header(ctx: Ctx) -> None:
    c, inv = ctx.c, ctx.inv
    lh = draw_logo(ctx, M, Y(50), max_w=32, max_h=32)
    if not lh:
        c.setFillColor(ACCENT)
        c.roundRect(M, Y(82), 32, 32, 6, stroke=0, fill=1)
        text(ctx, initials(inv.biller.name), M + 16, Y(70), font=SANS_B, size=12, color=white, align="center")
    x = M + 44
    text(ctx, inv.biller.name, x, Y(66), font=SANS_B, size=15, color=INK)
    addr = ", ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    text(ctx, wrap(addr, SANS, 9, 200)[0], x, Y(80), font=SANS, size=9, color=MUTED)

    text(ctx, "INVOICE", R, Y(84), font=SANS_B, size=40, color=INK, align="right")
    label = "PAYMENT DUE"
    pw = tracked_width(label, SANS_B, 6.5, 1.2) + 30
    px = R - pw
    c.setFillColor(PILL)
    c.roundRect(px, Y(108), pw, 16, 8, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.circle(px + 10, Y(100), 2.5, stroke=0, fill=1)
    tracked(ctx, px + 17, 104, label, SANS_B, 6.5, ACCENT, 1.2)
    meta = " · ".join(v for v in (inv.invoice_number, inv.currency) if v)
    tracked(ctx, px - 12, 104, meta, SANS_B, 8.5, INK, 0.5, align="right")


def party_block(ctx: Ctx, x: float, top: float, label: str, p, width: float) -> None:
    tracked(ctx, x, top, label, SANS_B, 6.5, MUTED, 1.5)
    t = top + 17
    for ln in wrap(p.name, SANS_B, 10.5, width):
        text(ctx, ln, x, Y(t), font=SANS_B, size=10.5, color=INK)
        t += 14
    for ln in wrap(p.address, SANS, 9, width):
        text(ctx, ln, x, Y(t), font=SANS, size=9, color=BODY)
        t += 12


def info_card(ctx: Ctx) -> None:
    c, inv = ctx.c, ctx.inv
    c.setFillColor(CARD)
    c.setStrokeColor(CARD_LINE)
    c.setLineWidth(0.6)
    c.roundRect(M, Y(CARD_BOT), R - M, CARD_BOT - CARD_TOP, 8, stroke=1, fill=1)
    party_block(ctx, M + 24, 166, "FROM", inv.biller, 160)
    party_block(ctx, 258, 166, "BILLED TO", inv.client, 140)
    for x in (240, 413):
        c.setStrokeColor(CARD_LINE)
        c.setLineWidth(0.6)
        c.line(x, Y(163), x, Y(212))

    tracked(ctx, 430, 166, "DETAILS", SANS_B, 6.5, MUTED, 1.5)
    rows = [("Issued", inv.issue_date.strftime("%d %b %Y")),
            ("Due", inv.due_date.strftime("%d %b %Y")),
            ("Terms", terms(inv))]
    for i, (label, value) in enumerate(rows):
        base = 186 + i * 13
        text(ctx, label, 430, Y(base), font=SANS, size=9, color=MUTED)
        text(ctx, value, R - 24, Y(base), font=SANS_B, size=9, color=INK, align="right")


def new_page(ctx: Ctx) -> float:
    ctx.c.showPage()
    ctx.page += 1
    text(ctx, f"Invoice {ctx.number} (continued)", M, Y(44), font=SANS_B, size=9, color=MUTED)
    rule(ctx, M, R, 52, CARD_LINE)
    return CONT_TOP


def table_header(ctx: Ctx, top: float) -> float:
    c = ctx.c
    c.setFillColor(INK)
    c.rect(M, Y(top + 23), R - M, 23, stroke=0, fill=1)
    tracked(ctx, DESC_X, top + 14, "DESCRIPTION", SANS_B, 7, white, 1.6)
    tracked(ctx, COLS_QTY, top + 14, "QTY", SANS_B, 7, white, 1.6, align="center")
    tracked(ctx, COLS_RATE, top + 14, "RATE", SANS_B, 7, white, 1.6, align="right")
    tracked(ctx, R - 11, top + 14, "AMOUNT", SANS_B, 7, white, 1.6, align="right")
    return top + 23


def items(ctx: Ctx, top: float) -> float:
    inv = ctx.inv
    top = table_header(ctx, top)
    for n, (item, amount) in enumerate(zip(inv.items, ctx.t.line_totals)):
        paras = safe(item.description).splitlines() or [""]
        title = wrap(paras[0], SANS_B, 9.5, DESC_W)
        detail = wrap("\n".join(paras[1:]), SANS, 8.5, DESC_W) if len(paras) > 1 else []
        last = 29 + 12 * (len(title) - 1) + (13 + 11 * (len(detail) - 1) if detail else 0)
        h = max(56, last + 16)
        if top + h > CONTENT_LIMIT:
            top = table_header(ctx, new_page(ctx))
        if n % 2 == 1:
            ctx.c.setFillColor(ZEBRA)
            ctx.c.rect(M, Y(top + h), R - M, h, stroke=0, fill=1)
        base = top + 29
        for ln in title:
            text(ctx, ln, DESC_X, Y(base), font=SANS_B, size=9.5, color=INK)
            base += 12
        base += 1
        for ln in detail:
            text(ctx, ln, DESC_X, Y(base), font=SANS, size=8.5, color=MUTED)
            base += 11
        text(ctx, qty_fmt(item.quantity), COLS_QTY, Y(top + 29), font=SANS, size=9.5, color=BODY, align="center")
        text(ctx, money(inv, item.unit_price), COLS_RATE, Y(top + 29), font=SANS, size=9.5, color=BODY, align="right")
        text(ctx, money(inv, amount), R - 11, Y(top + 29), font=SANS_B, size=9.5, color=INK, align="right")
        rule(ctx, M, R, top + h, ROW_LINE, 0.6)
        top += h
    return top


def summary(ctx: Ctx, top: float) -> float:
    c, inv, t = ctx.c, ctx.inv, ctx.t
    notes = [(lab, body) for lab, body in (("NOTES", inv.notes), ("PAYMENT DETAILS", inv.payment_details)) if body]
    left_w = 250
    notes_h = sum(17 + 12 * len(wrap(body, SANS, 8.5, left_w)) + 14 for _, body in notes)
    rows = [("Subtotal", money(inv, t.subtotal), BODY)]
    if t.discount > 0:
        rows.append((adj_label("Discount", inv.discount), "-" + money(inv, t.discount), ACCENT))
    if t.tax > 0:
        rows.append((adj_label("Tax", inv.tax), money(inv, t.tax), BODY))
    card_h = 112 + 17 * max(0, len(rows) - 2)
    if top + 40 + max(notes_h, card_h - 7) > CONTENT_LIMIT:
        top = new_page(ctx)
    label_base = top + 40

    base = label_base
    for label, body in notes:
        tracked(ctx, M, base - 3, label, SANS_B, 6.5, MUTED, 1.5)
        base += 17
        for ln in wrap(body, SANS, 8.5, left_w):
            text(ctx, ln, M, Y(base), font=SANS, size=8.5, color=BODY)
            base += 12
        base += 14

    cx0, cx1 = 336, R
    c.setFillColor(CARD)
    c.setStrokeColor(CARD_LINE)
    c.setLineWidth(0.6)
    card_top = label_base - 7
    c.roundRect(cx0, Y(card_top + card_h), cx1 - cx0, card_h, 8, stroke=1, fill=1)
    row_base = card_top + 30
    for label, value, color in rows:
        text(ctx, label, cx0 + 17, Y(row_base), font=SANS, size=9.5, color=BODY)
        text(ctx, value, cx1 - 18, Y(row_base), font=SANS_B, size=9.5, color=color, align="right")
        row_base += 17
    rl = row_base - 9
    rule(ctx, cx0 + 17, cx1 - 18, rl, INK, 0.8)
    tracked(ctx, cx0 + 17, rl + 18, "TOTAL DUE", SANS_B, 7.5, INK, 1.6)
    text(ctx, money(inv, t.total), cx1 - 18, Y(rl + 38), font=SANS_B, size=20, color=INK, align="right")
    return card_top + card_h


def band(ctx: Ctx) -> None:
    inv, t = ctx.inv, ctx.t
    c = ctx.c
    c.setFillColor(INK)
    c.rect(0, 0, W, Y(BAND_TOP), stroke=0, fill=1)
    tracked(ctx, M, 780, "BALANCE DUE", SANS, 7, BAND_MUTED, 1.8)
    text(ctx, money(inv, t.total), M, Y(812), font=SANS_B, size=26, color=white)

    lines = [("Due", inv.due_date.strftime("%d %b %Y"))]
    if inv.invoice_number:
        lines.append(("Reference", inv.invoice_number))
    y = 782
    for label, value in lines:
        vw = pdfmetrics.stringWidth(safe(value), SANS_B, 8.5)
        text(ctx, value, R, Y(y), font=SANS_B, size=8.5, color=white, align="right")
        text(ctx, label, R - vw - 6, Y(y), font=SANS, size=8.5, color=BAND_MUTED, align="right")
        y += 15
    tracked(ctx, R, 813, "THANK YOU FOR YOUR BUSINESS", SANS, 6.5, BAND_MUTED, 1.6, align="right")


def render(inv: InvoiceRequest, totals: Totals, logo: Optional[ImageReader]) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    c.setTitle(f"Invoice {inv.invoice_number}")
    c.setAuthor(safe(inv.biller.name))
    style = Style(font=SANS, bold=SANS_B, size=9.5, text=BODY, muted=MUTED, line=CARD_LINE, accent=ACCENT)
    ctx = Ctx(c, inv, totals, logo, style)
    header(ctx)
    info_card(ctx)
    top = items(ctx, TABLE_TOP)
    top = summary(ctx, top + 26)
    band(ctx)
    if ctx.page > 1:
        text(ctx, f"{ctx.number}  ·  Page {ctx.page}", W / 2, Y(826), font=SANS, size=7.5, color=MUTED, align="center")
    c.save()
    return buf.getvalue()
