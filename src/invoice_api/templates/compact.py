from reportlab.lib.colors import HexColor

from .layout import Theme, render as _render

DESCRIPTION = "Dense small-type layout with tighter rows for long item lists."
THEME = Theme(
    accent=HexColor("#0f766e"), ink=HexColor("#111111"), body=HexColor("#333333"), muted=HexColor("#666666"),
    line=HexColor("#d4d4d4"), pill_bg=HexColor("#ccfbf1"), pill_fg=HexColor("#0f766e"),
    title_font="Helvetica-Bold", title_size=22, name_font="Helvetica-Bold", name_size=13, row_pad=5, track=1.2)


def render(inv, totals, logo):
    return _render(inv, totals, logo, THEME)
