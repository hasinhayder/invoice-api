from . import bold, classic, compact, elegant, minimal, modern, noir, professional, sidebar, studio, swiss

_MODULES = {
    "professional": professional,
    "studio": studio,
    "sidebar": sidebar,
    "noir": noir,
    "swiss": swiss,
    "classic": classic,
    "modern": modern,
    "minimal": minimal,
    "bold": bold,
    "elegant": elegant,
    "compact": compact,
}

REGISTRY = {name: m.render for name, m in _MODULES.items()}
INFO = [{"name": name, "description": m.DESCRIPTION} for name, m in _MODULES.items()]
