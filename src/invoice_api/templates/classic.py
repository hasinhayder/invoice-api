from reportlab.lib.colors import HexColor

from .base import H, M, W, Ctx, Style, draw_logo, draw_parties, meta_rows, render as _render, text

DESCRIPTION = "Traditional serif layout with a fully bordered table. Black and white."
STYLE = Style(font="Times-Roman", bold="Times-Bold", size=10.5, th_fill=HexColor("#eeeeee"), grid="box",
              line=HexColor("#555555"), accent=HexColor("#000000"), total_size=14)


def header(ctx: Ctx) -> float:
    c = ctx.c
    top = H - M
    lh = draw_logo(ctx, M, top)
    if not lh:
        text(ctx, ctx.inv.biller.name, M, top - 18, font=ctx.st.bold, size=18)
    text(ctx, "INVOICE", W - M, top - 20, font=ctx.st.bold, size=28, align="right")
    y = top - 42
    for k, v in meta_rows(ctx):
        text(ctx, f"{k}:", W - M - 170, y, font=ctx.st.bold, size=10)
        text(ctx, v, W - M, y, size=10, align="right")
        y -= 14
    y = min(y, top - max(lh, 24) - 8) - 6
    c.setStrokeColor(ctx.st.accent)
    c.setLineWidth(1.5)
    c.line(M, y, W - M, y)
    return draw_parties(ctx, y - 20, size_name=12) - 14


def render(inv, totals, logo):
    return _render(inv, totals, logo, STYLE, header)
