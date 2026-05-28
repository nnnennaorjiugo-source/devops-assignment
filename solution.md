# Solution

## Overview

This solution containerizes a simple Flask application and deploys it to a local Kubernetes cluster using Helm. It includes a CI pipeline via GitHub Actions, basic observability via Prometheus, Grafana, Loki, and FluentBit, and security hardening at both the container and Kubernetes levels.

See [architecture.md](architecture.md) for a diagram of the full system.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/)
- A [Docker Hub](https://hub.docker.com/) account

---

## Build & Deploy (Local)

### 1. Start Minikube

```bash
minikube start
```

### 2. Build and push the Docker image

Replace `yourdockerhubusername` with your Docker Hub username.

```bash
docker build -t yourdockerhubusername/flask-app:latest .
docker login
docker push yourdockerhubusername/flask-app:latest
```

### 3. Update the image repository in the Helm chart

Edit `chart/values.yaml` and set:

```yaml
image:
  repository: yourdockerhubusername/flask-app
  tag: latest
```

### 4. Deploy the app

```bash
helm install flask-app ./chart
```

To verify the pods are running:

```bash
kubectl get pods -l app.kubernetes.io/name=flask-app
```

### 5. Access the app

```bash
kubectl port-forward svc/flask-app-flask-app 8080:80
```

Open [http://localhost:8080](http://localhost:8080) — it will redirect randomly to `/sergei` or `/raditya`.

Health and readiness endpoints:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

Prometheus metrics:

```bash
curl http://localhost:8080/metrics
```

---

## Deploy the Observability Stack

Add the required Helm repos:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

Deploy Prometheus and Grafana:

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  -f observability/prometheus-values.yaml
```

Deploy Loki and FluentBit:

```bash
helm install logging grafana/loki-stack \
  -f observability/loki-values.yaml
```

### Access Grafana

```bash
kubectl port-forward svc/monitoring-grafana 3000:80
```

Open [http://localhost:3000](http://localhost:3000) and log in with `admin` / `admin`.

- Prometheus metrics are available under the Explore tab, datasource: Prometheus
- Logs are available under the Explore tab, datasource: Loki

---

## CI Pipeline

The pipeline runs on every push and pull request via GitHub Actions (`.github/workflows/ci.yml`).

Steps:
1. Lint Python code with `flake8`
2. Build the Docker image
3. Push the image to Docker Hub tagged with the Git commit SHA
4. Lint the Helm chart with `helm lint`

### Required GitHub Secrets

Add these in your repository under Settings → Secrets → Actions:

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | A Docker Hub access token (not your password) |

---

## Security

| Measure | Where | Detail |
|---|---|---|
| Non-root user | Dockerfile | Dedicated `appuser` system user, `USER appuser` directive |
| Non-root enforcement | Helm chart | `runAsNonRoot: true`, `runAsUser: 1000` |
| Read-only filesystem | Helm chart | `readOnlyRootFilesystem: true` |
| No privilege escalation | Helm chart | `allowPrivilegeEscalation: false` |
| Dropped capabilities | Helm chart | `capabilities.drop: [ALL]` |
| Resource limits | Helm chart | CPU and memory limits on every pod |
| Network policy | Helm chart | Restricts ingress to port 5000 only; egress to DNS only |

---

## Observability

### Metrics
`prometheus_flask_exporter` automatically exposes a `/metrics` endpoint on every pod. Pods are annotated so Prometheus scrapes them without any additional configuration:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "5000"
  prometheus.io/path: "/metrics"
```

### Logs
FluentBit runs as a DaemonSet and collects stdout logs from every pod, forwarding them to Loki. Logs are queryable in Grafana using LogQL.

### Health Probes
Both liveness and readiness probes are configured in the Helm chart:

- `/health` — liveness probe, tells Kubernetes if the pod should be restarted
- `/ready` — readiness probe, tells Kubernetes if the pod should receive traffic

---

## Tradeoffs & Known Issues

**Plain text logging** — logs are emitted as plain text rather than structured JSON. This means Loki can store and ship the logs but field-level filtering (e.g. filter by `level=error`) is not available. In production, a library like `python-json-logger` would be the right addition.

**No persistent storage for Loki** — `persistence.enabled: false` in `loki-values.yaml` means logs are lost when the pod restarts. Acceptable for local development; in production this would be backed by object storage (S3, GCS).

**Grafana password in values file** — the Grafana `adminPassword` is set to `admin` in `prometheus-values.yaml`. In production this would be injected via a Kubernetes Secret or a secrets manager.

**Single-node Minikube** — running 2 replicas on a single-node cluster provides no real redundancy. The `replicaCount: 2` value is set to demonstrate the Helm parameterisation; it has full effect in a multi-node cluster.

**No ingress controller** — access is via `kubectl port-forward` rather than a proper Ingress resource. Adding an NGINX or Traefik ingress would be the natural next step for anything beyond local testing.

**Image tag `latest`** — `values.yaml` defaults to `latest` for convenience during local development. The CI pipeline tags images with the Git commit SHA, and in a real deployment `--set image.tag=$GIT_SHA` would be passed at deploy time.

---

## What I'd Do With More Time

- Add structured JSON logging via `python-json-logger` and pre-built Grafana dashboards to query log fields
- Configure a Grafana dashboard for request rate, error rate, and latency (RED metrics) from the Prometheus data
- Set up alerting rules in Prometheus for error rate thresholds
- Add an Ingress resource with TLS termination
- Pin the base Docker image to a specific digest rather than a floating tag for reproducible builds
- Add image vulnerability scanning (Trivy) to the CI pipeline
- Store Grafana password and any other secrets in a proper secrets manager
