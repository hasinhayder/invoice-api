from reportlab.lib.colors import HexColor

from .layout import Theme, render as _render

DESCRIPTION = "Heavy crimson headline, strong typography and a big total callout."
THEME = Theme(
    accent=HexColor("#b91c1c"), ink=HexColor("#0a0a0a"), body=HexColor("#262626"), muted=HexColor("#666666"),
    line=HexColor("#e5e5e5"), pill_bg=HexColor("#fde8e8"), pill_fg=HexColor("#b91c1c"),
    title_font="Helvetica-Bold", title_size=40, title_color=HexColor("#b91c1c"), title="INVOICE",
    name_font="Helvetica-Bold", name_size=15)


def render(inv, totals, logo):
    return _render(inv, totals, logo, THEME)
