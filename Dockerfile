FROM python:3.12-slim AS backend-builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# -- Frontend Builder --
FROM node:20-slim AS frontend-builder
WORKDIR /app/ui
COPY ui/package*.json ./
RUN npm ci
COPY ui/ .
# Export static files
ENV NEXT_TELEMETRY_DISABLED=1
# Ensure next.config.ts has output: 'export'
RUN npm run build

# -- Final Production Image --
FROM python:3.12-slim

WORKDIR /app

# Copy python dependencies
COPY --from=backend-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend code
COPY app/ ./app/
COPY services/ ./services/
COPY data/ ./data/

# Copy built frontend static files to a public directory
COPY --from=frontend-builder /app/ui/out ./public

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
