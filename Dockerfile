# Stage 1: Build wheel
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ src/
COPY config/ config/

RUN pip install --no-cache-dir build \
    && python -m build --wheel --outdir /build/dist

# Stage 2: Runtime
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 \
       libxdamage1 libxrandr2 libgbm1 libasound2 libpango-1.0-0 \
       libcairo2 libatspi2.0-0 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl \
    && rm -rf /tmp/*.whl

# Install Playwright Chromium
RUN playwright install chromium --with-deps 2>/dev/null || true

COPY config/ config/

ENTRYPOINT ["searchmuse"]
