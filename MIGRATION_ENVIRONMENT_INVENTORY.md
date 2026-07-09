# Migration Environment Inventory

Use this file as the operator-facing source of truth for migration gate readiness.

Gate revision:

```text
0011_search_indexes
```

## Environment Status

| Environment ID | Deploy Type | Owner | Host / Service | Last Scan At | Last Scan Result | Current Revision | Compat Fix Applied | Last Deploy At | Manual Baseline Count | Deploy Triggered Passed Count | Log Location | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| test-docker-01 | docker | pending | fixture_m_lite_api | 2026-07-09T16:58:35+08:00 | passed | 0011_search_indexes | no | 2026-07-09T16:58:35+08:00 | 0 | 1 | `docker logs fixture_m_lite_api` | Verified on real Docker test deployment: `migration_check` passed and `docker logs fixture_m_lite_api` emitted `migration_runtime_gate` with `source=app_startup` and `outcome=passed`. |
| prod-linux-01 | systemd | pending | <service_name> | pending | unknown | pending | n/a | pending | 0 | 0 | `journalctl -u <service_name>` | pending first baseline scan |

## Gate Result Vocabulary

- `passed`
- `blocked`
- `unknown`

## Compat Fix Applied Vocabulary

- `yes`
- `no`
- `n/a`

## Deploy Type Vocabulary

- `docker`
- `systemd`

## Baseline Rule

- The first successful or blocked `migration_check` run for an environment is the manual baseline.
- Set `Manual Baseline Count = 0` at that first recorded scan.
- Increment `Deploy Triggered Passed Count` only after later deployments or restarts emit startup outcome `passed`.

## Per-Environment Scan Record

Copy this block once per environment and append new entries instead of rewriting history.

```text
Environment ID:
Deploy Type:
Owner:
Host / Service:
Log Location:

Last scan at:
Command:
  docker exec <container_name> python -m backend.app.tools.migration_check
  OR
  /path/to/.venv/bin/python -m backend.app.tools.migration_check

Last scan result:
  passed | blocked

Current revision:

Issue codes:

Compat fixes applied:
  yes | no

Follow-up action:

Manual baseline count:

Deploy triggered passed count:

Baseline scan:
  yes | no

Evidence:
  - service log snippet
  - docker logs / jq command used
  - journalctl / jq command used
  - ticket / change request id
```

## Recorded Scan Entries

```text
Environment ID: test-docker-01
Deploy Type: docker
Owner: pending
Host / Service: fixture_m_lite_api
Log Location: docker logs fixture_m_lite_api

Last scan at:
  2026-07-09T16:58:35+08:00
Command:
  docker compose exec -T api python -m backend.app.tools.migration_check

Last scan result:
  passed

Current revision:
  0011_search_indexes

Issue codes:
  none

Compat fixes applied:
  no

Follow-up action:
  keep prod-linux-01 pending until first baseline scan

Manual baseline count:
  0

Deploy triggered passed count:
  1

Baseline scan:
  yes

Evidence:
  - migration_check stdout reported `status: runtime migration gate passed`
  - `docker logs fixture_m_lite_api 2>&1 | grep migration_runtime_gate`
  - observed JSON event with `source=app_startup` and `outcome=passed`
```
