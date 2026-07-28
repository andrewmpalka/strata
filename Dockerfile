ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STRATA_MIGRATIONS_DIR=/srv/migrations

WORKDIR /srv

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir ".[test]" \
    && rm -rf src

COPY migrations ./migrations
COPY tests ./tests
COPY integration_tests ./integration_tests

# No credentials are baked in. Every secret is read from the runtime
# environment by strata.config.
CMD ["python", "-m", "strata.main"]
