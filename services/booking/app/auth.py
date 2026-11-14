import asyncio
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.errors import ApiError
from app.models import AuthSession, DemoAccount, Employee
from app.people import person_public
from app.schemas import LoginRequest

COOKIE_NAME = "biocad_session"
SESSION_SECONDS = 8 * 60 * 60
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
DB = Annotated[AsyncSession, Depends(get_session)]


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return f"scrypt${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().session_secret, salt="biocad-session-v1")


@dataclass
class Identity:
    employee: Employee
    session: AuthSession


async def current_identity(request: Request, db: DB) -> Identity:
    token = request.cookies.get(COOKIE_NAME, "")
    try:
        payload = serializer().loads(token, max_age=SESSION_SECONDS)
        sid = UUID(payload["sid"])
    except (BadSignature, KeyError, ValueError, TypeError):
        raise ApiError(401, "UNAUTHENTICATED", "Войдите в демонстрационный аккаунт") from None
    session = await db.get(AuthSession, sid)
    if session is None or session.expires_at <= datetime.now(UTC):
        raise ApiError(401, "UNAUTHENTICATED", "Сессия завершена")
    employee = await db.get(Employee, session.employee_id)
    if employee is None:
        raise ApiError(401, "UNAUTHENTICATED", "Аккаунт недоступен")
    return Identity(employee, session)


User = Annotated[Identity, Depends(current_identity)]


async def mutation_identity(
    user: User, csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None
) -> Identity:
    token = csrf_token or ""
    if not hmac.compare_digest(token.encode(), user.session.csrf_token.encode()):
        raise ApiError(403, "CSRF_INVALID", "Обновите сессию перед подтверждением")
    return user


Writer = Annotated[Identity, Depends(mutation_identity)]


def profile(user: Identity) -> dict:
    return {
        "employee": person_public(user.employee),
        "csrf_token": user.session.csrf_token,
    }


@router.post("/login")
async def login(body: LoginRequest, response: Response, db: DB):
    account = await db.scalar(select(DemoAccount).where(DemoAccount.username == body.username))
    # Do equivalent hashing work for unknown usernames, without revealing account existence.
    encoded = account.password_hash if account else "scrypt$00000000000000000000000000000000$" + "0" * 128
    valid = await asyncio.to_thread(verify_password, body.password, encoded)
    if account is None or not valid:
        raise ApiError(401, "INVALID_CREDENTIALS", "Неверный логин или пароль")
    session = AuthSession(
        employee_id=account.employee_id,
        csrf_token=secrets.token_urlsafe(32),
        expires_at=datetime.now(UTC) + timedelta(seconds=SESSION_SECONDS),
    )
    db.add(session)
    await db.commit()
    employee = await db.get(Employee, account.employee_id)
    response.set_cookie(
        COOKIE_NAME,
        serializer().dumps({"sid": str(session.id)}),
        max_age=SESSION_SECONDS,
        httponly=True,
        secure=get_settings().app_env != "local",
        samesite="lax",
        path="/api",
    )
    return profile(Identity(employee, session))


@router.get("/me")
async def me(user: User):
    return profile(user)


@router.post("/logout", status_code=204)
async def logout(response: Response, db: DB, user: Writer):
    await db.delete(user.session)
    await db.commit()
    response.delete_cookie(COOKIE_NAME, path="/api")
