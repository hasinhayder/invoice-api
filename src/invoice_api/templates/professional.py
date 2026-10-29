from reportlab.lib.colors import HexColor

from .layout import Theme, render as _render

DESCRIPTION = "Editorial and polished: serif headings, deep-green accents and a balance band. Default."
THEME = Theme(
    accent=HexColor("#1f3d2e"), ink=HexColor("#1d1d1b"), body=HexColor("#3d3d3a"), muted=HexColor("#6f6f6a"),
    line=HexColor("#d8ddd8"), pill_bg=HexColor("#e4ece6"), pill_fg=HexColor("#1f3d2e"),
    name_font="Times-Roman")


def render(inv, totals, logo):
    return _render(inv, totals, logo, THEME)
