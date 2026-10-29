import json
import os
import re
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import ValidationError

from .calc import compute
from .home import render_home
from .logo import LogoError, load_logo
from .models import InvoiceRequest
from .templates import INFO, REGISTRY

app = FastAPI(
    title="Invoice Builder API",
    description="Generate PDF invoices in seven templates. Stateless; nothing is stored.",
    version="0.1.0",
)


def _build(inv: InvoiceRequest, logo_bytes: Optional[bytes]) -> Response:
    logo = None
    if logo_bytes:
        try:
            logo = load_logo(logo_bytes)
        except LogoError as e:
            raise HTTPException(422, detail=[{"loc": ["logo"], "msg": str(e)}])
    if not inv.invoice_number:
        inv.invoice_number = f"INV-{datetime.now():%Y%m%d-%H%M%S}"
    pdf = REGISTRY[inv.template](inv, compute(inv), logo)
    fname = re.sub(r"[^A-Za-z0-9._-]+", "_", inv.invoice_number)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice-{fname}.pdf"'},
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return render_home(str(request.base_url))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/templates")
def templates():
    return INFO


@app.post("/invoices", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
async def create_invoice(
    data: str = Form(..., description="JSON string matching the InvoiceRequest schema"),
    logo: Optional[UploadFile] = File(None, description="Optional PNG/JPEG logo, max 2 MB"),
):
    try:
        inv = InvoiceRequest.model_validate_json(data)
    except ValidationError as e:
        raise HTTPException(422, detail=json.loads(e.json()))
    logo_bytes = await logo.read() if logo and logo.filename else None
    return _build(inv, logo_bytes)


@app.post("/invoices/json", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
def create_invoice_json(inv: InvoiceRequest):
    return _build(inv, None)


def run():
    import uvicorn

    uvicorn.run(
        "invoice_api.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
    )
