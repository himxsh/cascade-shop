#!/usr/bin/env python3
"""Ingest cascade-shop Postgres datasets + lineage into DataHub GMS.

Reads table definitions from this repo's catalog (kept in sync with db/init.sql).
Does not use Cascade's demo_graph fixture.

Usage:
    python scripts/ingest_datahub.py           # dry-run
    python scripts/ingest_datahub.py --apply   # emit to DATAHUB_GMS_URL

Env:
    DATAHUB_GMS_URL  (default http://localhost:8080)
    DATAHUB_TOKEN    (optional)
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from datahub.emitter.mcp import MetadataChangeProposalWrapper
    from datahub.emitter.rest_emitter import DatahubRestEmitter
    from datahub.metadata.schema_classes import (
        AuditStampClass,
        DatasetLineageTypeClass,
        DatasetPropertiesClass,
        NumberTypeClass,
        OtherSchemaClass,
        OwnerClass,
        OwnershipClass,
        OwnershipTypeClass,
        SchemaFieldClass,
        SchemaFieldDataTypeClass,
        SchemaMetadataClass,
        StringTypeClass,
        UpstreamClass,
        UpstreamLineageClass,
    )
except ImportError:
    print(
        "acryl-datahub required. Install: pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

PLATFORM = "postgres"
OWNER = "urn:li:corpuser:shop_analytics"


def urn(table: str) -> str:
    return f"urn:li:dataset:(urn:li:dataPlatform:{PLATFORM},cascade_shop.public.{table},PROD)"


# Kept aligned with db/init.sql — operators update both when schema changes.
CATALOG = [
    {
        "name": "raw_orders",
        "description": "Landing table for shop orders.",
        "fields": [
            ("order_id", "bigint"),
            ("user_id", "bigint"),
            ("amount_cents", "int"),
            ("ordered_at", "timestamp"),
        ],
    },
    {
        "name": "stg_orders",
        "description": "Cleaned orders for marts.",
        "fields": [
            ("order_id", "bigint"),
            ("user_id", "bigint"),
            ("amount_cents", "int"),
            ("ordered_at", "timestamp"),
        ],
    },
    {
        "name": "fct_orders",
        "description": "Order-grain fact for analytics.",
        "fields": [
            ("order_id", "bigint"),
            ("user_id", "bigint"),
            ("amount_cents", "int"),
            ("ordered_at", "timestamp"),
        ],
    },
]

# target has upstream source
LINEAGE = [
    ("stg_orders", "raw_orders"),
    ("fct_orders", "stg_orders"),
]


def _schema_fields(fields: list[tuple[str, str]]) -> list:
    out = []
    for name, native in fields:
        cls = NumberTypeClass if native in ("bigint", "int") else StringTypeClass
        out.append(
            SchemaFieldClass(
                fieldPath=name,
                type=SchemaFieldDataTypeClass(type=cls()),
                nativeDataType=native,
            )
        )
    return out


def build_mcps() -> list:
    mcps: list = []
    for ds in CATALOG:
        u = urn(ds["name"])
        mcps.append(
            MetadataChangeProposalWrapper(
                entityUrn=u,
                aspect=DatasetPropertiesClass(description=ds["description"]),
            )
        )
        mcps.append(
            MetadataChangeProposalWrapper(
                entityUrn=u,
                aspect=SchemaMetadataClass(
                    schemaName=ds["name"],
                    platform=f"urn:li:dataPlatform:{PLATFORM}",
                    version=0,
                    hash="",
                    platformSchema=OtherSchemaClass(rawSchema=""),
                    fields=_schema_fields(ds["fields"]),
                ),
            )
        )
        mcps.append(
            MetadataChangeProposalWrapper(
                entityUrn=u,
                aspect=OwnershipClass(
                    owners=[
                        OwnerClass(owner=OWNER, type=OwnershipTypeClass.DATAOWNER)
                    ],
                    lastModified=AuditStampClass(
                        time=0, actor="urn:li:corpuser:datahub"
                    ),
                ),
            )
        )
    for target, source in LINEAGE:
        mcps.append(
            MetadataChangeProposalWrapper(
                entityUrn=urn(target),
                aspect=UpstreamLineageClass(
                    upstreams=[
                        UpstreamClass(
                            dataset=urn(source),
                            type=DatasetLineageTypeClass.TRANSFORMED,
                        )
                    ]
                ),
            )
        )
    return mcps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Emit to DataHub (default: dry-run)",
    )
    args = parser.parse_args()
    mcps = build_mcps()
    if not args.apply:
        print(f"[dry-run] Would emit {len(mcps)} MCP(s):\n")
        for mcp in mcps:
            print(f"  {mcp.entityUrn}  {mcp.aspectName}")
        print("\nRe-run with --apply to emit.")
        return

    gms = os.environ.get("DATAHUB_GMS_URL", "http://localhost:8080").rstrip("/")
    token = os.environ.get("DATAHUB_TOKEN") or None
    emitter = DatahubRestEmitter(gms_server=gms, token=token)
    ok = 0
    for mcp in mcps:
        try:
            emitter.emit(mcp)
            ok += 1
        except Exception as e:
            print(f"FAIL {mcp.entityUrn} [{mcp.aspectName}]: {e}", file=sys.stderr)
    print(f"Emitted {ok}/{len(mcps)} to {gms}")
    if ok != len(mcps):
        sys.exit(1)


if __name__ == "__main__":
    main()
