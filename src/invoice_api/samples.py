"""A fixed sample invoice, rendered by the template preview endpoint."""
from datetime import date

from .models import Adjustment, InvoiceRequest, LineItem, Party


def sample_invoice(template: str) -> InvoiceRequest:
    return InvoiceRequest(
        template=template,
        invoice_number="SAMPLE-0001",
        currency="USD",
        biller=Party(name="Acme Studio", address="1 Main St\nDhaka 1207", email="hello@acme.test"),
        client=Party(name="Globex Ltd", address="99 Long Road\nLondon", tax_id="GB123456789"),
        items=[
            LineItem(description="Website Data Migration\nLegacy content and assets moved to the new platform",
                     quantity=1, unit_price=500),
            LineItem(description="Disaster Recovery (DR)\nBackup, failover and recovery setup",
                     quantity=1, unit_price=4500),
            LineItem(description="AI Implementation\nIntegration and configuration", quantity=1, unit_price=1000),
            LineItem(description="Support\nOngoing technical support", quantity=20, unit_price=30),
        ],
        discount=Adjustment(type="percent", value=10),
        issue_date=date(2026, 10, 29),
        due_date=date(2026, 11, 12),
        notes="Payment is due within 14 days of the issue date. Thank you for your business.",
    )
