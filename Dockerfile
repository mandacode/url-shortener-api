FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 1000 app

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY --chown=app:app . .

USER app

ENTRYPOINT ["./entrypoint.sh"]
