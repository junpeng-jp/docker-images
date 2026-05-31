# Docker images

This repository builds and publishes reusable Docker images to GitHub Container Registry (GHCR). Each image lives in its own directory, carries a `VERSION` file, and is published as both a versioned tag and `latest`.

## Images

| Image | Directory | Description |
|---|---|---|
| `ghcr.io/junpeng-jp/helm:<version>` | [helm](./helm) | Alpine-based CI image bundling kubectl, helm, helm-diff, helm-unittest, and chart-testing for linting, testing, and deploying Helm charts. |
| `ghcr.io/junpeng-jp/gitops-sidecar:<version>` | [gitops-sidecar](./gitops-sidecar) | Alpine-based image wrapping the [gitops-sidecar](https://github.com/junpeng-jp/gitops-sidecar) binary for GitOps-driven configuration management in Kubernetes pods. |

## Add a new image

1. Create a directory at the repo root with your image name.

2. Add a `Dockerfile`.

3. Add a `VERSION` file containing a single version string.

   ```
   1.0.0
   ```

4. Add an `annotations` file with OCI annotations (see below). This file is required for the annotation verification step to pass.

5. Open a pull request. The CI pipeline picks up the new directory automatically.

## OCI annotations

Each image directory may contain an `annotations` file. Each non-empty line is passed to `docker/build-push-action` as an OCI annotation.

```
<level>:<key>=<value>
```

Always include a level prefix. Lines without one default to `manifest` only.

| Prefix | Where the annotation is stored |
|---|---|
| `index:` | OCI image index (manifest list) — use this for standard metadata on multi-platform images |
| `manifest:` | Each platform-specific image manifest |
| `manifest-descriptor:` | The descriptor entry within the index that references each manifest |
| `index-descriptor:` | The descriptor entry referencing the index itself (uncommon) |

Example:

```
index:org.opencontainers.image.title=my-image
index:org.opencontainers.image.source=https://github.com/org/repo
manifest:org.opencontainers.image.revision=abc123
```

Standard OCI annotation keys are defined at <https://specs.opencontainers.org/image-spec/annotations/>.
