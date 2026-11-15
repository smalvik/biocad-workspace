# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.5.11-python3.12-bookworm-slim AS base
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 TZ=UTC
WORKDIR /srv

FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

FROM base AS test
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project
COPY . .
ENV PATH="/srv/.venv/bin:$PATH"
CMD ["pytest", "-q", "--alluredir=/allure-results"]

FROM python:3.12-slim-bookworm AS runtime
ARG GIT_SHA=dev
LABEL org.opencontainers.image.source="biocad-workspace" org.opencontainers.image.revision=$GIT_SHA
ENV PYTHONUNBUFFERED=1 PATH="/srv/.venv/bin:$PATH" GIT_SHA=$GIT_SHA
WORKDIR /srv
RUN useradd --system --uid 10001 app && mkdir /data && chown app /data
COPY --from=deps /srv/.venv /srv/.venv
COPY app ./app
USER app
HEALTHCHECK --interval=5s --timeout=3s --retries=6 CMD python -m app.health
CMD ["python", "-m", "app.main"]
