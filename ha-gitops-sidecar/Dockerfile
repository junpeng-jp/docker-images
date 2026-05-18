FROM python:3.12-alpine AS builder

RUN apk add --no-cache yaml-dev

WORKDIR /build
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

FROM python:3.12-alpine

RUN apk add --no-cache git openssh-client yaml

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/ha-gitops-sidecar /usr/local/bin/ha-gitops-sidecar

RUN adduser -D -u 1000 appuser
USER appuser

ENTRYPOINT ["ha-gitops-sidecar"]
