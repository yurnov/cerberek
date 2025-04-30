### --- Stage 1: Builder ---
FROM python:3.13-slim AS builder

WORKDIR /build

# Copy only necessary files to build the wheel
COPY pyproject.toml src/ ./

# Build wheel
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-deps --wheel-dir /wheels .

### --- Stage 2: Runtime ---
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

ARG BUILD_DATETIME=now
ARG CONTAINER_IMAGE_VERSION=source
ARG VCS_REF=HEAD

# Labels as per https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL org.opencontainers.image.authors="yuriy@novostavskiy.kyiv.ua" \
        org.opencontainers.image.created="${BUILD_DATETIME}" \
        org.opencontainers.image.revision="${VCS_REF}" \
        org.opencontainers.image.source="https://github.com/yurnov/cerberek" \
        org.opencontainers.image.title="cerberek-telegram-antispam" \
        org.opencontainers.image.description="Telegram antispam bot inspired by the name of name of Cerberus from the Greek mythology." \
        org.opencontainers.image.vendor="Yuriy Novostavskiy" \
        org.opencontainers.image.version="${CONTAINER_IMAGE_VERSION}"

WORKDIR /app

# Install runtime dependencies
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/debconf/*-old /var/lib/dpkg/*-old /var/log/* /tmp/* /var/tmp/*

# Install the built wheel
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && \
    rm -fr /wheels

# Run app
CMD ["python", "-m", "cerberek.main"]