"""Versioned, bounded request/reply. No Booking HTTP or database access."""

import asyncio
import json
import time
from uuid import uuid4

import aio_pika

from app.errors import AssistantError, unavailable

QUEUE = "biocad.booking.rpc.v1"
REPLY_PREFIX = "biocad.rpc.reply."


class RpcClient:
    def __init__(self, url: str, session_token: str, csrf: str = ""):
        self.url, self.session_token, self.csrf = url, session_token, csrf

    async def call(self, operation: str, payload: dict | None = None):
        request_id = str(uuid4())
        try:
            async with asyncio.timeout(12):
                connection = await aio_pika.connect(self.url, timeout=3)
                async with connection:
                    channel = await connection.channel(publisher_confirms=True)
                    queue = await channel.declare_queue(
                        REPLY_PREFIX + request_id,
                        exclusive=True,
                        auto_delete=True,
                        arguments={"x-expires": 20000, "x-max-length": 1},
                    )
                    request = {
                        "schema_version": 1,
                        "request_id": request_id,
                        "deadline_at": time.time() + 10,
                        "operation": operation,
                        "session_token": self.session_token,
                        "csrf": self.csrf,
                        "payload": payload or {},
                    }
                    body = json.dumps(request).encode()
                    if len(body) > 32768:
                        raise AssistantError(422, "VALIDATION_ERROR", "Запрос слишком большой")
                    async with queue.iterator() as replies:
                        await channel.default_exchange.publish(
                            aio_pika.Message(
                                body=body,
                                correlation_id=request_id,
                                reply_to=queue.name,
                                content_type="application/json",
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                                expiration=12,
                            ),
                            routing_key=QUEUE,
                        )
                        async for message in replies:
                            async with message.process():
                                if message.correlation_id != request_id or len(message.body) > 131072:
                                    raise unavailable()
                                reply = json.loads(message.body)
                                if (
                                    reply.get("schema_version") != 1
                                    or reply.get("request_id") != request_id
                                    or reply.get("type") != "booking.response.v1"
                                ):
                                    raise unavailable()
                                if reply["status"] >= 400:
                                    error = reply["data"]["error"]
                                    raise AssistantError(reply["status"], error["code"], error["message"])
                                return reply["data"]
        except AssistantError:
            raise
        except Exception:
            raise unavailable() from None
        raise unavailable()
