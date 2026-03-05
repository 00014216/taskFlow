# ─────────────────────────────────────────────────────────────
# CloudBlog Dockerfile - Multi-Stage Build
# ─────────────────────────────────────────────────────────────
#
# A Dockerfile is a set of instructions for building a Docker image.
# Think of it like a recipe: "start with Python, add our code, serve it up".
#
# We use a MULTI-STAGE BUILD:
#   Stage 1 (builder): Install all Python packages
#   Stage 2 (runtime): Copy only what's needed - final image ~150MB instead of ~1GB
#
# This technique reduces the image size dramatically because we don't
# include build tools and compilers in the final image.
# ─────────────────────────────────────────────────────────────

# ── STAGE 1: BUILDER ──────────────────────────────────────────
# We use "python:3.11-slim" - a minimal Python image
FROM python:3.11-slim AS builder

# Set environment variables to keep Python output clean
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy only requirements first (Docker caches this layer for speed)
COPY app/requirements.txt .

# Install dependencies into the system Python path (accessible by all users)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ── STAGE 2: RUNTIME ──────────────────────────────────────────
# Start fresh with a clean slim image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# Copy installed packages from builder stage (system-wide, accessible by all users)
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy our application code
COPY app/ .

# Create a static files directory
RUN mkdir -p /app/staticfiles /app/media

# Create a non-root user for security
# Running as root inside a container is a security risk
RUN adduser --disabled-password --no-create-home --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

# Tell Docker that this container listens on port 8000
EXPOSE 8000

# Default command: run Gunicorn (production web server)
# --workers 3: handle 3 requests at once
# --bind 0.0.0.0:8000: listen on all interfaces, port 8000
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-"]
