#!/usr/bin/env python3
"""Build manifest.json from all latest.json files in data/.

Usage:
    python3 tools/build_manifest.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
VOCAB_DIR = REPO_ROOT / "vocab"
SCHEMAS_DIR = REPO_ROOT / "schemas"
SCHEMA_BASE = "https://raw.githubusercontent.com/eva01/qs-data/master/schemas"
RAW_BASE = "https://raw.githubusercontent.com/eva01/qs-data/master"


def load_categories_vocab() -> dict[str, dict]:
    """Load categories.json keyed by slug."""
    path = VOCAB_DIR / "categories.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        cats = json.load(f)
    return {c["slug"]: c for c in cats}


def build_manifest() -> dict:
    categories_vocab = load_categories_vocab()
    categories_out = []

    # Walk all category directories
    for cat_dir in sorted(DATA_DIR.iterdir()):
        if not cat_dir.is_dir():
            continue
        slug = cat_dir.name
        latest_json = cat_dir / "latest.json"
        if not latest_json.exists():
            print(f"  [WARN] missing latest.json for {slug}")
            continue

        with open(latest_json, encoding="utf-8") as f:
            doc = json.load(f)

        vocab = categories_vocab.get(slug, {})
        data_type = doc.get("data_type", vocab.get("data_type", ""))

        # Files list
        files: dict[str, str] = {}
        for ext in ("json", "jsonl", "md"):
            p = cat_dir / f"latest.{ext}"
            if p.exists():
                files[ext] = f"{RAW_BASE}/data/{slug}/latest.{ext}"

        # Snapshots
        snapshots = []
        for p in sorted(cat_dir.glob("*.json")):
            if p.stem == "latest":
                continue
            snapshots.append({
                "date": p.stem,
                "json": f"{RAW_BASE}/data/{slug}/{p.name}",
                "md": f"{RAW_BASE}/data/{slug}/{p.stem}.md",
            })

        cat_entry = {
            "slug": slug,
            "display_name": vocab.get("display_name", slug),
            "data_type": data_type,
            "summary": vocab.get("summary", doc.get("summary", "")),
            "tags": vocab.get("tags", []),
            "source_url": vocab.get("source_url", ""),
            "update_cadence": vocab.get("update_cadence", "unknown"),
            "currency": vocab.get("currency"),
            "unit_system": vocab.get("unit_system"),
            "data_date": doc.get("data_date", "unknown"),
            "last_extracted_at": doc.get("extracted_at", ""),
            "row_count": doc.get("row_count", 0),
            "quality_flags": doc.get("quality_flags", []),
            "schema_url": f"{SCHEMA_BASE}/{data_type}.schema.json",
            "files": files,
            "snapshots": snapshots,
        }
        # Remove None values
        cat_entry = {k: v for k, v in cat_entry.items() if v is not None}
        categories_out.append(cat_entry)
        print(f"  added {slug} ({doc.get('row_count', 0)} rows)")

    manifest = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "description": "Malaysian construction cost data scraped from quantitysurveyoronline.com.my. Includes all-in rates, labour, materials, plant, preliminaries, and reference tables.",
        "source": "https://quantitysurveyoronline.com.my",
        "currency_default": "MYR",
        "usage": {
            "manifest": f"{RAW_BASE}/manifest.json",
            "readme": f"{RAW_BASE}/README.md",
            "example_json": f"{RAW_BASE}/data/materials-prices/latest.json",
            "example_md": f"{RAW_BASE}/data/materials-prices/latest.md",
            "llm_tip": (
                "Fetch manifest.json to discover all categories and their latest data URLs. "
                "Each category's latest.json is a self-describing document with schema_version, "
                "data_date, row_count, and structured rows. The .jsonl file has one row per line "
                "for streaming/partial reads."
            ),
        },
        "schemas": {
            "price_table": f"{SCHEMA_BASE}/price_table.schema.json",
            "reference_table": f"{SCHEMA_BASE}/reference_table.schema.json",
            "strength_group_list": f"{SCHEMA_BASE}/strength_group_list.schema.json",
        },
        "categories": categories_out,
    }
    return manifest


def main() -> None:
    print("Building manifest.json ...")
    manifest = build_manifest()
    out_path = REPO_ROOT / "manifest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {out_path.relative_to(REPO_ROOT)}")
    print(f"Total categories: {len(manifest['categories'])}")


if __name__ == "__main__":
    main()
