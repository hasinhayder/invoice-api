from reportlab.lib.colors import HexColor, white

from .base import H, M, W, Ctx, Style, draw_logo, draw_parties, meta_rows, render as _render, text

DESCRIPTION = "Heavy dark header block, strong typography and a big total callout."
DARK = HexColor("#14213d")
ORANGE = HexColor("#fca311")
STYLE = Style(accent=DARK, th_fill=DARK, th_text=white, zebra=HexColor("#f4f4f6"), grid="none",
              line=HexColor("#dddddd"), total_style="box", total_size=17, pad=7)


def header(ctx: Ctx) -> float:
    c = ctx.c
    bh = 130
    c.setFillColor(DARK)
    c.rect(0, H - bh, W, bh, stroke=0, fill=1)
    c.setFillColor(ORANGE)
    c.rect(0, H - bh - 5, W, 5, stroke=0, fill=1)
    text(ctx, "INVOICE", M, H - 62, font=ctx.st.bold, size=40, color=white)
    y = H - 84
    for k, v in meta_rows(ctx):
        text(ctx, k.upper(), M, y, size=7.5, color=ORANGE, font=ctx.st.bold)
        text(ctx, v, M + 70, y, size=9.5, color=white)
        y -= 13
    if ctx.logo:
        c.setFillColor(white)
        c.roundRect(W - M - 150, H - 105, 150, 78, 6, stroke=0, fill=1)
        iw, ih = ctx.logo.getSize()
        s = min(130 / iw, 58 / ih)
        c.drawImage(ctx.logo, W - M - 75 - iw * s / 2, H - 66 - ih * s / 2, iw * s, ih * s, mask="auto")
    else:
        text(ctx, ctx.inv.biller.name, W - M, H - 62, font=ctx.st.bold, size=15, color=white, align="right")
    return draw_parties(ctx, H - bh - 34, size_name=12) - 16


def render(inv, totals, logo):
    return _render(inv, totals, logo, STYLE, header)
