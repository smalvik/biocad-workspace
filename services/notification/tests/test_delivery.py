from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import allure
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.events import Event
from app.mail import render
from app.main import handle
from app.store import Store

pytestmark = [allure.suite("regression"), allure.feature("notification")]


def test_durable_deduplication_after_ack_loss_and_restart(tmp_path, event):
    path = str(tmp_path / "deliveries.sqlite")
    original = Store(path)
    assert original.accept(event)
    sender = Mock()
    assert original.deliver_one(sender)["state"] == "sent"
    restarted = Store(path)
    assert not restarted.accept(event)
    assert restarted.deliver_one(sender) is None
    sender.assert_called_once()


def test_concurrent_admission_and_sending_have_one_delivery(tmp_path, event):
    store = Store(str(tmp_path / "deliveries.sqlite"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(lambda _: store.accept(event), range(16))) == 1
        sender = Mock()
        list(pool.map(lambda _: store.deliver_one(sender), range(8)))
    sender.assert_called_once()


def test_conflicting_duplicate_does_not_replace_original(tmp_path, event):
    store = Store(str(tmp_path / "deliveries.sqlite"))
    store.accept(event)
    with pytest.raises(ValueError, match="Conflicting"):
        store.accept(event.model_copy(update={"space_id": "D-24"}))
    sent = []
    store.deliver_one(sent.append)
    assert sent[0].space_id == "D-15"


def test_smtp_retry_survives_restart_and_preserves_per_booking_order(tmp_path, event):
    path = str(tmp_path / "deliveries.sqlite")
    store = Store(path)
    cancellation = event.model_copy(
        update={"event_id": uuid4(), "type": "booking.cancelled.v1", "status": "cancelled"}
    )
    unrelated = event.model_copy(update={"event_id": uuid4(), "booking_id": uuid4()})
    for value in (event, cancellation, unrelated):
        store.accept(value)
    assert store.deliver_one(Mock(side_effect=OSError("SMTP down")), now=0)["state"] == "retry"
    sent = []
    assert store.deliver_one(sent.append, now=0)["event_id"] == str(unrelated.event_id)
    assert store.deliver_one(sent.append, now=1) is None
    restarted = Store(path)
    assert restarted.deliver_one(sent.append, now=2)["event_id"] == str(event.event_id)
    assert restarted.deliver_one(sent.append, now=2)["event_id"] == str(cancellation.event_id)
    assert [row.status for row in sent] == ["confirmed", "confirmed", "cancelled"]


@pytest.mark.parametrize(
    "kind,status,event_type,title",
    [
        ("DESK", "confirmed", "booking.created.v1", "Бронь подтверждена"),
        ("MEETING_ROOM", "cancelled", "booking.cancelled.v1", "Бронь отменена"),
    ],
)
def test_branded_multipart_moscow_period_and_stable_identity(event, kind, status, event_type, title):
    event = event.model_copy(
        update={
            "type": event_type,
            "status": status,
            "notification": event.notification.model_copy(update={"kind": kind}),
        }
    )
    message = render(event, "https://biocad.smalvik.dev")
    assert message["To"] == "e01@example.test"
    assert message["Message-ID"] == f"<{event.event_id}@workspace.example.test>"
    assert title in message["Subject"]
    for subtype in ("plain", "html"):
        body = message.get_body(preferencelist=(subtype,)).get_content()
        assert "18.11.2026 10:00" in body and "18.11.2026 12:00 МСК" in body
        assert str(event.booking_id) in body and "D-15" in body
        assert "Вымышленный адрес, 1" in body and "Этаж 2" in body
        assert "https://biocad.smalvik.dev/" in body
        assert "Анна Смирнова" in body and "support@example.test" in body
    assert "приблизительные" in message.get_body(preferencelist=("html",)).get_content()


def test_html_fields_are_escaped(event):
    event = event.model_copy(
        update={
            "notification": event.notification.model_copy(
                update={
                    "office_address": '<script>alert("x")</script>',
                    "employee_name": "<script>unsafe name</script>",
                }
            )
        }
    )
    html = render(event, "http://localhost:8080").get_body(preferencelist=("html",)).get_content()
    assert "<script>" not in html and "&lt;script&gt;" in html


@pytest.mark.parametrize(
    "field,value",
    [
        ("recipient", "someone@real-domain.example"),
        ("recipient", "e01@example.test\r\nBcc: attack@example.test"),
        ("fictional", False),
        ("kind", "UNKNOWN"),
    ],
)
def test_rejects_real_recipient_header_injection_or_non_demo(event, field, value):
    data = event.model_dump(mode="json")
    data["notification"][field] = value
    with pytest.raises(ValidationError):
        Event.model_validate(data)


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": 2},
        {"type": "shell"},
        {"status": "cancelled"},
        {"start_at": "2026-11-18T10:00:00"},
        {"end_at": "2026-11-17T01:00:00Z"},
    ],
)
def test_rejects_invalid_event_contract(event, change):
    with pytest.raises(ValidationError):
        Event.model_validate({**event.model_dump(mode="json"), **change})


def test_refuses_external_smtp_and_non_http_cta():
    with pytest.raises(ValidationError):
        Settings(mailpit_smtp_host="smtp.example.org")
    with pytest.raises(ValidationError):
        Settings(notification_public_url="javascript:alert(1)")


def message(event):
    return Mock(
        body=event.model_dump_json().encode(),
        message_id=str(event.event_id),
        type=event.type,
        correlation_id=str(event.correlation_id),
        routing_key=event.type,
        ack=AsyncMock(),
        reject=AsyncMock(),
        nack=AsyncMock(),
    )


async def test_ack_only_after_durable_admission(event):
    incoming = message(event)
    store = Mock()

    def admit(value):
        incoming.ack.assert_not_awaited()

    store.accept.side_effect = admit
    await handle(incoming, store)
    incoming.ack.assert_awaited_once()
    incoming.reject.assert_not_awaited()


async def test_failed_inbox_write_requeues_before_ack(event, monkeypatch):
    incoming = message(event)
    store = Mock(accept=Mock(side_effect=OSError("disk full")))
    import app.main as main

    monkeypatch.setattr(main.asyncio, "sleep", AsyncMock())
    await handle(incoming, store)
    incoming.ack.assert_not_awaited()
    incoming.nack.assert_awaited_once_with(requeue=True)


async def test_invalid_amqp_identity_dead_letters_without_admission(event):
    incoming = message(event)
    incoming.message_id = str(uuid4())
    store = Mock()
    await handle(incoming, store)
    store.accept.assert_not_called()
    incoming.reject.assert_awaited_once_with(requeue=False)
