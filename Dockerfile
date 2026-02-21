FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


# Create a non-root user with bash as default shell and set up environment
RUN adduser -D -s /bin/bash appuser \
    && mkdir -p /home/appuser/.local/bin /app \
    && chown -R appuser:appuser /home/appuser /app

WORKDIR /app

# Install system dependencies and bash as root, clean up apk cache
RUN apk add --no-cache postgresql-client curl bash \
    && rm -rf /var/cache/apk/*

# Copy only dependency files first for better cache usage
COPY pyproject.toml /app/

# Ensure pytest cache directory exists and is writable by all users
RUN mkdir -p /app/.pytest_cache \
    && chmod -R 777 /app/.pytest_cache

# Switch to non-root user and set PATH
USER appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Install uv as appuser, then sync dependencies
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && uv sync --no-dev

# Copy the rest of the application code
COPY --chown=appuser:appuser . /app

EXPOSE 8000
