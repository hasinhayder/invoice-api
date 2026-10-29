from reportlab.lib.colors import HexColor

from .layout import Theme, render as _render

DESCRIPTION = "Airy and quiet: light sans-serif, hairline rules, no fills and no pill."
THEME = Theme(
    accent=HexColor("#444444"), ink=HexColor("#222222"), body=HexColor("#444444"), muted=HexColor("#8a8a8a"),
    line=HexColor("#e2e2e2"), pill_bg=HexColor("#f2f2f2"), pill_fg=HexColor("#444444"),
    title_font="Helvetica", title_size=28, name_font="Helvetica-Bold", name_size=15,
    band=False, pill=False, initials=False, track=2.0)


def render(inv, totals, logo):
    return _render(inv, totals, logo, THEME)
