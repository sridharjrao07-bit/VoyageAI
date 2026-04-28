FROM python:3.10-slim

WORKDIR /app

# Install system-level build dependencies for numpy, scipy, scikit-learn, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching — only re-installs if deps change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user (HF Spaces best practice)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH="/home/user/.local/bin:$PATH"

# Copy entire backend into /app
COPY --chown=user . /app

# HF Spaces requires port 7860
EXPOSE 7860

# Run FastAPI via uvicorn — single worker to stay within free-tier RAM
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
