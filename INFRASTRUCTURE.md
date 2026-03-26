# NEX Ledger — ANDROS Infrastructure

## Directory Layout
- `/opt/nex-ledger-src/` — Git repository, source code
- `/opt/github-runner-nex-ledger/` — GitHub Actions runner installation

## GitHub Actions Runner
- Name: `andros-ubuntu-nex-ledger`
- Labels: `andros`, `ubuntu`, `self-hosted`
- Service: `actions.runner.rauschiccsk-nex-ledger.andros-ubuntu-nex-ledger.service`
- User: `andros`
- Runner version: 2.333.0

## Systemd Service Management

```bash
# Status
sudo systemctl status actions.runner.rauschiccsk-nex-ledger.andros-ubuntu-nex-ledger.service

# Restart
sudo systemctl restart actions.runner.rauschiccsk-nex-ledger.andros-ubuntu-nex-ledger.service

# Logs
sudo journalctl -u actions.runner.rauschiccsk-nex-ledger.andros-ubuntu-nex-ledger.service -f
```

## CI/CD Pipeline
- Workflow: `.github/workflows/backend-ci.yml`
- Jobs: lint (ruff) -> test (pytest with PostgreSQL service) -> build (Docker)
- Triggers: push to main/develop, pull requests to main

## Ports (ICC Port Registry)
- 9180 — NEX Ledger API (backend, production)
- 9181 — NEX Ledger Web (frontend, production)
- 5432 — PostgreSQL (CI test service container)

## Tech Stack
- Python 3.12+
- FastAPI
- PostgreSQL 16 (driver: pg8000)
- Docker + Docker Compose
- Poetry (dependency management)
- Ruff (linting)

## First Deploy Checklist
- [x] Runner online: `systemctl status actions.runner.*.service`
- [ ] CI green: push commit, verify workflow passes
- [ ] PostgreSQL test service working: check test job logs
- [ ] Docker build succeeds: check build job logs
