"""Shared rendering engine. Each template supplies a Style and a header function."""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable, Optional

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen.canvas import Canvas

from ..calc import Totals
from ..models import Adjustment, InvoiceRequest

W, H = A4
M = 42  # page margin
BOTTOM = M + 24

_SYMBOLS = {"₹": "INR ", "৳": "BDT ", "₦": "NGN ", "₽": "RUB ", "₺": "TRY "}


def safe(text: str) -> str:
    """Standard PDF fonts only cover Latin-1; replace what they cannot draw."""
    for k, v in _SYMBOLS.items():
        text = text.replace(k, v)
    return text.encode("cp1252", errors="replace").decode("cp1252")


def money(inv: InvoiceRequest, amount: Decimal) -> str:
    cur = safe(inv.currency)
    sep = " " if cur[-1:].isalpha() else ""
    sign = "-" if amount < 0 else ""
    return f"{sign}{cur}{sep}{abs(amount):,.2f}"


def qty_fmt(q: Decimal) -> str:
    s = f"{q:f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def adj_label(name: str, adj: Adjustment) -> str:
    if adj.type == "percent":
        v = f"{adj.value:f}".rstrip("0").rstrip(".") if "." in f"{adj.value:f}" else f"{adj.value:f}"
        return f"{name} ({v}%)"
    return name


def wrap(text: str, font: str, size: float, width: float) -> list[str]:
    out: list[str] = []
    for para in safe(text).splitlines() or [""]:
        out.extend(simpleSplit(para, font, size, width) or [""])
    return out


@dataclass
class Style:
    font: str = "Helvetica"
    bold: str = "Helvetica-Bold"
    size: float = 9.5
    accent: Color = field(default_factory=lambda: HexColor("#111111"))
    text: Color = field(default_factory=lambda: HexColor("#222222"))
    muted: Color = field(default_factory=lambda: HexColor("#777777"))
    th_fill: Optional[Color] = None
    th_text: Color = field(default_factory=lambda: HexColor("#222222"))
    zebra: Optional[Color] = None
    grid: str = "h"  # "box" | "h" | "none"
    line: Color = field(default_factory=lambda: HexColor("#cccccc"))
    pad: float = 6
    total_style: str = "plain"  # "plain" | "box"
    total_size: float = 13


@dataclass
class Ctx:
    c: Canvas
    inv: InvoiceRequest
    t: Totals
    logo: Optional[ImageReader]
    st: Style
    page: int = 1

    @property
    def number(self) -> str:
        return self.inv.invoice_number or ""


HeaderFn = Callable[[Ctx], float]


def draw_logo(ctx: Ctx, x: float, y_top: float, max_w=150, max_h=60, align="left") -> float:
    """Draw logo with its top at y_top; returns height used (0 if no logo)."""
    if not ctx.logo:
        return 0
    iw, ih = ctx.logo.getSize()
    s = min(max_w / iw, max_h / ih, 1e9)
    w, h = iw * s, ih * s
    if align == "center":
        x = x - w / 2
    ctx.c.drawImage(ctx.logo, x, y_top - h, w, h, mask="auto")
    return h


def text(ctx: Ctx, s: str, x: float, y: float, font=None, size=None, color=None, align="left"):
    c, st = ctx.c, ctx.st
    c.setFont(font or st.font, size or st.size)
    c.setFillColor(color or st.text)
    s = safe(s)
    if align == "right":
        c.drawRightString(x, y, s)
    elif align == "center":
        c.drawCentredString(x, y, s)
    else:
        c.drawString(x, y, s)


def block(ctx: Ctx, lines: list[str], x: float, y: float, size=None, leading=None, font=None, color=None) -> float:
    size = size or ctx.st.size
    leading = leading or size * 1.4
    for ln in lines:
        text(ctx, ln, x, y, font=font, size=size, color=color)
        y -= leading
    return y


def party_lines(p, width, ctx: Ctx) -> list[str]:
    st = ctx.st
    lines = wrap(p.address, st.font, st.size, width)
    for label, v in (("", p.email), ("", p.phone), ("Tax ID: ", p.tax_id)):
        if v:
            lines.append(label + v)
    return lines


def draw_parties(ctx: Ctx, y: float, label_biller="FROM", label_client="BILL TO", size_name=11, gap=30) -> float:
    st = ctx.st
    col_w = (W - 2 * M - gap) / 2
    ys = []
    for i, (label, p) in enumerate(((label_biller, ctx.inv.biller), (label_client, ctx.inv.client))):
        x = M + i * (col_w + gap)
        text(ctx, label, x, y, font=st.bold, size=7.5, color=st.muted)
        yy = y - 15
        for ln in wrap(p.name, st.bold, size_name, col_w):
            text(ctx, ln, x, yy, font=st.bold, size=size_name)
            yy -= size_name * 1.35
        yy = block(ctx, party_lines(p, col_w, ctx), x, yy - 1)
        ys.append(yy)
    return min(ys) - 6


def meta_rows(ctx: Ctx) -> list[tuple[str, str]]:
    inv = ctx.inv
    return [
        ("Invoice #", ctx.number),
        ("Issue date", inv.issue_date.strftime("%d %b %Y")),
        ("Due date", inv.due_date.strftime("%d %b %Y")),
    ]


def footer(ctx: Ctx):
    text(ctx, f"{ctx.number}  ·  Page {ctx.page}", W / 2, M - 8, size=7.5, color=ctx.st.muted, align="center")


def new_page(ctx: Ctx, cont_header: Optional[HeaderFn] = None) -> float:
    footer(ctx)
    ctx.c.showPage()
    ctx.page += 1
    st = ctx.st
    text(ctx, f"Invoice {ctx.number} (continued)", M, H - M - 6, font=st.bold, size=9, color=st.muted)
    ctx.c.setStrokeColor(st.line)
    ctx.c.line(M, H - M - 14, W - M, H - M - 14)
    return H - M - 34


def table_header(ctx: Ctx, y: float, cols) -> float:
    st, c = ctx.st, ctx.c
    h = 22
    if st.th_fill:
        c.setFillColor(st.th_fill)
        c.rect(M, y - h, W - 2 * M, h, stroke=0, fill=1)
    if st.grid == "box":
        c.setStrokeColor(st.line)
        c.rect(M, y - h, W - 2 * M, h, stroke=1, fill=0)
    elif st.grid == "h":
        c.setStrokeColor(st.accent)
        c.setLineWidth(1)
        c.line(M, y - h, W - M, y - h)
        c.setLineWidth(1)
    for name, x, w, align in cols:
        tx = x + st.pad if align == "left" else x + w - st.pad
        text(ctx, name.upper(), tx, y - 14.5, font=st.bold, size=7.5, color=st.th_text, align=align)
    return y - h


def draw_items(ctx: Ctx, y: float) -> float:
    st, c, inv = ctx.st, ctx.c, ctx.inv
    full = W - 2 * M
    w_qty, w_unit, w_amt = 50, 85, 95
    w_desc = full - w_qty - w_unit - w_amt
    cols = [
        ("Description", M, w_desc, "left"),
        ("Qty", M + w_desc, w_qty, "right"),
        ("Unit price", M + w_desc + w_qty, w_unit, "right"),
        ("Amount", M + w_desc + w_qty + w_unit, w_amt, "right"),
    ]
    y = table_header(ctx, y, cols)
    leading = st.size * 1.35
    for n, (item, lt) in enumerate(zip(inv.items, ctx.t.line_totals)):
        lines = wrap(item.description, st.font, st.size, w_desc - 2 * st.pad)
        h = len(lines) * leading + 2 * st.pad - (leading - st.size) / 2
        if y - h < BOTTOM + 10:
            y = new_page(ctx)
            y = table_header(ctx, y, cols)
        if st.zebra and n % 2 == 1:
            c.setFillColor(st.zebra)
            c.rect(M, y - h, full, h, stroke=0, fill=1)
        base = y - st.pad - st.size + 1
        for i, ln in enumerate(lines):
            text(ctx, ln, M + st.pad, base - i * leading)
        text(ctx, qty_fmt(item.quantity), cols[1][1] + w_qty - st.pad, base, align="right")
        text(ctx, money(inv, item.unit_price), cols[2][1] + w_unit - st.pad, base, align="right")
        text(ctx, money(inv, lt), cols[3][1] + w_amt - st.pad, base, align="right")
        c.setStrokeColor(st.line)
        c.setLineWidth(0.5)
        if st.grid == "box":
            c.rect(M, y - h, full, h, stroke=1, fill=0)
            for _, x, _, _ in cols[1:]:
                c.line(x, y, x, y - h)
        elif st.grid == "h":
            c.line(M, y - h, W - M, y - h)
        y -= h
    return y


def draw_totals(ctx: Ctx, y: float) -> float:
    st, c, inv, t = ctx.st, ctx.c, ctx.inv, ctx.t
    rows = [("Subtotal", money(inv, t.subtotal))]
    if t.discount > 0:
        rows.append((adj_label("Discount", inv.discount), "-" + money(inv, t.discount)))
    if t.tax > 0:
        rows.append((adj_label("Tax", inv.tax), money(inv, t.tax)))
    need = len(rows) * 18 + 60
    if y - need < BOTTOM:
        y = new_page(ctx)
    y -= 16
    bw = 230
    x0, x1 = W - M - bw, W - M
    for label, val in rows:
        text(ctx, label, x0, y, color=st.muted)
        text(ctx, val, x1, y, align="right")
        y -= 18
    y -= 2
    bh = st.total_size + 18
    if st.total_style == "box":
        c.setFillColor(st.accent)
        c.rect(x0 - 10, y - bh + 14, bw + 20, bh, stroke=0, fill=1)
        fg = white
    else:
        c.setStrokeColor(st.accent)
        c.setLineWidth(1.2)
        c.line(x0, y + 12, x1, y + 12)
        fg = st.text
    text(ctx, "Total due", x0 + (0 if st.total_style != "box" else 0), y - 2, font=st.bold, size=st.total_size * 0.8, color=fg)
    text(ctx, money(inv, t.total), x1 - (0 if st.total_style != "box" else 0), y - 2, font=st.bold, size=st.total_size, color=fg, align="right")
    return y - bh


def draw_notes(ctx: Ctx, y: float) -> float:
    st, inv = ctx.st, ctx.inv
    width = W - 2 * M
    for title, body in (("PAYMENT DETAILS", inv.payment_details), ("NOTES", inv.notes)):
        if not body:
            continue
        lines = wrap(body, st.font, st.size, width)
        if y - 30 - len(lines) * st.size * 1.4 < BOTTOM:
            y = new_page(ctx)
        y -= 18
        text(ctx, title, M, y, font=st.bold, size=7.5, color=st.muted)
        y -= 13
        for ln in lines:
            if y < BOTTOM:
                y = new_page(ctx)
            text(ctx, ln, M, y)
            y -= st.size * 1.4
    return y


def render(inv: InvoiceRequest, totals: Totals, logo: Optional[ImageReader], st: Style, header: HeaderFn) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    c.setTitle(f"Invoice {inv.invoice_number}")
    c.setAuthor(safe(inv.biller.name))
    ctx = Ctx(c, inv, totals, logo, st)
    y = header(ctx)
    y = draw_items(ctx, y - 6)
    y = draw_totals(ctx, y)
    draw_notes(ctx, y)
    footer(ctx)
    c.save()
    return buf.getvalue()
