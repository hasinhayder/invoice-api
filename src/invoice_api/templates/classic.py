from reportlab.lib.colors import HexColor

from .layout import Theme, render as _render

DESCRIPTION = "Traditional serif layout: black ink, ruled sections and a bordered feel."
THEME = Theme(
    accent=HexColor("#000000"), ink=HexColor("#000000"), body=HexColor("#222222"), muted=HexColor("#555555"),
    line=HexColor("#8a8a8a"), pill_bg=HexColor("#eeeeee"), pill_fg=HexColor("#000000"),
    sans="Times-Roman", sans_b="Times-Bold", title="INVOICE", title_font="Times-Bold", title_size=30,
    name_font="Times-Bold", name_size=17, band=False, pill=False, track=1.0)


def render(inv, totals, logo):
    return _render(inv, totals, logo, THEME)
