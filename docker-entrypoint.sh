# syntax=docker/dockerfile:1.5
#
# Production image for the Django app.
#
# Stage 1 compiles the front-end assets with Vite.
# Stage 2 installs the production Python dependencies
# and copies the built assets in.

# ---------------------------------------------------------------------------
# Stage 1: Build front-end assets
# ---------------------------------------------------------------------------
FROM node:24-bookworm AS frontend

WORKDIR /code

# Install Node dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy project and build assets
COPY . .
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: Python application
# ---------------------------------------------------------------------------
FROM python:3.14-bookworm AS app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_PROJECT_ENVIRONMENT=/home/django/.venv \
    PATH="/home/django/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# Install OS dependencies
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && \
    apt-get install -yqq --no-install-recommends \
        gettext \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ARG MY_UID=1000
ARG MY_GID=1000

# Create django user/group
RUN groupadd -g $MY_GID -r django || \
    (groupmod -g $MY_GID django 2>/dev/null || true) && \
    useradd -u $MY_UID -r -g django -m -d /home/django django 2>/dev/null || \
    usermod -u $MY_UID -g django -d /home/django django

# Create application directory
RUN mkdir -p /code && chown django:django /code
WORKDIR /code

# Create uv cache
RUN mkdir -p /tmp/uv-cache && chown django:django /tmp/uv-cache

# Install Python dependencies
USER django

COPY --chown=django:django uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/tmp/uv-cache,uid=$MY_UID,gid=$MY_GID \
    uv sync --frozen --no-dev --group prod

# Copy application source
COPY --chown=django:django . /code/

# Copy built frontend assets
COPY --from=frontend --chown=django:django /code/static /code/static

# Switch to root temporarily
USER root

# Make entrypoint executable
RUN chmod +x /code/docker-entrypoint.sh

# Switch back to non-root user
USER django

EXPOSE 8000

# Use custom startup script
ENTRYPOINT ["/code/docker-entrypoint.sh"]

# Default command
CMD [
    "gunicorn",
    "config.wsgi:application",
    "--bind",
    "0.0.0.0:8000",
    "--workers",
    "3",
    "--access-logfile",
    "-",
    "--error-logfile",
    "-"
]