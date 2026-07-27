FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/strata ./strata
COPY app/tests ./tests
COPY migrations ./migrations

# No credentials are baked in. Every secret is read from the runtime
# environment by strata.config.
CMD ["python", "-m", "strata.main"]
