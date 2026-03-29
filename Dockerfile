FROM python:3.12-slim

WORKDIR /app

# Install supercronic for cron scheduling inside the container
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && \
    curl -fsSLo /usr/local/bin/supercronic \
      https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64 && \
    chmod +x /usr/local/bin/supercronic && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Runtime directories (data/output/logs are gitignored; create them here)
RUN mkdir -p data output logs

# Entrypoint: supercronic reads /app/crontab and runs scheduled jobs
CMD ["supercronic", "/app/crontab"]
