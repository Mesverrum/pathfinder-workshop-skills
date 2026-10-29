---
name: pathfinder-publish
description: >-
  Publishes Pathfinder InteractiveGuide packages to a Grafana stack and reads
  them back to confirm the API kept every block field. Use when uploading,
  updating, or verifying a learning path, learning journey, or interactive
  guide, or when a Pathfinder write returns 403. Never sends without an
  explicit apply.
---

# Pathfinder publish

Upload is `scripts/upsert_net.py`. It is a Python port of `grafana/grafana-pathfinder-app` `scripts/upsert-learning-path.sh`. It talks to the Grafana HTTP API.

Set `GRAFANA_URL` to the stack origin, such as `https://example.grafana.net`, and `GRAFANA_TOKEN` to a service account token that can edit dashboards and apps. Do not read, print, commit, or paste the token.

## Commands

Dry run (default). Prints the plan and any undeclared block fields. Writes nothing.

```
python scripts/upsert_net.py <packages-root> [pkg ...]
```

Apply. Do this only after the user has seen the dry-run plan and confirmed in this turn.

```
python scripts/upsert_net.py <packages-root> [pkg ...] --apply
```

`--status draft` stores drafts. Default is `published`. `GRAFANA_URL` and `GRAFANA_TOKEN` are required. There is no default stack.

Read back. Compares local block fields to the live resource. A dropped field means the API stripped something the guide needs (`verify`, `hint`, `successCriteria`, conditional configs, terminal blocks).

```
python scripts/readback.py <packages-root> [pkg ...]
```

`<packages-root>` is the directory of package folders. Set `PATHFINDER_PACKAGES` when a generator needs that path.

On Windows, run Python against the script path. Do not inline the script in a shell one-liner.

## What the uploader will not do

- It refuses a guide whose `managed-by` annotation is anything other than `upsert-learning-path.sh`. Those are left untouched.
- It will not apply because a dry run looked clean. `--apply` is the confirmation.
- A 403 on the real POST/PUT means the token cannot write. A dry-run 201 does not prove the write is allowed. Create and update need Editor. Viewer can list guides and still be refused on the write.

## After a write

Open the **path**, not a milestone: `https://<stack>.grafana.net/a/grafana-pathfinder-app?doc=api%3A<path-id>`.

Tenant settings are a different resource. This uploader does not touch them.
