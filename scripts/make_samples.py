"""Render one sample PDF per template into docs/samples/ (uses tests' payload + logo helper)."""
import sys, json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "tests"))
from fastapi.testclient import TestClient
from test_api import payload, png
from invoice_api.main import app
from invoice_api.models import TEMPLATE_NAMES

out = root / "docs" / "samples"
c = TestClient(app)
for t in TEMPLATE_NAMES:
    r = c.post("/invoices", data={"data": json.dumps(payload(template=t, invoice_number=f"SAMPLE-{t}"))},
               files={"logo": ("logo.png", png(), "image/png")})
    r.raise_for_status()
    (out / f"{t}.pdf").write_bytes(r.content)
r = c.post("/invoices/json", json=payload(40, template="compact", invoice_number="SAMPLE-long"))
(out / "compact-multipage.pdf").write_bytes(r.content)
