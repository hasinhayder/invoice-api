from reportlab.lib.colors import HexColor

from .layout import Theme, render as _render

DESCRIPTION = "Centred-feel serif with muted gold rules and an italic title."
THEME = Theme(
    accent=HexColor("#a98a4c"), ink=HexColor("#2b2b2b"), body=HexColor("#2b2b2b"), muted=HexColor("#8c7a55"),
    line=HexColor("#e4d9bf"), pill_bg=HexColor("#f5efe0"), pill_fg=HexColor("#8c7a55"),
    title_font="Times-Italic", title_size=34, title_color=HexColor("#a98a4c"), band=False)


def render(inv, totals, logo):
    return _render(inv, totals, logo, THEME)
