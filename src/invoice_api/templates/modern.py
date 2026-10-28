from reportlab.lib.colors import HexColor, white

from .base import H, M, W, Ctx, Style, draw_logo, draw_parties, meta_rows, render as _render, text

DESCRIPTION = "Clean sans-serif with a blue accent bar, zebra-striped rows."
ACCENT = HexColor("#2563eb")
STYLE = Style(accent=ACCENT, th_fill=ACCENT, th_text=white, zebra=HexColor("#f3f6fd"), grid="none",
              line=HexColor("#dbe3f5"), total_style="box", total_size=13)


def header(ctx: Ctx) -> float:
    c = ctx.c
    c.setFillColor(ACCENT)
    c.rect(0, H - 16, W, 16, stroke=0, fill=1)
    top = H - 16 - 32
    text(ctx, "Invoice", M, top - 8, font=ctx.st.bold, size=30, color=ACCENT)
    y = top - 30
    for k, v in meta_rows(ctx):
        text(ctx, k, M, y, color=ctx.st.muted, size=9)
        text(ctx, v, M + 62, y, font=ctx.st.bold, size=9)
        y -= 13
    lh = draw_logo(ctx, W - M - 150, top + 6, align="left") if ctx.logo else 0
    if not lh:
        text(ctx, ctx.inv.biller.name, W - M, top - 4, font=ctx.st.bold, size=13, align="right")
    return draw_parties(ctx, min(y, top - lh) - 24) - 14


def render(inv, totals, logo):
    return _render(inv, totals, logo, STYLE, header)
