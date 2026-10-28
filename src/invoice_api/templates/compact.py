from reportlab.lib.colors import HexColor

from .base import H, M, W, Ctx, Style, draw_logo, draw_parties, meta_rows, render as _render, text

DESCRIPTION = "Dense small-type layout that fits long item lists on fewer pages."
STYLE = Style(size=8, accent=HexColor("#333333"), th_fill=HexColor("#e9ecef"), zebra=HexColor("#f8f9fa"),
              grid="h", line=HexColor("#d5d9de"), pad=3.5, total_size=11)


def header(ctx: Ctx) -> float:
    top = H - M + 6
    lh = draw_logo(ctx, M, top, max_w=90, max_h=34)
    x = M + (100 if lh else 0)
    text(ctx, "INVOICE", x, top - 14, font=ctx.st.bold, size=16)
    y = top - 28
    line = "   |   ".join(f"{k}: {v}" for k, v in meta_rows(ctx))
    text(ctx, line, x, y, size=8, color=ctx.st.muted)
    y = min(y, top - lh) - 12
    ctx.c.setStrokeColor(ctx.st.accent)
    ctx.c.line(M, y, W - M, y)
    return draw_parties(ctx, y - 14, size_name=9, gap=20) - 6


def render(inv, totals, logo):
    return _render(inv, totals, logo, STYLE, header)
