import asyncio
import os
import smtplib
from email.message import EmailMessage
from uuid import uuid4

import aio_pika
import allure
import httpx
import pytest

pytestmark = [pytest.mark.integration, allure.suite("smoke"), allure.feature("infrastructure")]


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} not set: use scripts/check.py for real infrastructure tests")
    return value


async def test_rabbitmq_round_trip_through_durable_queue():
    connection = await aio_pika.connect(required_env("RABBITMQ_URL"), timeout=10)
    async with connection:
        channel = await connection.channel(publisher_confirms=True)
        queue = await channel.declare_queue(f"wb01-smoke-{uuid4().hex}", durable=True)
        try:
            payload = b"fictional WB-01 infrastructure smoke"
            await channel.default_exchange.publish(
                aio_pika.Message(body=payload, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=queue.name,
                timeout=10,
            )
            message = await queue.get(timeout=10)
            assert message is not None
            async with message.process():
                assert message.body == payload
                assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
        finally:
            await queue.delete(if_unused=False, if_empty=False)


async def test_smtp_delivery_is_visible_in_real_mailpit():
    host = required_env("MAILPIT_SMTP_HOST")
    api = required_env("MAILPIT_API_URL")
    subject = f"WB-01 fictional smoke {uuid4().hex}"
    message = EmailMessage()
    message["From"] = "workspace@example.test"
    message["To"] = "fictional-employee@example.test"
    message["Subject"] = subject
    message.set_content("Fictional infrastructure check; no real booking or personal data.")

    def send():
        with smtplib.SMTP(host, 1025, timeout=10) as smtp:
            smtp.send_message(message)

    await asyncio.to_thread(send)
    async with httpx.AsyncClient(base_url=api, timeout=10) as client:
        for _ in range(20):
            response = await client.get("/api/v1/search", params={"query": f'subject:"{subject}"'})
            response.raise_for_status()
            if any(item["Subject"] == subject for item in response.json()["messages"]):
                return
            await asyncio.sleep(0.25)
    pytest.fail("SMTP accepted the message but Mailpit did not expose it")
