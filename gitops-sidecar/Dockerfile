FROM alpine:3.23.4 AS builder

ARG TARGETARCH=amd64
ARG VERSION

RUN apk add --no-cache ca-certificates curl

RUN curl -fsSL \
    "https://github.com/junpeng-jp/gitops-sidecar/releases/download/v${VERSION}/gitops-sidecar_linux_${TARGETARCH}" \
    -o /usr/local/bin/gitops-sidecar \
    && chmod +x /usr/local/bin/gitops-sidecar

FROM alpine:3.23.4

RUN apk add --no-cache ca-certificates git openssh-client

COPY --from=builder /usr/local/bin/gitops-sidecar /usr/local/bin/gitops-sidecar

EXPOSE 57005

ENTRYPOINT ["/usr/local/bin/gitops-sidecar"]
