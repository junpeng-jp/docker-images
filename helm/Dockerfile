FROM alpine:3.22.4 AS builder

ARG TARGETARCH=amd64
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
RUN curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" \
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
RUN curl -fsSL "https://github.com/helm/chart-testing/releases/download/v${CT_VERSION}/chart-testing_${CT_VERSION}_linux_${TARGETARCH}.tar.gz" \
    | tar -xz -C /tmp \
    && mv /tmp/ct /usr/local/bin/ct \
    && mkdir -p /etc/ct \
    && mv /tmp/etc/* /etc/ct/

FROM python:3.10-alpine AS python-builder

RUN pip install --no-cache-dir pyyaml yamale yamllint

FROM alpine:3.22.4

ENV HELM_PLUGINS=/usr/local/share/helm/plugins

RUN apk add --no-cache \
    ca-certificates \
    bash \
    git=2.49.1-r0 \
    openssl \
    libffi \
    zlib

COPY --from=builder /usr/local/bin/kubectl /usr/local/bin/kubectl
COPY --from=builder /usr/local/bin/helm    /usr/local/bin/helm
COPY --from=builder /usr/local/bin/ct      /usr/local/bin/ct
COPY --from=builder /root/.local/share/helm/plugins /usr/local/share/helm/plugins

# ct expects a chart_schema.yaml to be in /etc/ct
COPY --from=builder /etc/ct /etc/ct

# Python 3.10 binary, stdlib, shared library, and site-packages
COPY --from=python-builder /usr/local/bin/python3.10        /usr/local/bin/python3.10
COPY --from=python-builder /usr/local/bin/yamale            /usr/local/bin/yamale
COPY --from=python-builder /usr/local/bin/yamllint          /usr/local/bin/yamllint
COPY --from=python-builder /usr/local/lib/python3.10        /usr/local/lib/python3.10
COPY --from=python-builder /usr/local/lib/libpython3.10.so.1.0 /usr/local/lib/libpython3.10.so.1.0

RUN ln -sf /usr/local/bin/python3.10 /usr/local/bin/python3 \
    && ln -sf /usr/local/bin/python3.10 /usr/local/bin/python \
    && ln -sf /usr/local/lib/libpython3.10.so.1.0 /usr/local/lib/libpython3.10.so

# Verify all tools and plugins are present
RUN kubectl version --client

RUN helm version \
    && helm plugin list | grep -q "unittest" \
    && echo "helm-unittest verified" \
    && helm plugin list | grep -q "diff" \
    && echo "helm-diff verified"

RUN ct version

RUN python3 --version \
    && python3 -c "import yaml; import yamale; import yamllint; print('Python packages verified')"

RUN yamllint --version 

RUN yamale --help 2>&1 | grep -qi "usage\|yamale" && echo "yamale CLI verified"

RUN --mount=type=bind,source=test-chart,target=/tmp/test-chart \
    cp -r /tmp/test-chart /tmp/test-chart-rw \
    && helm unittest /tmp/test-chart-rw \
    && ct lint --charts /tmp/test-chart --validate-maintainers=false \
    && rm -rf /tmp/test-chart-rw
