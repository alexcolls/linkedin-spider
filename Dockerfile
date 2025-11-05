# Multi-stage Dockerfile for LinkedIn Spider
# Optimized for Kubernetes deployment with headless Chrome

# Stage 1: Builder - Install Python dependencies
FROM python:3.12-slim as builder

# Install Poetry
ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (including production extras)
RUN poetry install --no-root --no-dev --with excel \
    && poetry add psycopg2-binary redis sqlalchemy \
    && rm -rf $POETRY_CACHE_DIR


# Stage 2: Runtime - Final image with Chrome
FROM python:3.12-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libu2f-udev \
    libvulkan1 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r spider && useradd -r -g spider -u 1000 spider \
    && mkdir -p /home/spider /app/data /app/logs /tmp/spider \
    && chown -R spider:spider /home/spider /app /tmp/spider

WORKDIR /app

# Copy Python virtual environment from builder
COPY --from=builder --chown=spider:spider /app/.venv /app/.venv

# Copy application code
COPY --chown=spider:spider src ./src
COPY --chown=spider:spider config.yaml ./
COPY --chown=spider:spider pyproject.toml poetry.lock ./

# Set up environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CHROME_BIN=/usr/bin/google-chrome-stable \
    DISPLAY=:99 \
    TMPDIR=/tmp/spider

# Switch to non-root user
USER spider

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command (can be overridden)
CMD ["python", "-m", "linkedin_spider.cli.main", "worker"]
