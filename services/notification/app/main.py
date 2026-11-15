import asyncio
import json
import signal
import time

import aio_pika
from pydantic import ValidationError

from app.config import Settings
from app.events import Event
from app.health import PATH
from app.mail import send
from app.store import Store

EXCHANGE = "biocad.booking.events.v1"
QUEUE = "biocad.notifications.v1"
DEAD_EXCHANGE = "biocad.notifications.invalid.v1"
TYPES = ("booking.created.v1", "booking.cancelled.v1")


async def handle(message, store):
    try:
        if len(message.body) > 32768:
            raise ValueError("Event too large")
        event = Event.model_validate_json(message.body)
        if (
            message.message_id != str(event.event_id)
            or message.type != event.type
            or message.correlation_id != str(event.correlation_id)
            or message.routing_key != event.type
        ):
            raise ValueError("Mismatched AMQP identity")
        await asyncio.to_thread(store.accept, event)
    except (ValueError, ValidationError):
        await message.reject(requeue=False)
        return
    except Exception:
        await message.nack(requeue=True)
        await asyncio.sleep(1)
        return
    # A crash before this ACK only redelivers into the same durable inbox identity.
    await message.ack()


async def consume(settings, store, stop):
    while not stop.is_set():
        try:
            async with await aio_pika.connect_robust(
                settings.rabbitmq_url.get_secret_value(), timeout=3
            ) as connection:
                channel = await connection.channel(publisher_confirms=True)
                await channel.set_qos(prefetch_count=1)
                exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
                dead = await channel.declare_exchange(
                    DEAD_EXCHANGE, aio_pika.ExchangeType.FANOUT, durable=True
                )
                invalid = await channel.declare_queue(QUEUE + ".invalid", durable=True)
                await invalid.bind(dead)
                queue = await channel.declare_queue(
                    QUEUE,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": DEAD_EXCHANGE,
                        "x-max-length": 10000,
                        "x-overflow": "reject-publish",
                    },
                )
                for event_type in TYPES:
                    await queue.bind(exchange, routing_key=event_type)
                await queue.consume(lambda message: handle(message, store))
                await stop.wait()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            print(json.dumps({"state": "broker_retry", "error_type": type(error).__name__}), flush=True)
            await asyncio.sleep(2)


async def deliver(settings, store, stop):
    while not stop.is_set():
        try:
            result = await asyncio.to_thread(store.deliver_one, lambda event: send(event, settings))
            if result:
                print(json.dumps(result), flush=True)
        except Exception as error:
            print(json.dumps({"state": "storage_retry", "error_type": type(error).__name__}), flush=True)
        try:
            await asyncio.wait_for(stop.wait(), timeout=0.25)
        except TimeoutError:
            pass


async def heartbeat(settings, store, stop):
    while not stop.is_set():
        good = True
        try:
            await asyncio.to_thread(store.ping)
        except Exception:
            good = False
        PATH.write_text(
            json.dumps(
                {
                    "at": time.time(),
                    "storage_ok": good,
                    "git_sha": settings.git_sha,
                    "release_version": settings.release_version,
                }
            )
        )
        await asyncio.sleep(1)


async def main():
    settings = Settings()
    store = Store(settings.notification_state_path)
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(sig, stop.set)
    consumer = asyncio.create_task(consume(settings, store, stop))
    sender = asyncio.create_task(deliver(settings, store, stop))
    health = asyncio.create_task(heartbeat(settings, store, stop))
    await stop.wait()
    consumer.cancel()
    health.cancel()
    await asyncio.gather(consumer, health, return_exceptions=True)
    await sender  # Let the bounded in-flight SMTP operation finish before graceful shutdown.


if __name__ == "__main__":
    asyncio.run(main())
