"""Shared editorial layout. Each template supplies a Theme: colours, type families and a few switches."""
import io
from dataclasses import dataclass
from typing import Optional

from reportlab.lib.colors import Color, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas

from ..calc import Totals
from ..models import InvoiceRequest
from .base import H, M, W, Ctx, Style, adj_label, draw_logo, money, qty_fmt, safe, text, wrap


@dataclass(frozen=True)
class Theme:
    accent: Color
    ink: Color
    body: Color
    muted: Color
    line: Color
    pill_bg: Color
    pill_fg: Color
    sans: str = "Helvetica"
    sans_b: str = "Helvetica-Bold"
    serif: str = "Times-Roman"
    serif_b: str = "Times-Bold"
    serif_i: str = "Times-Italic"
    title: str = "Invoice"
    title_font: str = "Times-Roman"
    title_size: float = 34
    title_color: Optional[Color] = None  # defaults to ink
    name_font: str = "Times-Roman"
    name_size: float = 18
    band: bool = True          # filled balance band (False: a plain rule instead)
    pill: bool = True          # "PAYMENT DUE" pill
    initials: bool = True      # initials box when there is no logo
    row_pad: float = 0         # points removed from every item row (negative adds space)
    track: float = 1.6         # letter-spacing for labels


def Y(top: float) -> float:
    return H - top


def tracked_width(s: str, font: str, size: float, track: float) -> float:
    s = safe(s)
    return pdfmetrics.stringWidth(s, font, size) + track * (len(s) - 1)


def tracked(ctx: Ctx, x: float, top: float, s: str, font: str, size: float, color, track: float, align="left") -> float:
    """Letter-spaced label. Returns its width."""
    s = safe(s)
    w = tracked_width(s, font, size, track)
    if align == "right":
        x -= w
    elif align == "center":
        x -= w / 2
    c = ctx.c
    c.saveState()  # keep the character spacing from leaking into later text
    t = c.beginText(x, Y(top))
    t.setFont(font, size)
    t.setCharSpace(track)
    t.setFillColor(color)
    t.textOut(s)
    c.drawText(t)
    c.restoreState()
    return w


def rule(ctx: Ctx, x0: float, x1: float, top: float, color, width=0.8):
    ctx.c.setStrokeColor(color)
    ctx.c.setLineWidth(width)
    ctx.c.line(x0, Y(top), x1, Y(top))


def initials(name: str) -> str:
    parts = [p for p in safe(name).split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return safe(name)[:2].upper()


def terms(inv: InvoiceRequest) -> str:
    days = (inv.due_date - inv.issue_date).days
    return "Due on receipt" if days == 0 else f"Net {days} days"


# Layout, measured in points from the top of the page.
PARTY_X = M + 190
DETAIL_X = M + 375
DESC_W = 226
QTY_X = M + 282
RATE_X = M + 400
SUMMARY_W = 229
SUMMARY_LEFT_W = W - 2 * M - SUMMARY_W - 30
CONTENT_LIMIT = 706
CONT_TOP = 76


def header(ctx: Ctx, th: Theme) -> None:
    c, inv = ctx.c, ctx.inv
    lh = draw_logo(ctx, M, Y(52), max_w=40, max_h=40)
    x = M
    if not lh and th.initials:
        c.setFillColor(th.accent)
        c.rect(M, Y(92), 40, 40, stroke=0, fill=1)
        text(ctx, initials(inv.biller.name), M + 20, Y(78), font=th.serif_b, size=16, color=white, align="center")
    if lh or th.initials:
        x = M + 40 + 14
    text(ctx, inv.biller.name, x, Y(68), font=th.name_font, size=th.name_size, color=th.ink)
    addr = ", ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    for i, ln in enumerate(wrap(addr, th.sans, 8.5, 220)):
        text(ctx, ln, x, Y(84 + i * 11), font=th.sans, size=8.5, color=th.muted)

    title_color = th.title_color or th.ink
    text(ctx, th.title, W - M, Y(82), font=th.title_font, size=th.title_size, color=title_color, align="right")
    meta = " · ".join(v for v in (inv.invoice_number, inv.currency) if v)
    tracked(ctx, W - M, 100, meta, th.sans, 8, th.muted, 0.8, align="right")
    rule(ctx, M, W - M, 128, th.line)


def party(ctx: Ctx, th: Theme, x: float, top: float, label: str, p, width: float) -> float:
    tracked(ctx, x, top, label, th.sans, 7, th.muted, th.track)
    t = top + 19
    for ln in wrap(p.name, th.sans_b, 11, width):
        text(ctx, ln, x, Y(t), font=th.sans_b, size=11, color=th.ink)
        t += 15
    lines = wrap(p.address, th.sans, 9, width)
    for extra in (p.email, p.phone, f"Tax ID: {p.tax_id}" if p.tax_id else None):
        if extra:
            lines.extend(wrap(extra, th.sans, 9, width))
    for ln in lines:
        text(ctx, ln, x, Y(t), font=th.sans, size=9, color=th.body)
        t += 13
    return t


def details(ctx: Ctx, th: Theme, top: float) -> float:
    inv = ctx.inv
    tracked(ctx, DETAIL_X, top, "DETAILS", th.sans, 7, th.muted, th.track)
    t = top + 19
    rows = [("Issue date", inv.issue_date), ("Due date", inv.due_date)]
    for i, (label, when) in enumerate(rows):
        text(ctx, label, DETAIL_X, Y(t), font=th.sans, size=9, color=th.muted)
        text(ctx, when.strftime("%d %b %Y"), W - M, Y(t), font=th.sans_b, size=9, color=th.ink, align="right")
        if i == 0:
            rule(ctx, DETAIL_X, W - M, t + 5, th.line, 0.5)
        t += 15
    if not th.pill:
        return t
    pill_top = t - 6
    label = "PAYMENT DUE"
    pw = tracked_width(label, th.sans_b, 6.5, 1.2) + 16
    ctx.c.setFillColor(th.pill_bg)
    ctx.c.roundRect(DETAIL_X, Y(pill_top + 13), pw, 13, 2, stroke=0, fill=1)
    tracked(ctx, DETAIL_X + 8, pill_top + 9.5, label, th.sans_b, 6.5, th.pill_fg, 1.2)
    return pill_top + 13


def table_header(ctx: Ctx, th: Theme, top: float) -> float:
    tracked(ctx, M, top + 14, "DESCRIPTION", th.sans_b, 7.5, th.ink, th.track)
    tracked(ctx, QTY_X, top + 14, "QTY", th.sans_b, 7.5, th.ink, th.track, align="center")
    tracked(ctx, RATE_X, top + 14, "RATE", th.sans_b, 7.5, th.ink, th.track, align="right")
    tracked(ctx, W - M, top + 14, "AMOUNT", th.sans_b, 7.5, th.ink, th.track, align="right")
    rule(ctx, M, W - M, top + 20, th.accent, 1.2)
    return top + 20


def page_number(ctx: Ctx, th: Theme) -> None:
    text(ctx, f"{ctx.number}  ·  Page {ctx.page}", W / 2, Y(826), font=th.sans, size=7.5, color=th.muted, align="center")


def new_page(ctx: Ctx, th: Theme) -> float:
    page_number(ctx, th)
    ctx.c.showPage()
    ctx.page += 1
    text(ctx, f"Invoice {ctx.number} (continued)", M, Y(44), font=th.sans_b, size=9, color=th.muted)
    rule(ctx, M, W - M, 52, th.line)
    return CONT_TOP


def items(ctx: Ctx, th: Theme, top: float) -> float:
    inv = ctx.inv
    top = table_header(ctx, th, top)
    for item, amount in zip(inv.items, ctx.t.line_totals):
        paras = safe(item.description).splitlines() or [""]
        title = wrap(paras[0], th.sans_b, 9.5, DESC_W)
        detail = wrap("\n".join(paras[1:]), th.sans, 8.5, DESC_W) if len(paras) > 1 else []
        h = 17 + 12 * (len(title) - 1) + (13 + 11 * (len(detail) - 1) if detail else 0) + 10 - th.row_pad
        if top + h > CONTENT_LIMIT:
            top = table_header(ctx, th, new_page(ctx, th))
        base = top + 17
        for ln in title:
            text(ctx, ln, M, Y(base), font=th.sans_b, size=9.5, color=th.ink)
            base += 12
        base += 1
        for ln in detail:
            text(ctx, ln, M, Y(base), font=th.sans, size=8.5, color=th.muted)
            base += 11
        qty_base = top + 17
        text(ctx, qty_fmt(item.quantity), QTY_X, Y(qty_base), font=th.sans, size=9.5, color=th.body, align="center")
        text(ctx, money(inv, item.unit_price), RATE_X, Y(qty_base), font=th.sans, size=9.5, color=th.body, align="right")
        text(ctx, money(inv, amount), W - M, Y(qty_base), font=th.sans_b, size=9.5, color=th.ink, align="right")
        rule(ctx, M, W - M, top + h, th.line, 0.6)
        top += h
    return top


def notes_height(ctx: Ctx, th: Theme) -> float:
    h = 0
    for body in (ctx.inv.payment_details, ctx.inv.notes):
        if body:
            h += 17 + 13 * len(wrap(body, th.sans, 8.5, SUMMARY_LEFT_W)) + 14
    return h


def summary(ctx: Ctx, th: Theme, top: float) -> float:
    c, inv, t = ctx.c, ctx.inv, ctx.t
    rows = [("Subtotal", money(inv, t.subtotal), th.body)]
    if t.discount > 0:
        rows.append((adj_label("Discount", inv.discount), "-" + money(inv, t.discount), th.accent))
    if t.tax > 0:
        rows.append((adj_label("Tax", inv.tax), money(inv, t.tax), th.body))
    totals_h = 14 + 18 * (len(rows) - 1) + 9 + 26 + 12 + 32
    need = max(notes_height(ctx, th), totals_h + 14)
    if top + need > CONTENT_LIMIT:
        top = new_page(ctx, th)

    left_top = top
    for label, body in (("PAYMENT DETAILS", inv.payment_details), ("NOTES", inv.notes)):
        if not body:
            continue
        tracked(ctx, M, left_top, label, th.sans, 7, th.muted, th.track)
        base = left_top + 17
        for ln in wrap(body, th.sans, 8.5, SUMMARY_LEFT_W):
            text(ctx, ln, M, Y(base), font=th.sans, size=8.5, color=th.body)
            base += 13
        left_top = base + 14

    x0 = W - M - SUMMARY_W
    base = top + 14
    for label, value, color in rows:
        text(ctx, label, x0, Y(base), font=th.sans, size=9.5, color=th.muted)
        text(ctx, value, W - M, Y(base), font=th.sans, size=9.5, color=color, align="right")
        base += 18
    rl = base - 9
    rule(ctx, x0, W - M, rl, th.ink, 0.8)
    total_base = rl + 26
    tracked(ctx, x0, total_base - 2, "TOTAL DUE", th.sans_b, 8, th.ink, th.track)
    text(ctx, money(inv, t.total), W - M, Y(total_base), font=th.serif, size=22, color=th.ink, align="right")

    band_top = total_base + 12
    if th.band:
        c.setFillColor(th.accent)
        c.rect(x0, Y(band_top + 32), SUMMARY_W, 32, stroke=0, fill=1)
        tracked(ctx, x0 + 14, band_top + 20, "BALANCE DUE", th.sans, 7, white, th.track)
        text(ctx, money(inv, t.total), W - M - 14, Y(band_top + 20), font=th.serif, size=14, color=white, align="right")
        return max(left_top, band_top + 32)
    rule(ctx, x0, W - M, band_top + 4, th.accent, 1.2)
    tracked(ctx, x0, band_top + 18, "BALANCE DUE", th.sans, 7, th.muted, th.track)
    text(ctx, money(inv, t.total), W - M, Y(band_top + 18), font=th.serif, size=14, color=th.ink, align="right")
    return max(left_top, band_top + 22)


def footer(ctx: Ctx, th: Theme) -> None:
    inv = ctx.inv
    rule(ctx, M, W - M, 730, th.line)
    cols = [
        (M, "PAYMENT TERMS", terms(inv)),
        (M + 182, "CURRENCY", inv.currency),
        (M + 352, "REFERENCE", inv.invoice_number or "-"),
    ]
    for x, label, value in cols:
        tracked(ctx, x, 744, label, th.sans, 6.5, th.muted, 1.5)
        text(ctx, value, x, Y(757), font=th.sans_b, size=9, color=th.ink)
    for x in (M + 170, M + 340):
        ctx.c.setStrokeColor(th.line)
        ctx.c.setLineWidth(0.5)
        ctx.c.line(x, Y(738), x, Y(763))
    rule(ctx, M, W - M, 767, th.line)

    text(ctx, "Thank you for your business.", M, Y(811), font=th.serif_i, size=11, color=th.ink)
    tracked(ctx, W - M, 797, inv.biller.name.upper(), th.sans, 7, th.muted, 1.4, align="right")
    addr = " · ".join(ln.strip() for ln in inv.biller.address.splitlines() if ln.strip())
    tracked(ctx, W - M, 810, addr.upper(), th.sans, 7, th.muted, 1.4, align="right")


def render(inv: InvoiceRequest, totals: Totals, logo: Optional[ImageReader], th: Theme) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    c.setTitle(f"Invoice {inv.invoice_number}")
    c.setAuthor(safe(inv.biller.name))
    style = Style(font=th.sans, bold=th.sans_b, size=9.5, text=th.body, muted=th.muted, line=th.line, accent=th.accent)
    ctx = Ctx(c, inv, totals, logo, style)
    header(ctx, th)
    top = max(party(ctx, th, M, 178, "FROM", inv.biller, PARTY_X - M - 20),
              party(ctx, th, PARTY_X, 178, "BILLED TO", inv.client, DETAIL_X - PARTY_X - 20))
    top = max(top, details(ctx, th, 178))
    top = items(ctx, th, max(top + 20, 262))
    top = summary(ctx, th, top + 26)
    footer(ctx, th)
    if ctx.page > 1:
        page_number(ctx, th)
    c.save()
    return buf.getvalue()
