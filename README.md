# cascade-shop

Reference consumer for [Cascade](https://github.com/himxsh/Cascade): a small Postgres analytics warehouse with nested SQL models, DataHub lineage ingest, and a GitHub Action that runs Cascade on breaking PRs (`--source live` only).

This is not Cascade’s offline fixture demo. It is a standalone repo another team can copy.

## Layout

| Path | Role |
|------|------|
| `docker-compose.yml` | Postgres 16 on host port **5433** |
| `db/init.sql` | Schema + seed rows (`raw_orders` → `stg_orders` → `fct_orders`) |
| `models/raw|staging|marts/` | SQL Cascade remediates |
| `.cascade/config.json` | Path→URN mappings + `urn_files` |
| `scripts/ingest_datahub.py` | Register datasets + lineage in DataHub |
| `.github/workflows/cascade.yml` | Installs pinned Cascade; live impact + remediation PR |

## Prerequisites

1. Docker (Postgres)
2. [DataHub](https://datahubproject.io/) GMS reachable locally (e.g. quickstart on `http://localhost:8080`)
3. For GitHub Actions: an **HTTPS tunnel** to that GMS (Cloudflare Tunnel or ngrok) — runners cannot see `localhost`

## Setup

```bash
cp .env.example .env
docker compose up -d
# wait until healthy, then:
psql postgresql://shop:shop@localhost:5433/cascade_shop -c 'select count(*) from raw_orders;'

pip install -r requirements.txt
export DATAHUB_GMS_URL=http://localhost:8080
python scripts/ingest_datahub.py          # dry-run
python scripts/ingest_datahub.py --apply  # emit to GMS
```

Confirm lineage in the DataHub UI for:

`urn:li:dataset:(urn:li:dataPlatform:postgres,cascade_shop.public.raw_orders,PROD)`

## GitHub Actions (live)

1. Create this repo on GitHub and push.
2. Start a tunnel to local GMS, e.g. `cloudflared tunnel --url http://localhost:8080`.
3. Repo **Settings → Secrets**:

| Secret | Required | Notes |
|--------|----------|--------|
| `DATAHUB_GMS_URL` | yes | HTTPS tunnel URL (no trailing path issues; GMS root) |
| `DATAHUB_TOKEN` | if GMS needs auth | empty OK for local quickstart |
| `LLM_API_KEY` | optional | LLM-primary rewrites |
| `CASCADE_WRITEBACK` | optional | set `1` only when you want live tags from Actions |

4. Open a PR that renames `user_id` → `customer_id` in `models/raw/raw_orders.sql` (and update `db/init.sql` in the same change when you migrate the warehouse).

The workflow **fails** if `DATAHUB_GMS_URL` is missing. It never falls back to Cascade’s fixture catalog.

Update the Cascade pin in `.github/workflows/cascade.yml` when you intentionally upgrade (`@e52764e` → new tag/commit).

## Local Cascade (optional)

```bash
pip install "cascade @ git+https://github.com/himxsh/Cascade.git@5fd05e1"
# from a branch with a breaking SQL diff file:
cascade impact --diff /tmp/break.diff --source live --generate --out /tmp/out
cascade apply --report /tmp/out/impact_report.json --out /tmp/apply --mode dry-run
```

## License

Apache-2.0 — same spirit as Cascade; this reference repo is provided as an integration example.
