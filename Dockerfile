# Runtime image: sjx (linux/amd64) Docker Compose deployment.
FROM python:3.11.17-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Seoul \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    procps \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid 1001 --create-home --shell /usr/sbin/nologin appuser

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=appuser:appuser . .
ENV PATH="/app/.venv/bin:${PATH}"

USER appuser

CMD [".venv/bin/python", "-m", "scripts.run"]
