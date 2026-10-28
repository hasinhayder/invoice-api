from reportlab.lib.colors import HexColor

from .base import H, M, W, Ctx, Style, draw_logo, draw_parties, meta_rows, render as _render, text

DESCRIPTION = "Centered, serif and refined with muted gold rules."
GOLD = HexColor("#a98a4c")
STYLE = Style(font="Times-Roman", bold="Times-Bold", size=10.5, accent=GOLD, text=HexColor("#2b2b2b"),
              muted=HexColor("#8c7a55"), line=HexColor("#e4d9bf"), grid="h", pad=7, total_size=15)


def header(ctx: Ctx) -> float:
    c = ctx.c
    cx = W / 2
    y = H - M
    lh = draw_logo(ctx, cx, y, max_w=140, max_h=56, align="center")
    y -= lh + (14 if lh else 0)
    if not lh:
        text(ctx, ctx.inv.biller.name, cx, y - 8, font=ctx.st.bold, size=15, align="center")
        y -= 28
    text(ctx, "Invoice", cx, y - 20, font="Times-Italic", size=32, color=GOLD, align="center")
    y -= 40
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(M, y, W - M, y)
    c.line(M, y - 3, W - M, y - 3)
    y -= 22
    rows = meta_rows(ctx)
    cw = (W - 2 * M) / len(rows)
    for i, (k, v) in enumerate(rows):
        text(ctx, k.upper(), M + cw * (i + 0.5), y, size=8, color=ctx.st.muted, align="center")
        text(ctx, v, M + cw * (i + 0.5), y - 14, font=ctx.st.bold, size=11, align="center")
    y -= 36
    c.line(M, y, W - M, y)
    return draw_parties(ctx, y - 22, size_name=12) - 14


def render(inv, totals, logo):
    return _render(inv, totals, logo, STYLE, header)
