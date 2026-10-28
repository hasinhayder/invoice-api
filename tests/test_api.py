import json
import struct
import zlib

import pytest
from fastapi.testclient import TestClient

from invoice_api.main import app
from invoice_api.models import TEMPLATE_NAMES

client = TestClient(app)


def png(w=200, h=80) -> bytes:
    raw = b"".join(b"\x00" + b"\x20\x60\xc0" * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def payload(n_items=3, **kw):
    d = {
        "biller": {"name": "Acme Studio", "address": "1 Main St\nDhaka 1207", "email": "hi@acme.test"},
        "client": {"name": "Globex Ltd", "address": "99 Long Road\nLondon", "tax_id": "GB123"},
        "items": [{"description": f"Service item {i} " + "with a long description " * 4,
                   "quantity": i + 1, "unit_price": "125.50"} for i in range(n_items)],
        "tax": {"type": "percent", "value": 7.5},
        "discount": {"type": "amount", "value": 20},
        "issue_date": "2026-10-27", "due_date": "2026-11-26",
        "invoice_number": "INV-1", "currency": "$",
        "notes": "Thanks!", "payment_details": "Bank: X\nIBAN: Y",
    }
    d.update(kw)
    return d


@pytest.mark.parametrize("tpl", TEMPLATE_NAMES)
@pytest.mark.parametrize("with_logo", [False, True])
def test_templates(tpl, with_logo):
    files = {"logo": ("l.png", png(), "image/png")} if with_logo else None
    r = client.post("/invoices", data={"data": json.dumps(payload(template=tpl))}, files=files)
    assert r.status_code == 200, r.text
    assert r.content.startswith(b"%PDF")
    assert "invoice-INV-1.pdf" in r.headers["content-disposition"]


@pytest.mark.parametrize("tpl", TEMPLATE_NAMES)
def test_multipage(tpl):
    r = client.post("/invoices/json", json=payload(60, template=tpl))
    assert r.status_code == 200
    assert r.content.count(b"/Type /Page\n") >= 2 or r.content.count(b"/Type /Page") > 2


def test_validation_errors():
    r = client.post("/invoices", data={"data": json.dumps(payload(items=[]))})
    assert r.status_code == 422
    r = client.post("/invoices", data={"data": json.dumps(payload(due_date="2026-01-01"))})
    assert r.status_code == 422
    r = client.post("/invoices", data={"data": "{}"})
    assert r.status_code == 422


def test_bad_logo():
    r = client.post("/invoices", data={"data": json.dumps(payload())},
                    files={"logo": ("l.png", b"not an image", "image/png")})
    assert r.status_code == 422


def test_auto_number_and_templates_list():
    p = payload()
    del p["invoice_number"]
    assert client.post("/invoices/json", json=p).status_code == 200
    assert {t["name"] for t in client.get("/templates").json()} == set(TEMPLATE_NAMES)
