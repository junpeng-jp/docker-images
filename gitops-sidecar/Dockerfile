FROM alpine:3.23.4 AS builder

ARG TARGETARCH=amd64
ARG VERSION

RUN apk add --no-cache ca-certificates curl

RUN ARTIFACT="gitops_sidecar_v${VERSION}_linux_${TARGETARCH}" \
    && curl -fsSL \
        "https://github.com/junpeng-jp/gitops-sidecar/releases/download/v${VERSION}/${ARTIFACT}" \
        -o "/tmp/${ARTIFACT}" \
    && curl -fsSL \
        "https://github.com/junpeng-jp/gitops-sidecar/releases/download/v${VERSION}/checksums.txt" \
        -o /tmp/checksums.txt

RUN ARTIFACT="gitops_sidecar_v${VERSION}_linux_${TARGETARCH}" \
    && cd /tmp && grep "${ARTIFACT}" checksums.txt | sha256sum -c - \
    && mv "/tmp/${ARTIFACT}" /usr/local/bin/gitops-sidecar \
    && chmod +x /usr/local/bin/gitops-sidecar \
    && rm /tmp/checksums.txt

FROM alpine:3.23.4

RUN apk add --no-cache ca-certificates git openssh-client

COPY --from=builder /usr/local/bin/gitops-sidecar /usr/local/bin/gitops-sidecar

EXPOSE 57005

ENTRYPOINT ["/usr/local/bin/gitops-sidecar"]
