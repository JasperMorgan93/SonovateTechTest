# syntax=docker/dockerfile:1

# Builder: resolve and install dependencies with uv, isolated from the runtime image.
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src/ src/
COPY scripts/ scripts/
RUN uv sync --frozen --no-dev

# Runtime: no build toolchain, no uv — just the resolved venv and the app.
FROM python:3.12-slim AS runtime

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/scripts /app/scripts

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

USER appuser

ENTRYPOINT ["python"]
CMD ["scripts/run_all.py"]
