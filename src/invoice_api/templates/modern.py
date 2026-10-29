from reportlab.lib.colors import HexColor

from .layout import Theme, render as _render

DESCRIPTION = "Clean sans-serif with a bright blue accent and a solid total band."
THEME = Theme(
    accent=HexColor("#2563eb"), ink=HexColor("#111827"), body=HexColor("#374151"), muted=HexColor("#6b7280"),
    line=HexColor("#dbe3f5"), pill_bg=HexColor("#dbe7ff"), pill_fg=HexColor("#1d4ed8"),
    title_font="Helvetica-Bold", title_size=32, title_color=HexColor("#2563eb"),
    name_font="Helvetica-Bold", name_size=16)


def render(inv, totals, logo):
    return _render(inv, totals, logo, THEME)
