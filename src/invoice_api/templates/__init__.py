from . import bold, classic, compact, elegant, minimal, modern, professional

_MODULES = {
    "professional": professional,
    "classic": classic,
    "modern": modern,
    "minimal": minimal,
    "bold": bold,
    "elegant": elegant,
    "compact": compact,
}

REGISTRY = {name: m.render for name, m in _MODULES.items()}
INFO = [{"name": name, "description": m.DESCRIPTION} for name, m in _MODULES.items()]
