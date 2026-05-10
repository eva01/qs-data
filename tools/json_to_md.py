#!/usr/bin/env python3
"""Regenerate canonical markdown files from JSON.

Usage:
    python3 tools/json_to_md.py data/*/latest.json
    python3 tools/json_to_md.py  # process all latest.json files
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_price(price: dict[str, Any] | None) -> str:
    """Format a price dict back to display string."""
    if not price:
        return ""
    ptype = price.get("type", "tbd")
    ccy = price.get("currency", "MYR")
    ccy_sym = "RM" if ccy == "MYR" else ccy

    if ptype == "fixed":
        val = price.get("value", 0)
        return f"{ccy_sym} {val:,.2f}"
    elif ptype == "range":
        lo = price.get("min", 0)
        hi = price.get("max", 0)
        return f"{ccy_sym} {lo:,.2f} – {ccy_sym} {hi:,.2f}"
    elif ptype == "formula":
        return price.get("formula", "")
    elif ptype == "item":
        return "Item"
    else:
        return price.get("raw", "")


def fmt_unit(unit: str) -> str:
    return unit or ""


def md_cell(s: str) -> str:
    """Escape pipe characters in markdown table cells."""
    return s.replace("|", "\\|")


def md_row(*cells: str) -> str:
    parts = [md_cell(c) for c in cells]
    return "| " + " | ".join(parts) + " |"


# ---------------------------------------------------------------------------
# Price table -> markdown
# ---------------------------------------------------------------------------

def price_table_to_md(doc: dict[str, Any]) -> str:
    lines: list[str] = []

    # Frontmatter
    category = doc.get("category", "")
    source = doc.get("source", {})
    lines.append("---")
    lines.append(f"category: {category}")
    if source.get("image"):
        lines.append(f"source_image: {source['image']}")
    lines.append(f"data_date: {doc.get('data_date', 'unknown')}")
    lines.append(f"extracted_at: {doc.get('extracted_at', '')}")
    extraction = doc.get("extraction", {})
    if extraction.get("ocr_engine"):
        lines.append(f"ocr_engine: {extraction['ocr_engine']}")
    if extraction.get("cross_check_confidence") is not None:
        lines.append(f"cross_check_confidence: {extraction['cross_check_confidence']}")
    lines.append("---")
    lines.append("")

    # Table header
    lines.append(md_row("S/N", "Description", "Price (RM)", "Unit", "Remarks"))
    lines.append(md_row(":---", ":---", ":---", ":---", ":---"))

    current_section = None
    for row in doc.get("rows", []):
        section = row.get("section", "_")
        section_name = row.get("section_name", "")

        # Emit section header when section changes
        if section != "_" and section != current_section and row.get("item_no") != "0":
            lines.append(md_row("", f"**({section}) {section_name}**", "", "", ""))
            current_section = section

        item_no = row.get("item_no", "")
        if item_no == "0":
            # Section-level item (like site security with a rate)
            price_str = fmt_price(row.get("price"))
            unit_str = fmt_unit(row.get("unit", ""))
            # Also include alt prices if any
            alt = row.get("alt_prices", [])
            if alt:
                alt_price_str = " / ".join(fmt_price(a.get("price")) for a in alt if a.get("price"))
                alt_unit_str = " / ".join(a.get("unit", "") for a in alt if a.get("unit"))
                if alt_price_str:
                    price_str = f"{price_str} / {alt_price_str}"
                if alt_unit_str:
                    unit_str = f"{unit_str} / {alt_unit_str}"
            lines.append(md_row(
                "",
                f"**({section}) {section_name}**",
                price_str,
                unit_str,
                row.get("remarks", ""),
            ))
            current_section = section
            continue

        price_str = fmt_price(row.get("price"))
        unit_str = fmt_unit(row.get("unit", ""))

        # Handle alt prices (e.g. dual day/month rates)
        alt = row.get("alt_prices", [])
        if alt:
            alt_prices_str = " / ".join(
                fmt_price(a.get("price")) for a in alt if a.get("price")
            )
            alt_units_str = " / ".join(
                a.get("unit", a.get("unit_raw", "")) for a in alt if a.get("unit") or a.get("unit_raw")
            )
            if alt_prices_str:
                price_str = f"{price_str} / {alt_prices_str}"
            if alt_units_str:
                unit_str = f"{unit_str} / {alt_units_str}"

        lines.append(md_row(
            item_no,
            row.get("description", ""),
            price_str,
            unit_str,
            row.get("remarks", ""),
        ))

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reference table -> markdown
# ---------------------------------------------------------------------------

def reference_table_to_md(doc: dict[str, Any]) -> str:
    lines: list[str] = []
    category = doc.get("category", "")
    source = doc.get("source", {})

    # Frontmatter
    lines.append("---")
    lines.append(f"category: {category}")
    if source.get("image"):
        lines.append(f"source_image: {source['image']}")
    lines.append(f"data_date: {doc.get('data_date', 'static')}")
    lines.append(f"extracted_at: {doc.get('extracted_at', '')}")
    if source.get("ocr_engine"):
        lines.append(f"ocr_engine: {source['ocr_engine']}")
    lines.append("---")
    lines.append("")

    if category == "conversion-table":
        _conversion_table_md(doc, lines)
    elif category == "rebar-kg-per-m":
        _rebar_kg_per_m_md(doc, lines)
    elif category == "rebar-hook-bend-lap":
        _rebar_hook_bend_lap_md(doc, lines)
    elif category == "building-element-steel-content":
        _building_element_steel_md(doc, lines)
    elif category == "weight-of-building-materials":
        _weight_of_building_materials_md(doc, lines)
    else:
        lines.append("*Reference table — see JSON for structured data.*")

    lines.append("")
    return "\n".join(lines)


def _fmt_value(value: dict | None) -> str:
    if not value:
        return ""
    vtype = value.get("type", "tbd")
    unit = value.get("unit", "")
    if vtype == "fixed":
        v = value.get("value", "")
        return f"{v} {unit}".strip()
    elif vtype == "range":
        lo = value.get("min", "")
        hi = value.get("max", "")
        return f"{lo} – {hi} {unit}".strip()
    return value.get("raw", "")


def _conversion_table_md(doc: dict, lines: list) -> None:
    lines.append(md_row("To convert", "Multiply by"))
    lines.append(md_row(":---", ":---"))
    current_dim = None
    for row in doc.get("rows", []):
        dim = row.get("dimension", "")
        if dim != current_dim:
            lines.append(md_row(f"**{dim}**", ""))
            current_dim = dim
        from_u = row.get("from_unit", "")
        to_u = row.get("to_unit", "")
        mult = row.get("multiplier", "")
        lines.append(md_row(f"{from_u} into {to_u}", str(mult) if mult is not None else ""))


def _rebar_kg_per_m_md(doc: dict, lines: list) -> None:
    lines.append(md_row(
        "Diameter (mm)", "Cross Sectional Area (mm²)",
        "Mass Per Meter (kg/m)", "Mass Per 12 Meter (kg/12m)"
    ))
    lines.append(md_row(":---", ":---", ":---", ":---"))
    for row in doc.get("rows", []):
        lines.append(md_row(
            str(row.get("diameter_mm", "")),
            str(row.get("cross_section_area_mm2", "")),
            str(row.get("mass_per_m_kg", "")),
            str(row.get("mass_per_12m_kg", "")),
        ))


def _rebar_hook_bend_lap_md(doc: dict, lines: list) -> None:
    """Reconstruct transposed table format."""
    rows = doc.get("rows", [])
    if not rows:
        return

    # Collect bar sizes
    bar_sizes = sorted(set(r["bar_size_mm"] for r in rows))

    for steel_type in ["mild_steel", "high_yield"]:
        type_rows = [r for r in rows if r.get("steel_type") == steel_type]
        if not type_rows:
            continue

        type_label = (
            "1. For Mild Steel Bars Complying With BS 4449"
            if steel_type == "mild_steel"
            else "2. For High Yield Bars Complying With BS 4449 or BS 4461"
        )
        # Header row
        header_cells = [type_label] + [""] * len(bar_sizes)
        lines.append(md_row(*header_cells))
        sep_cells = [":---"] + [":---:"] * len(bar_sizes)
        lines.append(md_row(*sep_cells))

        # Bar size row
        size_cells = ["Bar size (D), mm"] + [str(s) for s in bar_sizes]
        lines.append(md_row(*size_cells))

        # Measurements
        measurement_order = [
            "hook_allowance_mm",
            "bend_allowance_mm",
            "rebar_lapping_mm",
            "tying_allowance_mm",
        ]
        measurement_labels = {
            "hook_allowance_mm": lambda m: f"Hook allowance ({int(m)}D), mm" if m else "Hook allowance, mm",
            "bend_allowance_mm": lambda m: f"Bend allowance ({m}D), mm" if m else "Bend allowance, mm",
            "rebar_lapping_mm": lambda m: f"Rebar lapping ({int(m)}D), mm" if m else "Rebar lapping, mm",
            "tying_allowance_mm": lambda m: f"Tying allowance ({int(m)}D), mm" if m else "Tying allowance, mm",
        }

        for mtype in measurement_order:
            mrows = [r for r in type_rows if r.get("measurement") == mtype]
            if not mrows:
                continue
            mult = mrows[0].get("formula_multiplier")
            label = measurement_labels[mtype](mult)
            by_size = {r["bar_size_mm"]: r.get("value_mm") for r in mrows}
            value_cells = [label] + [str(by_size.get(s, "")) for s in bar_sizes]
            lines.append(md_row(*value_cells))


def _building_element_steel_md(doc: dict, lines: list) -> None:
    lines.append(md_row("No.", "Description", "Rate"))
    lines.append(md_row(":---", ":---", ":---"))
    for row in doc.get("rows", []):
        lines.append(md_row(
            row.get("item_no", ""),
            row.get("description", ""),
            _fmt_value(row.get("value")),
        ))


def _weight_of_building_materials_md(doc: dict, lines: list) -> None:
    lines.append(md_row("No.", "Description", "Value", "Remarks"))
    lines.append(md_row(":---", ":---", ":---", ":---"))
    current_section = None
    for row in doc.get("rows", []):
        section = row.get("section", "_")
        section_name = row.get("section_name", "")
        if section != "_" and section != current_section:
            lines.append(md_row("", f"**({section}) {section_name}**", "", ""))
            current_section = section
        lines.append(md_row(
            row.get("item_no", ""),
            row.get("description", ""),
            _fmt_value(row.get("value")),
            row.get("remarks", ""),
        ))


# ---------------------------------------------------------------------------
# Strength group list -> markdown
# ---------------------------------------------------------------------------

def strength_group_list_to_md(doc: dict[str, Any]) -> str:
    lines: list[str] = []
    category = doc.get("category", "")
    source = doc.get("source", {})

    lines.append("---")
    lines.append(f"category: {category}")
    lines.append(f"source: {source.get('url', '')}")
    lines.append(f"data_date: {doc.get('data_date', 'static')}")
    lines.append(f"extracted_at: {doc.get('extracted_at', '')}")
    lines.append("---")
    lines.append("")
    lines.append("TIMBER STRENGTH GROUP")
    lines.append("")

    for row in doc.get("rows", []):
        lines.append(f"GROUP {row['group']}")
        for species in row.get("species", []):
            lines.append(species)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def json_to_md(doc: dict[str, Any]) -> str:
    dtype = doc.get("data_type", "")
    if dtype == "price_table":
        return price_table_to_md(doc)
    elif dtype == "reference_table":
        return reference_table_to_md(doc)
    elif dtype == "strength_group_list":
        return strength_group_list_to_md(doc)
    else:
        return f"# Unknown data type: {dtype}\n"


def main() -> None:
    if len(sys.argv) > 1:
        json_files = [Path(p) for p in sys.argv[1:] if p.endswith(".json")]
    else:
        json_files = sorted(DATA_DIR.rglob("latest.json"))

    if not json_files:
        print("No JSON files found.")
        return

    errors = 0
    for json_path in json_files:
        json_path = json_path.resolve()
        try:
            rel = json_path.relative_to(REPO_ROOT)
        except ValueError:
            rel = json_path
        print(f"Processing {rel} ...")
        try:
            with open(json_path, encoding="utf-8") as f:
                doc = json.load(f)
            md_content = json_to_md(doc)
            stem = json_path.stem  # "latest" or date
            md_path = json_path.parent / f"{stem}.md"
            md_path.write_text(md_content, encoding="utf-8")
            try:
                md_rel = md_path.relative_to(REPO_ROOT)
            except ValueError:
                md_rel = md_path
            print(f"  wrote {md_rel}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            errors += 1

    print(f"\nDone. {len(json_files)} files processed, {errors} errors.")


if __name__ == "__main__":
    main()
