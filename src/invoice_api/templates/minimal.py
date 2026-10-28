from reportlab.lib.colors import HexColor

from .base import H, M, W, Ctx, Style, draw_logo, draw_parties, meta_rows, render as _render, text

DESCRIPTION = "Airy and quiet: lots of white space, hairline rules, no fills."
STYLE = Style(size=9, accent=HexColor("#999999"), line=HexColor("#e2e2e2"), grid="h", pad=8,
              total_size=12, muted=HexColor("#8a8a8a"))


def header(ctx: Ctx) -> float:
    top = H - M - 10
    lh = draw_logo(ctx, M, top, max_w=120, max_h=40)
    if not lh:
        text(ctx, ctx.inv.biller.name, M, top - 10, font=ctx.st.bold, size=11)
    text(ctx, "I N V O I C E", W - M, top - 10, size=10, color=ctx.st.muted, align="right")
    y = top - 52
    x = M
    for k, v in meta_rows(ctx):
        text(ctx, k.upper(), x, y, size=7, color=ctx.st.muted)
        text(ctx, v, x, y - 13, size=10)
        x += 140
    y -= 40
    ctx.c.setStrokeColor(ctx.st.line)
    ctx.c.line(M, y, W - M, y)
    return draw_parties(ctx, y - 24, size_name=10, gap=40) - 22


def render(inv, totals, logo):
    return _render(inv, totals, logo, STYLE, header)
