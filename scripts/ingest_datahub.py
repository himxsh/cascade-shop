#!/usr/bin/env python3
"""Ingest cascade-shop Postgres datasets + lineage into DataHub GMS.

Kept aligned with db/init.sql and models/. Does not use Cascade demo_graph.

Usage:
    python scripts/ingest_datahub.py           # dry-run
    python scripts/ingest_datahub.py --apply   # emit to DATAHUB_GMS_URL
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
    return (
        f"urn:li:dataset:(urn:li:dataPlatform:{PLATFORM},"
        f"cascade_shop.public.{table},PROD)"
    )


def _fields(*pairs: tuple[str, str]) -> list[tuple[str, str]]:
    return list(pairs)


CATALOG = [
    {
        "name": "raw_customers",
        "description": "Landing customers.",
        "fields": _fields(
            ("customer_id", "bigint"),
            ("email", "string"),
            ("full_name", "string"),
            ("country", "string"),
        ),
    },
    {
        "name": "raw_products",
        "description": "Landing products.",
        "fields": _fields(
            ("product_id", "bigint"),
            ("sku", "string"),
            ("product_name", "string"),
            ("unit_price_cents", "int"),
        ),
    },
    {
        "name": "raw_orders",
        "description": "Landing orders.",
        "fields": _fields(
            ("order_id", "bigint"),
            ("user_id", "bigint"),
            ("amount_cents", "int"),
            ("ordered_at", "timestamp"),
        ),
    },
    {
        "name": "raw_order_items",
        "description": "Landing order line items.",
        "fields": _fields(
            ("order_id", "bigint"),
            ("product_id", "bigint"),
            ("qty", "int"),
            ("line_amount_cents", "int"),
        ),
    },
    {
        "name": "stg_customers",
        "description": "Staged customers.",
        "fields": _fields(
            ("customer_id", "bigint"),
            ("email", "string"),
            ("full_name", "string"),
            ("country", "string"),
        ),
    },
    {
        "name": "stg_products",
        "description": "Staged products.",
        "fields": _fields(
            ("product_id", "bigint"),
            ("sku", "string"),
            ("product_name", "string"),
            ("unit_price_cents", "int"),
        ),
    },
    {
        "name": "stg_orders",
        "description": "Staged orders.",
        "fields": _fields(
            ("order_id", "bigint"),
            ("user_id", "bigint"),
            ("amount_cents", "int"),
            ("ordered_at", "timestamp"),
        ),
    },
    {
        "name": "stg_order_items",
        "description": "Staged order items with sku.",
        "fields": _fields(
            ("order_id", "bigint"),
            ("product_id", "bigint"),
            ("sku", "string"),
            ("qty", "int"),
            ("line_amount_cents", "int"),
        ),
    },
    {
        "name": "int_orders_enriched",
        "description": "Orders joined to customer attributes.",
        "fields": _fields(
            ("order_id", "bigint"),
            ("user_id", "bigint"),
            ("email", "string"),
            ("country", "string"),
            ("amount_cents", "int"),
            ("ordered_at", "timestamp"),
        ),
    },
    {
        "name": "fct_orders",
        "description": "Order-grain fact.",
        "fields": _fields(
            ("order_id", "bigint"),
            ("user_id", "bigint"),
            ("amount_cents", "int"),
            ("ordered_at", "timestamp"),
        ),
    },
    {
        "name": "fct_order_items",
        "description": "Order-item fact with purchaser.",
        "fields": _fields(
            ("order_id", "bigint"),
            ("product_id", "bigint"),
            ("user_id", "bigint"),
            ("qty", "int"),
            ("line_amount_cents", "int"),
        ),
    },
    {
        "name": "mart_customer_revenue",
        "description": "Customer revenue mart.",
        "fields": _fields(
            ("user_id", "bigint"),
            ("email", "string"),
            ("country", "string"),
            ("order_count", "int"),
            ("revenue_cents", "bigint"),
        ),
    },
]

# (downstream, upstream)
LINEAGE = [
    ("stg_customers", "raw_customers"),
    ("stg_products", "raw_products"),
    ("stg_orders", "raw_orders"),
    ("stg_order_items", "raw_order_items"),
    ("stg_order_items", "raw_products"),
    ("int_orders_enriched", "stg_orders"),
    ("int_orders_enriched", "stg_customers"),
    ("fct_orders", "int_orders_enriched"),
    ("fct_order_items", "stg_order_items"),
    ("fct_order_items", "stg_orders"),
    ("mart_customer_revenue", "fct_orders"),
    ("mart_customer_revenue", "stg_customers"),
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

    # Group lineage by target so multi-upstream datasets get one aspect
    by_target: dict[str, list[str]] = {}
    for target, source in LINEAGE:
        by_target.setdefault(target, []).append(source)
    for target, sources in by_target.items():
        mcps.append(
            MetadataChangeProposalWrapper(
                entityUrn=urn(target),
                aspect=UpstreamLineageClass(
                    upstreams=[
                        UpstreamClass(
                            dataset=urn(src),
                            type=DatasetLineageTypeClass.TRANSFORMED,
                        )
                        for src in sources
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
