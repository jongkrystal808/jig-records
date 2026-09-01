# Migration Gate Runbook

## Purpose

Use this runbook before deploying a backend build that contains the runtime migration gate in `backend/app/core/migrations.py`.

The goal is to prevent surprise outages from deploying into environments that are still below the migration gate revision `0011_search_indexes`.

## Runtime Behavior

- Fresh databases without legacy app tables are allowed to start and run Alembic normally.
- Databases below `0011_search_indexes` are blocked at startup.
- Legacy compatibility fixes are no longer applied silently during startup.
- Manual compatibility checks must be run first through:

```bash
python -m backend.app.tools.migration_check
```

## Required Inputs

Before rollout, maintain one line per deployed environment in [MIGRATION_ENVIRONMENT_INVENTORY.md](MIGRATION_ENVIRONMENT_INVENTORY.md).

Track at least:

- environment id
- deploy type
- owner
- host / service
- current revision
- gate result
- scan date
- manual baseline count
- deploy-triggered passed count

Current environment split:

- test machine: `docker`
- production machine: `systemd`

Treat them as two fully independent environment entries. They do not share `.env`, Docker settings, logs, or revision tracking.

## Pre-Rollout Procedure

Run this for every known environment before enabling the runtime gate in production-like deployments.

1. Record the environment in [MIGRATION_ENVIRONMENT_INVENTORY.md](MIGRATION_ENVIRONMENT_INVENTORY.md) before the first scan.
2. Run the first `migration_check` scan for that environment.
3. Treat that first scan as manual baseline `0` for gate tracking.
4. If the result is blocked, fix the environment before deploying the gated startup build.

### Test Machine: Docker

Run from the host:

```bash
docker exec <container_name> python -m backend.app.tools.migration_check
```

If the check is blocked because of `alembic_version` metadata compatibility issues, run:

```bash
docker exec <container_name> python -m backend.app.tools.migration_check --apply-compat-fixes
```

Then run the explicit Alembic upgrade path for that environment and re-run:

```bash
docker exec <container_name> python -m backend.app.tools.migration_check
```

### Production Machine: Linux Native / systemd

Run from the host with the same Python runtime the service uses:

```bash
python -m backend.app.tools.migration_check
```

or:

```bash
/path/to/.venv/bin/python -m backend.app.tools.migration_check
```

If the check is blocked because of `alembic_version` metadata compatibility issues, run:

```bash
/path/to/.venv/bin/python -m backend.app.tools.migration_check --apply-compat-fixes
```

Then run the explicit Alembic upgrade path for that environment and re-run the plain check.

### Rollout Blocker

Do not deploy the gated startup build until the environment reports:

```text
status: runtime migration gate passed
```

## Rollout Rule

Do not use the first gated deployment itself as the environment discovery mechanism.

The runtime gate is allowed to protect against missed legacy environments, but only after all known environments have already been scanned and recorded.

## Deployment-Time Verification

After each deployment or restart, confirm one of these log outcomes from the service log:

- `"event": "migration_runtime_gate", "outcome": "passed"`
- `"event": "migration_runtime_gate", "outcome": "blocked"`
- `"event": "migration_runtime_gate", "outcome": "compat_fixes_applied"`

Examples:

- test machine: `docker`

```bash
docker logs <container_name> 2>&1 | grep 'migration_runtime_gate'
```

If the Docker log backend is persisted and you want structured filtering:

```bash
docker logs <container_name> 2>&1 \
  | jq -R 'fromjson? | select(.event == "migration_runtime_gate")'
```

If the application log is mounted to a host volume instead of only stdout:

```bash
jq -c 'select(.event == "migration_runtime_gate")' /path/to/mounted/volume/app.log
```

- production machine: `systemd`

```bash
journalctl -u <service_name> --since "30 min ago" \
  | grep 'migration_runtime_gate'
```

Prefer structured filtering when `jq` is available:

```bash
journalctl -u <service_name> -o cat --since "30 min ago" \
  | jq -R 'fromjson? | select(.event == "migration_runtime_gate")'
```

Only the latest boot:

```bash
journalctl -u <service_name> -b -o cat \
  | jq -R 'fromjson? | select(.event == "migration_runtime_gate")'
```

Live follow:

```bash
journalctl -u <service_name> -f -o cat \
  | jq -R 'fromjson? | select(.event == "migration_runtime_gate")'
```

## Gate Tracking Rule

To justify removal of `schema_patch.py` from the remaining historical path, keep evidence for:

1. every known environment scanned at least once
2. every known environment currently at or above `0011_search_indexes`
3. `N` consecutive deployments per environment with startup outcome `passed`
4. zero environments still relying on offline compat fixes during that observation window

## Suggested Inventory Workflow

Per environment:

1. initial scan
2. mark that scan as manual baseline `0`
3. compat fix if required
4. explicit Alembic upgrade
5. post-upgrade scan
6. record deployment count and startup outcome after each restart

## Current Limits

- The application now emits structured startup log events, but it does not yet aggregate them into a central dashboard or database table.
- Counting `N` consecutive clean deployments still depends on log collection discipline plus the inventory document.
- The Docker and systemd environments intentionally use different scan and log-collection commands; do not collapse them into one shared procedure in the inventory.
