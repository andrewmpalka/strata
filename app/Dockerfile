FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY strata ./strata
COPY tests ./tests

# No credentials are baked in. Every secret is read from the runtime
# environment by strata.config.
CMD ["python", "-m", "strata.main"]
