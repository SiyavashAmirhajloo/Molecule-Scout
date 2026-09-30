FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxrender1 libxext6 libexpat1 curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && useradd -m app
WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts

# Vina is a subprocess binary, not a pip package: no build-essential/swig in
# this image. Runs as root so the installed binary is world-executable, and the
# receptor cache is created up front so the `app` user can write to the volume
# compose mounts there.
RUN python scripts/fetch_vina.py && \
    mkdir -p /code/cache/receptors && chown -R app:app /code/cache

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
