FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

# Own /data before declaring it a volume: ownership set after VOLUME is not
# carried into a fresh named volume reliably.
RUN useradd --create-home --uid 10001 tzbot \
 && mkdir -p /data \
 && chown tzbot:tzbot /data

# The SQLite file lives here; mount a volume over it to keep subscribers
# across container rebuilds.
ENV DATABASE_PATH=/data/tzbot.sqlite3
VOLUME ["/data"]

USER tzbot

CMD ["python", "-m", "tzbot"]
