# ─────────────────────────────────────────────────────────────────────────────
# Lumio Backend — Production Dockerfile
# Multi-stage build: slim final image with FFmpeg + Python
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into /install
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: production image ─────────────────────────────────────────────────
FROM python:3.11-slim AS production

# Install FFmpeg, curl, and unzip (required for Deno installer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno globally (recommended JS runtime for yt-dlp signature deciphering)
RUN curl -fsSL https://deno.land/install.sh | sh \
    && mv /root/.deno/bin/deno /usr/local/bin/ \
    && rm -rf /root/.deno

# Create non-root user for security
RUN groupadd --gid 1001 lumio \
    && useradd --uid 1001 --gid lumio --shell /bin/bash --create-home lumio

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=lumio:lumio . .

# Create temp download directory with correct permissions
RUN mkdir -p /tmp/lumio_downloads && chown lumio:lumio /tmp/lumio_downloads

# Switch to non-root user
USER lumio

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start server
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
