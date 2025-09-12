# Vault Prometheus Exporter

## Overview
The `vault-prometheus-exporter` is a Python-based service that authenticates with HashiCorp Vault, collects validity information of PKI issuer certificates, and exposes this data as Prometheus-compatible metrics via HTTP endpoint.

## Repository Structure
```
app/
  app.py               # Flask app defining HTTP endpoints (/metrics, /status)
  wsgi.py              # Entrypoint for production Gunicorn server
  lib/
    healthcheck.py     # Health check functions verifying Vault connectivity
    logger.py          # Logger setup (JSON structured logging)
  metrics/
    vault.py           # Core Vault authentication and metrics collection logic
chart/
  vault-prometheus-exporter/
    templates/         # Helm chart templates for Kubernetes deployment
    values.yaml        # Helm chart default configuration variables
docker/
  Dockerfile           # Docker build instructions

```

## Application Flow

**1. Authentication:**

`metrics/vault.py` creates a Vault client using one of:

- Vault token
- User token
- Kubernetes Service Account JWT token

**2. Metric Collection:**
- Lists Vault mounted secrets engines and filters for `pki` types.
- For each PKI engine, lists issuer certificates available.
- Parses each issuer’s certificate, calculates the remaining validity in seconds.
- Publishes this data as Prometheus gauge metrics `vault_issuer_validity_seconds` with labels: `engine`, `issuer`, and `url`.

**3. HTTP Server:**
- Flask app exposes `/metrics` endpoint serving Prometheus metrics.
- Health check endpoint `/status` verifies connectivity to Vault.

**4. Docker & Deployment:**
- Dockerfile builds a lightweight container with Python3 and dependencies.
- Runs with Gunicorn for production-grade server concurrency.
- Helm chart enables Kubernetes deployment with configurable environment variables.

## Development Setup

- Clone the repository and navigate into the project directory.
- Create a Python virtual environment:
```bash
python3 -m venv venv
```
- Activate the virtual environment (Linux and MacOS venv activation):
```bash
source venv/bin/activate
```
- Activate the virtual environment (Windows venv activation):
```bash
# In cmd.exe
venv\Scripts\activate.bat
# In PowerShell
venv\Scripts\Activate.ps1
```
- Install dependencies via: 
```bash
pip install -r app/requirements.txt
```
- Set environment variables such as `VAULT_ADDR`, `VAULT_ROLE`, `VAULT_MOUNT_POINT`.
- Run the Flask development server with:
```bash
python app/app.py
```
- Access metrics at `http://localhost:8080/metrics`.