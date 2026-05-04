FROM alpine:3.22.4 AS builder

ARG PLATFORM=linux-amd64
ARG PLATFORM_CT=linux_amd64
ARG KUBECTL_VERSION=1.36.0
ARG HELM_VERSION=4.1.4
ARG HELM_DIFF_VERSION=3.15.6
ARG HELM_UNITTEST_VERSION=1.0.3
ARG CT_VERSION=3.14.0

RUN apk add --no-cache \
    ca-certificates \
    bash \
    curl \
    openssl \
    git

# kubectl
RUN KUBECTL_ARCH="${PLATFORM#linux-}" \
    && curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${KUBECTL_ARCH}/kubectl" \
    -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl

# helm
RUN curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4 \
    && chmod 700 get_helm.sh \
    && ./get_helm.sh \
    && rm get_helm.sh

# helm-diff plugin
RUN helm plugin install https://github.com/databus23/helm-diff --verify=false --version v${HELM_DIFF_VERSION} \
    && helm plugin list | grep -q "diff" \
    && echo "helm-diff installed successfully"

# helm-unittest plugin (requires openssl)
RUN helm plugin install https://github.com/helm-unittest/helm-unittest.git --verify=false --version v${HELM_UNITTEST_VERSION} \
    && helm plugin list | grep -q "unittest" \
    && echo "helm-unittest installed successfully"

# chart-testing
RUN curl -fsSL "https://github.com/helm/chart-testing/releases/download/v${CT_VERSION}/chart-testing_${CT_VERSION}_${PLATFORM_CT}.tar.gz" \
    | tar -xz -C /tmp \
    && mv /tmp/ct /usr/local/bin/ct \
    && mkdir -p /etc/ct \
    && mv /tmp/etc/* /etc/ct/

# ---- final stage ----
FROM alpine:3.22.4

ENV HELM_PLUGINS=/usr/local/share/helm/plugins

RUN apk add --no-cache \
    ca-certificates \
    bash \
    git \
    yamllint

COPY --from=builder /usr/local/bin/kubectl /usr/local/bin/kubectl
COPY --from=builder /usr/local/bin/helm    /usr/local/bin/helm
COPY --from=builder /usr/local/bin/ct      /usr/local/bin/ct
COPY --from=builder /root/.local/share/helm/plugins /usr/local/share/helm/plugins

# Verify all tools and plugins are present
RUN kubectl version --client 

RUN helm version \
    && helm plugin list | grep -q "unittest" \
    && echo "helm-unittest verified" \
    && helm plugin list | grep -q "diff" \
    && echo "helm-diff verified"

RUN ct version
