# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.5.11-python3.12-bookworm-slim AS base
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 TZ=UTC
WORKDIR /srv

FROM base AS deps
COPY services/booking/pyproject.toml services/booking/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

# Test image: dev deps + tests; used by compose `test` profile and CI.
FROM base AS test
COPY services/booking/pyproject.toml services/booking/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project
COPY services/booking/ .
COPY docs/data/demo_fixture.json ./data/demo_fixture.json
COPY scripts/delivery_manifest.py scripts/deploy_server.py scripts/package_images.py /delivery/
COPY tests/delivery/ ./tests/delivery/
ENV PATH="/srv/.venv/bin:$PATH"
CMD ["pytest", "-q", "--alluredir=/allure-results"]

FROM python:3.12-slim-bookworm AS runtime
ARG GIT_SHA=dev
LABEL org.opencontainers.image.source="biocad-workspace" org.opencontainers.image.revision=$GIT_SHA
ENV PYTHONUNBUFFERED=1 PATH="/srv/.venv/bin:$PATH" GIT_SHA=$GIT_SHA
WORKDIR /srv
RUN useradd --system --uid 10001 app
COPY --from=deps /srv/.venv /srv/.venv
COPY services/booking/app ./app
COPY services/booking/migrations ./migrations
COPY services/booking/alembic.ini ./alembic.ini
COPY docs/data/demo_fixture.json ./data/demo_fixture.json
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz').status==200 else 1)"
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
