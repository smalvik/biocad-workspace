import smtplib
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.config import Settings
from app.events import Event

TEMPLATES = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html"]),
    undefined=StrictUndefined,
)
MOSCOW = ZoneInfo("Europe/Moscow")


def render(event: Event, public_url: str) -> EmailMessage:
    title = "Бронь подтверждена" if event.status == "confirmed" else "Бронь отменена"
    resource = "FreeDesk" if event.notification.kind == "DESK" else "Переговорная"
    start, end = event.start_at.astimezone(MOSCOW), event.end_at.astimezone(MOSCOW)
    values = {
        "title": title,
        "employee_name": event.notification.employee_name,
        "resource": resource,
        "space_id": event.space_id,
        "office": event.notification.office_name,
        "address": event.notification.office_address,
        "floor": event.notification.floor_name,
        "booking_id": str(event.booking_id),
        "period": f"{start:%d.%m.%Y %H:%M} — {end:%d.%m.%Y %H:%M} МСК",
        "public_url": public_url.rstrip("/") + "/",
    }
    message = EmailMessage()
    message["From"] = "BIOCAD Workspace Demo <workspace@example.test>"
    message["To"] = event.notification.recipient
    message["Subject"] = f"{title} · {resource} {event.space_id} · {event.booking_id}"
    message["Message-ID"] = f"<{event.event_id}@workspace.example.test>"
    message["Date"] = format_datetime(event.occurred_at)
    message["X-BIOCAD-Event-ID"] = str(event.event_id)
    message["X-Correlation-ID"] = str(event.correlation_id)
    message.set_content(TEMPLATES.get_template("booking.txt").render(**values))
    message.add_alternative(TEMPLATES.get_template("booking.html").render(**values), subtype="html")
    return message


def send(event: Event, settings: Settings) -> None:
    message = render(event, settings.notification_public_url)
    with smtplib.SMTP(
        settings.mailpit_smtp_host, settings.mailpit_smtp_port, timeout=settings.smtp_timeout
    ) as smtp:
        refused = smtp.send_message(message)
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)
