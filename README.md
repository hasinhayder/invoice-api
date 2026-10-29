# Invoice Builder API

A small FastAPI service that renders PDF invoices in twelve templates, plus an agent skill (`skills/invoice-generator`) that lets an AI agent turn a user's plain-text invoice notes into a finished PDF.

- Stateless: nothing is stored; the PDF is returned in the response.
- No authentication — meant for local use. Bind to `127.0.0.1` (default) unless you add auth.
- Pure-Python PDF rendering (ReportLab); no system dependencies.

## Quickstart

```bash
uv sync
./start.sh                  # http://127.0.0.1:8120 (env HOST, PORT to change)
uv run pytest               # tests
```

Interactive docs: http://127.0.0.1:8120/docs

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/templates` | list templates `[{name, description}]` |
| GET | `/templates/{name}/preview` | sample invoice in that template, as a PDF |
| POST | `/invoices` | multipart: `data` (JSON string, required) + `logo` (PNG/JPEG ≤ 2 MB, optional) → `application/pdf` |
| POST | `/invoices/json` | JSON body, no logo → PDF |

```bash
curl -fS -o invoice.pdf \
  -F 'data=<invoice.json' \
  -F 'logo=@logo.png' \
  http://127.0.0.1:8120/invoices
```

Invoice JSON (full table in `skills/invoice-generator/reference/schema.md`):

```json
{
  "template": "modern",
  "currency": "USD",
  "invoice_number": "INV-001",
  "biller": {"name": "Acme Studio", "address": "1 Main St\nDhaka 1207", "email": "hi@acme.test"},
  "client": {"name": "Globex Ltd", "address": "99 Long Road\nLondon"},
  "items": [{"description": "Website redesign", "quantity": 1, "unit_price": 2500}],
  "tax": {"type": "percent", "value": 20},
  "discount": {"type": "amount", "value": 50},
  "issue_date": "2026-10-27",
  "due_date": "2026-11-26",
  "notes": "Thank you!",
  "payment_details": "IBAN GB00 0000 0000"
}
```

Totals are computed server-side: `subtotal − discount + tax` where tax applies to the discounted subtotal (decimal, half-up rounding). `tax` / `discount` are `{type: "percent"|"amount", value}`. Without a logo the logo area is simply omitted. Validation problems return HTTP 422 with `detail: [{loc, msg}]`. Long invoices paginate automatically.

## Templates

`professional` (default) · `studio` · `sidebar` · `noir` · `swiss` · `ledger` · `classic` · `modern` · `minimal` · `bold` · `elegant` · `compact` — samples in `docs/samples/` (regenerate with `uv run python scripts/make_samples.py`).

Limitation: standard PDF fonts are used, so only Latin-1 text renders correctly (₹/৳ currency symbols are converted to codes; other unsupported characters become `?`).

## Agent skill

`skills/invoice-generator/` contains `SKILL.md` (workflow: read notes → structure → ask for missing info → call API → save PDF), `scripts/generate_invoice.sh`, and references. Install:

```bash
ln -s "$PWD/skills/invoice-generator" ~/.claude/skills/invoice-generator
```

The agent needs the API running (`./start.sh`) — the skill tells it to start the server if it is unreachable. Set `INVOICE_API_URL` if it runs elsewhere.

## Hosting

Production deployment on a CloudPanel server (site setup, systemd, SSL, basic auth): [docs/DEPLOY-CLOUDPANEL.md](docs/DEPLOY-CLOUDPANEL.md).

## Layout

```
src/invoice_api/   main.py (routes) · models.py · calc.py · logo.py · templates/
tests/             calc + API/template tests
skills/            invoice-generator skill
scripts/           make_samples.py
```
