#!/usr/bin/env python3
"""Convert qs-data markdown files to canonical JSON + JSONL.

Usage:
    python3 tools/md_to_json.py data/*/latest.md
    python3 tools/md_to_json.py data/materials-prices/latest.md
    python3 tools/md_to_json.py  # process all md files
"""

from __future__ import annotations

import json
import re
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
VOCAB_DIR = REPO_ROOT / "vocab"
DATA_DIR = REPO_ROOT / "data"
SCHEMA_BASE = "https://raw.githubusercontent.com/eva01/qs-data/master/schemas"
SCHEMA_VERSION = "1.0.0"

# Categories that are price tables (have RM prices)
PRICE_TABLE_CATEGORIES = {
    "all-in-rates-architecture",
    "all-in-rates-structure",
    "labour-rates",
    "materials-prices",
    "plant-equipment-rates",
    "preliminaries-rates",
}

# Categories that are reference tables (no prices)
REFERENCE_TABLE_CATEGORIES = {
    "building-element-steel-content",
    "conversion-table",
    "rebar-hook-bend-lap",
    "rebar-kg-per-m",
    "weight-of-building-materials",
}

# ---------------------------------------------------------------------------
# Vocab / unit normalization
# ---------------------------------------------------------------------------

_UNITS: dict[str, str] = {}

def _load_units() -> None:
    path = VOCAB_DIR / "units.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            _UNITS.update(json.load(f))

def normalize_unit(raw: str) -> str:
    """Map raw unit string to canonical form."""
    raw = raw.strip()
    if raw in _UNITS:
        return _UNITS[raw]
    # Try case-insensitive
    lower = raw.lower()
    for k, v in _UNITS.items():
        if k.lower() == lower:
            return v
    return raw  # return as-is if unknown

# ---------------------------------------------------------------------------
# YAML frontmatter parser
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extract YAML-like frontmatter and return (meta, body)."""
    meta: dict[str, Any] = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    for line in fm_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
    return meta, body

# ---------------------------------------------------------------------------
# Price parsing
# ---------------------------------------------------------------------------

_RM_RE = re.compile(
    r"RM\s*([\d,]+(?:\.\d+)?)"
    r"(?:\s*[-–—]\s*RM\s*([\d,]+(?:\.\d+)?))?",
    re.IGNORECASE,
)
_FORMULA_RE = re.compile(
    r"([\d.]+%)\s*[Oo]f\s+([A-Za-z\s]+)",
    re.IGNORECASE,
)
_CURRENCY_TAG_RE = re.compile(r"(RM|SGD|USD)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE)


def _parse_number(s: str) -> float:
    return float(s.replace(",", ""))


def parse_price(raw: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Parse a price string into structured form.
    Returns (primary_price, alt_prices).
    """
    raw = raw.strip()
    alt_prices: list[dict[str, Any]] = []

    if not raw:
        return {"type": "tbd", "raw": raw}, alt_prices

    # Formula: 0.125% Of Contract Sum
    m_formula = _FORMULA_RE.search(raw)
    if m_formula:
        pct = m_formula.group(1)
        basis = m_formula.group(2).strip().lower().replace(" ", "_")
        return {"type": "formula", "formula": f"{pct} of {basis}", "raw": raw}, alt_prices

    # Item / Sum
    if raw.lower() in ("item", "sum", "l/s", "ls"):
        return {"type": "item", "raw": raw}, alt_prices

    # Check if there are multiple slash-separated prices (e.g. "RM550.00 / RM8,300.00")
    # or multi-currency (e.g. "RM 435.00 / SGD 145.00")
    slash_parts = [p.strip() for p in raw.split("/") if p.strip()]
    if len(slash_parts) >= 2:
        prices_found = []
        for part in slash_parts:
            currencies = _CURRENCY_TAG_RE.findall(part)
            for ccy, val in currencies:
                prices_found.append((ccy.upper(), _parse_number(val), part))
        if len(prices_found) >= 2:
            # Primary is first
            primary_ccy, primary_val, primary_raw = prices_found[0]
            primary = {
                "type": "fixed",
                "value": primary_val,
                "currency": primary_ccy,
                "raw": primary_raw.strip(),
            }
            for ccy, val, part_raw in prices_found[1:]:
                alt_prices.append({
                    "price": {
                        "type": "fixed",
                        "value": val,
                        "currency": ccy,
                        "raw": part_raw.strip(),
                    }
                })
            return primary, alt_prices

    # Single RM price or range
    m = _RM_RE.search(raw)
    if m:
        val1 = _parse_number(m.group(1))
        if m.group(2):
            val2 = _parse_number(m.group(2))
            return {
                "type": "range",
                "min": min(val1, val2),
                "max": max(val1, val2),
                "currency": "MYR",
                "raw": raw,
            }, alt_prices
        return {
            "type": "fixed",
            "value": val1,
            "currency": "MYR",
            "raw": raw,
        }, alt_prices

    # Non-RM but numeric-looking (like percentage amounts without "Of")
    if raw.lower() in ("item", "sum"):
        return {"type": "item", "raw": raw}, alt_prices

    return {"type": "tbd", "raw": raw}, alt_prices


# ---------------------------------------------------------------------------
# Unit parsing with dual-unit handling
# ---------------------------------------------------------------------------

def parse_unit_field(raw: str) -> tuple[str, str, list[dict[str, Any]]]:
    """
    Parse a unit field that may contain dual units like "Day (8 hours) / Month".
    Returns (canonical_unit, raw_unit, alt_unit_list).
    """
    raw = raw.strip()
    if "/" in raw:
        parts = [p.strip() for p in raw.split("/")]
        primary_unit = normalize_unit(parts[0])
        alt_units = [{"unit": normalize_unit(p), "unit_raw": p} for p in parts[1:]]
        return primary_unit, raw, alt_units
    return normalize_unit(raw), raw, []


# ---------------------------------------------------------------------------
# Section header detection
# ---------------------------------------------------------------------------

_SECTION_RE = re.compile(
    r"^\*?\*?\(([A-Z])\)\*?\*?\s+(.*?)\*?\*?$"
)

def detect_section_header(cells: list[str]) -> tuple[str | None, str | None]:
    """
    Returns (section_code, section_name) if row is a section header, else (None, None).
    A section header has bold text like **(A) SECTION NAME** or **(A)** | **NAME**.
    """
    # Flatten all cells into one string to check
    full = " ".join(c.strip() for c in cells if c.strip())
    # Pattern: **(A) SECTION NAME** or ** (A) ** ** SECTION NAME **
    m = re.search(r"\*\*\(?([A-Z])\)?\*?\*?\**\s*\**([^*]+)\*\*", full)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Pattern in separate cells: cells[0]="**(A)**", cells[1]="**NAME**"
    if len(cells) >= 2:
        m0 = re.match(r"^\*\*\(([A-Z])\)\*\*$", cells[0].strip())
        m1 = re.match(r"^\*\*(.+)\*\*$", cells[1].strip())
        if m0 and m1:
            return m0.group(1), m1.group(1)
    return None, None


def is_section_header_row(cells: list[str]) -> tuple[str | None, str | None]:
    """Check if a markdown table row is a section header."""
    non_empty = [c for c in cells if c.strip()]
    if not non_empty:
        return None, None
    full = " ".join(non_empty)
    # Match **(A) SECTION NAME** pattern (anywhere in the row)
    m = re.search(r"\*\*\s*\(([A-Z])\)\s*([^*]+?)\*\*", full)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Match split-cell format: first non-empty cell is **(A)**, second is **NAME**
    ne = [c.strip() for c in cells if c.strip()]
    if len(ne) >= 2:
        m0 = re.match(r"^\*\*\(([A-Z])\)\*\*$", ne[0])
        m1 = re.match(r"^\*\*(.+?)\*\*$", ne[1])
        if m0 and m1:
            return m0.group(1), m1.group(1)
    return None, None


# ---------------------------------------------------------------------------
# Markdown table parser
# ---------------------------------------------------------------------------

def parse_md_table(body: str) -> list[list[str]]:
    """Parse a markdown table into list of rows, each row is list of cell strings."""
    rows = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[-: |]+\|$", line):
            continue  # skip separator rows
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    return rows


# ---------------------------------------------------------------------------
# Category-specific parsers
# ---------------------------------------------------------------------------

def parse_price_table(category: str, meta: dict, body: str) -> dict[str, Any]:
    """Parse a price table markdown into structured JSON."""
    rows_raw = parse_md_table(body)
    if not rows_raw:
        return {}

    quality_flags: list[str] = []
    data_rows: list[dict[str, Any]] = []
    current_section = "_"
    current_section_name = ""
    row_counter: dict[str, int] = {}

    # Detect column layout by examining header row
    header = rows_raw[0] if rows_raw else []
    header_lower = [h.lower() for h in header]

    # Determine if table has S/N + No. columns (materials-prices, preliminaries-rates style)
    has_sn_no = (
        len(header) >= 5
        and "s/n" in header_lower[0]
        and ("no" in header_lower[1] or "no." in header_lower[1])
    )
    # Determine if it's a 4-col table (S/N | DESCRIPTION | RATE | UNIT) or 6-col
    is_6col = has_sn_no or len(header) >= 6

    # Skip header row
    table_rows = rows_raw[1:]

    # Categorize columns:
    # 4-col: [sn, description, rate, unit]
    # 6-col: [sn, no, description, rate, unit, remarks]

    for row_cells in table_rows:
        # Pad to expected width
        while len(row_cells) < max(6 if is_6col else 4, len(row_cells)):
            row_cells.append("")

        if is_6col:
            sn_cell = row_cells[0] if len(row_cells) > 0 else ""
            no_cell = row_cells[1] if len(row_cells) > 1 else ""
            desc_cell = row_cells[2] if len(row_cells) > 2 else ""
            rate_cell = row_cells[3] if len(row_cells) > 3 else ""
            unit_cell = row_cells[4] if len(row_cells) > 4 else ""
            remarks_cell = row_cells[5] if len(row_cells) > 5 else ""
            item_source = no_cell
        else:
            sn_cell = row_cells[0] if len(row_cells) > 0 else ""
            desc_cell = row_cells[1] if len(row_cells) > 1 else ""
            rate_cell = row_cells[2] if len(row_cells) > 2 else ""
            unit_cell = row_cells[3] if len(row_cells) > 3 else ""
            remarks_cell = ""
            item_source = sn_cell

        # Check for section header
        sec_code, sec_name = is_section_header_row(row_cells)
        if sec_code:
            current_section = sec_code
            current_section_name = sec_name.strip("* ").strip()
            # Also check if this row has rate info (like "(B) Site security | RM8 - RM10 | Hour")
            # Some sections have inline rate
            if rate_cell.strip() or unit_cell.strip():
                # This is a section-level item
                price, alt_prices = parse_price(rate_cell)
                unit, unit_raw, alt_units = parse_unit_field(unit_cell)
                # Merge alt units into alt prices
                for i, au in enumerate(alt_units):
                    if i < len(alt_prices):
                        alt_prices[i].update(au)
                    else:
                        alt_prices.append(au)
                item_no = "0"  # section-level item
                row_id = f"{category}:{current_section}:{item_no}"
                row: dict[str, Any] = {
                    "row_id": row_id,
                    "section": current_section,
                    "section_name": current_section_name,
                    "item_no": item_no,
                    "description": current_section_name,
                    "price": price,
                    "unit": unit,
                    "unit_raw": unit_raw,
                }
                if alt_prices:
                    row["alt_prices"] = alt_prices
                if remarks_cell.strip():
                    row["remarks"] = remarks_cell.strip()
                data_rows.append(row)
            continue

        # Skip rows with no description and no rate
        if not desc_cell.strip() and not rate_cell.strip():
            continue

        # Determine item_no
        item_no = item_source.strip().strip("*").strip()
        if not item_no:
            # Use auto-counter if no item number
            key = f"{current_section}"
            row_counter[key] = row_counter.get(key, 0) + 1
            item_no = f"_{row_counter[key]}"

        # Clean description
        desc = desc_cell.strip().strip("*").strip()
        if not desc:
            continue

        # Parse price
        price, alt_prices = parse_price(rate_cell.strip())

        # Parse unit (may be dual e.g. "Day (8 hours) / Month")
        unit, unit_raw, alt_units = parse_unit_field(unit_cell.strip())

        # Merge alt units into alt prices for dual-rate rows
        if alt_units and alt_prices:
            for i, au in enumerate(alt_units):
                if i < len(alt_prices):
                    alt_prices[i].update(au)
        elif alt_units and not alt_prices:
            # We have dual unit but only one price — mark as needs_review
            quality_flags.append(f"dual-unit with single price at {category}:{current_section}:{item_no}")

        row_id = f"{category}:{current_section}:{item_no}"
        row = {
            "row_id": row_id,
            "section": current_section,
            "section_name": current_section_name,
            "item_no": item_no,
            "description": desc,
            "price": price,
            "unit": unit,
            "unit_raw": unit_raw,
        }
        if alt_prices:
            row["alt_prices"] = alt_prices
        if remarks_cell.strip():
            row["remarks"] = remarks_cell.strip("* ").strip()
        if price.get("type") == "tbd" and not rate_cell.strip():
            row["needs_review"] = True

        data_rows.append(row)

    return {
        "schema_version": SCHEMA_VERSION,
        "$schema": f"{SCHEMA_BASE}/price_table.schema.json",
        "category": category,
        "data_type": "price_table",
        "source": {
            "image": meta.get("source_image", ""),
            "url": f"https://quantitysurveyoronline.com.my/{category}.html",
        },
        "data_date": meta.get("data_date", "unknown"),
        "extracted_at": meta.get("extracted_at", datetime.now(timezone.utc).isoformat()),
        "extraction": {k: v for k, v in {
            "ocr_engine": meta.get("ocr_engine", ""),
            "cross_check_confidence": (
                float(meta["cross_check_confidence"])
                if "cross_check_confidence" in meta else None
            ),
        }.items() if v is not None and v != ""},
        "currency": "MYR",
        "unit_system": "metric",
        "row_count": len(data_rows),
        "quality_flags": quality_flags,
        "rows": data_rows,
    }


def parse_building_element_steel(meta: dict, body: str) -> dict[str, Any]:
    """Parse building-element-steel-content table."""
    rows_raw = parse_md_table(body)
    if not rows_raw:
        return {}

    quality_flags: list[str] = []
    data_rows = []

    # Skip header row
    for cells in rows_raw[1:]:
        if len(cells) < 3:
            continue
        no_cell = cells[0].strip()
        desc_cell = cells[1].strip()
        rate_cell = cells[2].strip()

        if not desc_cell or desc_cell.startswith("---"):
            continue

        # Parse rate: may be range like "50 - 250 kg/m3" or "385-135 kg/m3"
        # Note: "385-135" is a corrupt OCR row — likely "85-135"
        value: dict[str, Any] = {}
        unit = ""

        # Split numeric part from unit
        m = re.match(
            r"([\d.]+)\s*[-–]\s*([\d.]+)\s*(kg/m[23²³]?|kg/m²|kg/m³)?",
            rate_cell
        )
        if m:
            v1, v2 = float(m.group(1)), float(m.group(2))
            unit_raw = (m.group(3) or "kg/m³").strip()
            unit = normalize_unit(unit_raw) if unit_raw in _UNITS else unit_raw
            if v1 > v2:
                # Likely corrupt OCR (e.g. "385-135" should be "85-135")
                quality_flags.append(
                    f"corrupt_range: row {no_cell} has min > max: {rate_cell!r} — min/max swapped"
                )
                v1, v2 = v2, v1
            value = {"type": "range", "min": v1, "max": v2, "unit": unit}
        else:
            # Single value
            m2 = re.match(r"([\d.]+)\s*(kg/m[23²³]?|kg/m²|kg/m³)?", rate_cell)
            if m2:
                unit_raw = (m2.group(2) or "kg/m³").strip()
                unit = normalize_unit(unit_raw) if unit_raw in _UNITS else unit_raw
                value = {"type": "fixed", "value": float(m2.group(1)), "unit": unit}
            else:
                value = {"type": "tbd", "raw": rate_cell}
                quality_flags.append(f"unparsed_rate: row {no_cell}: {rate_cell!r}")

        data_rows.append({
            "row_id": f"building-element-steel-content:_:{no_cell}",
            "item_no": no_cell,
            "description": desc_cell.strip("*").strip(),
            "value": value,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "$schema": f"{SCHEMA_BASE}/reference_table.schema.json",
        "category": "building-element-steel-content",
        "data_type": "reference_table",
        "source": {
            "image": meta.get("source_image", ""),
            "url": "https://quantitysurveyoronline.com.my/building-element-steel-content.html",
            "ocr_engine": meta.get("ocr_engine", ""),
        },
        "data_date": "static",
        "extracted_at": meta.get("extracted_at", datetime.now(timezone.utc).isoformat()),
        "columns": [
            {"name": "item_no", "description": "Row number"},
            {"name": "description", "description": "Building element type"},
            {"name": "value", "description": "Steel content (kg/m³), fixed or range"},
        ],
        "row_count": len(data_rows),
        "quality_flags": quality_flags,
        "rows": data_rows,
    }


def parse_conversion_table(meta: dict, body: str) -> dict[str, Any]:
    """Parse conversion table markdown."""
    quality_flags: list[str] = []
    data_rows = []
    current_dimension = "AREA"  # default; only area data present

    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[-: |]+\|$", line):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue

        left, right = cells[0].strip("*").strip(), cells[1].strip("*").strip()

        # Dimension header row (e.g. "**AREA**" or "AREA")
        if re.match(r"^[A-Z ]+$", left) and not right:
            current_dimension = left
            continue
        if "To convert" in left or "to convert" in left.lower():
            continue  # header row

        # Parse conversion row: "Sq. Feet into Sq. Metres" | "0.092903"
        if "into" in left.lower() or "into" in left:
            parts = re.split(r"\s+into\s+", left, flags=re.IGNORECASE)
            if len(parts) == 2:
                from_unit = parts[0].strip()
                to_unit = parts[1].strip()
                try:
                    multiplier = float(right.replace(",", ""))
                except ValueError:
                    quality_flags.append(f"non-numeric multiplier: {right!r} for {left!r}")
                    multiplier = None
                data_rows.append({
                    "row_id": f"conversion-table:{current_dimension.lower()}:{len(data_rows)+1}",
                    "dimension": current_dimension,
                    "from_unit": from_unit,
                    "to_unit": to_unit,
                    "multiplier": multiplier,
                })
        elif left and right:
            # Unexpected format
            quality_flags.append(f"unparsed_row: {left!r} | {right!r}")

    return {
        "schema_version": SCHEMA_VERSION,
        "$schema": f"{SCHEMA_BASE}/reference_table.schema.json",
        "category": "conversion-table",
        "data_type": "reference_table",
        "source": {
            "image": meta.get("source_image", ""),
            "url": "https://quantitysurveyoronline.com.my/conversion-table.html",
            "ocr_engine": meta.get("ocr_engine", ""),
        },
        "data_date": "static",
        "extracted_at": meta.get("extracted_at", datetime.now(timezone.utc).isoformat()),
        "columns": [
            {"name": "dimension", "description": "Measurement dimension, e.g. AREA, LENGTH"},
            {"name": "from_unit", "description": "Source unit"},
            {"name": "to_unit", "description": "Target unit"},
            {"name": "multiplier", "description": "Multiply from_unit by this to get to_unit"},
        ],
        "row_count": len(data_rows),
        "quality_flags": quality_flags,
        "rows": data_rows,
    }


def parse_rebar_kg_per_m(meta: dict, body: str) -> dict[str, Any]:
    """Parse rebar kg/m reference table."""
    rows_raw = parse_md_table(body)
    quality_flags: list[str] = []
    data_rows = []

    for cells in rows_raw[1:]:
        if len(cells) < 4:
            continue
        try:
            diameter = int(cells[0].strip())
            cross_section = float(cells[1].strip())
            mass_per_m = float(cells[2].strip())
            mass_per_12m = float(cells[3].strip())
        except ValueError:
            quality_flags.append(f"unparsed_row: {cells!r}")
            continue
        data_rows.append({
            "row_id": f"rebar-kg-per-m:_:{diameter}",
            "diameter_mm": diameter,
            "cross_section_area_mm2": cross_section,
            "mass_per_m_kg": mass_per_m,
            "mass_per_12m_kg": mass_per_12m,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "$schema": f"{SCHEMA_BASE}/reference_table.schema.json",
        "category": "rebar-kg-per-m",
        "data_type": "reference_table",
        "source": {
            "image": meta.get("source_image", ""),
            "url": "https://quantitysurveyoronline.com.my/rebar-kg-per-m.html",
            "ocr_engine": meta.get("ocr_engine", ""),
        },
        "data_date": "static",
        "extracted_at": meta.get("extracted_at", datetime.now(timezone.utc).isoformat()),
        "columns": [
            {"name": "diameter_mm", "unit": "mm", "description": "Bar diameter in mm"},
            {"name": "cross_section_area_mm2", "unit": "mm²", "description": "Cross-sectional area"},
            {"name": "mass_per_m_kg", "unit": "kg/m", "description": "Mass per linear metre"},
            {"name": "mass_per_12m_kg", "unit": "kg/12m", "description": "Mass per 12-metre bar"},
        ],
        "row_count": len(data_rows),
        "quality_flags": quality_flags,
        "rows": data_rows,
    }


def parse_rebar_hook_bend_lap(meta: dict, body: str) -> dict[str, Any]:
    """Parse rebar hook/bend/lap table — a transposed table with bar sizes as columns."""
    quality_flags: list[str] = []
    rows_raw = parse_md_table(body)
    data_rows = []

    # The table has bar sizes as column headers and measurement types as row labels
    # We emit one record per (steel_type, bar_size, measurement_type)
    # Find header row with bar sizes
    header_row = None
    bar_sizes: list[int] = []
    current_steel_type = ""

    for cells in rows_raw:
        if not cells:
            continue
        first = cells[0].strip().strip("*")

        # Steel type header row
        m_type = re.match(r"(\d+)\.\s+For\s+(.+?)(?:\(|$)", first, re.IGNORECASE)
        if m_type or "For Mild Steel" in first or "For High Yield" in first:
            if "Mild Steel" in first:
                current_steel_type = "mild_steel"
            elif "High Yield" in first:
                current_steel_type = "high_yield"
            # Skip this row as data row
            continue

        # Bar size header row
        if first.lower() in ("bar size (d), mm", "description"):
            try:
                bar_sizes = [int(c.strip()) for c in cells[1:] if c.strip()]
            except ValueError:
                pass
            continue

        # Data row
        if first and bar_sizes:
            values = []
            for c in cells[1:]:
                c = c.strip()
                try:
                    values.append(int(c))
                except ValueError:
                    values.append(None)

            # Determine measurement type
            mtype = None
            unit = "mm"
            if "hook allowance" in first.lower():
                mtype = "hook_allowance_mm"
                # Extract multiplier: "Hook allowance (9D)" -> 9
                m_mult = re.search(r"\((\d+(?:\.\d+)?)D\)", first)
                multiplier = float(m_mult.group(1)) if m_mult else None
            elif "bend allowance" in first.lower():
                mtype = "bend_allowance_mm"
                m_mult = re.search(r"\((\d+(?:\.\d+)?)D\)", first)
                multiplier = float(m_mult.group(1)) if m_mult else None
            elif "lapping" in first.lower():
                mtype = "rebar_lapping_mm"
                m_mult = re.search(r"\((\d+(?:\.\d+)?)D\)", first)
                multiplier = float(m_mult.group(1)) if m_mult else None
            elif "tying" in first.lower():
                mtype = "tying_allowance_mm"
                m_mult = re.search(r"\((\d+(?:\.\d+)?)D\)", first)
                multiplier = float(m_mult.group(1)) if m_mult else None
            else:
                continue

            for i, bar_size in enumerate(bar_sizes):
                val = values[i] if i < len(values) else None
                data_rows.append({
                    "row_id": f"rebar-hook-bend-lap:{current_steel_type or '_'}:{mtype}:{bar_size}",
                    "steel_type": current_steel_type,
                    "bar_size_mm": bar_size,
                    "measurement": mtype,
                    "formula_multiplier": multiplier if 'multiplier' in dir() else None,
                    "value_mm": val,
                })

    return {
        "schema_version": SCHEMA_VERSION,
        "$schema": f"{SCHEMA_BASE}/reference_table.schema.json",
        "category": "rebar-hook-bend-lap",
        "data_type": "reference_table",
        "source": {
            "image": meta.get("source_image", ""),
            "url": "https://quantitysurveyoronline.com.my/rebar-hook-bend-lap.html",
            "ocr_engine": meta.get("ocr_engine", ""),
        },
        "data_date": "static",
        "extracted_at": meta.get("extracted_at", datetime.now(timezone.utc).isoformat()),
        "columns": [
            {"name": "steel_type", "description": "mild_steel or high_yield"},
            {"name": "bar_size_mm", "unit": "mm", "description": "Bar diameter"},
            {"name": "measurement", "description": "hook_allowance_mm, bend_allowance_mm, rebar_lapping_mm, tying_allowance_mm"},
            {"name": "formula_multiplier", "description": "Multiplier applied to D (e.g. 9 for hook allowance 9D)"},
            {"name": "value_mm", "unit": "mm", "description": "Calculated minimum value in mm"},
        ],
        "row_count": len(data_rows),
        "quality_flags": quality_flags,
        "rows": data_rows,
    }


def parse_weight_of_building_materials(meta: dict, body: str) -> dict[str, Any]:
    """Parse weight-of-building-materials table."""
    quality_flags: list[str] = []
    rows_raw = parse_md_table(body)
    data_rows = []
    current_section = "_"
    current_section_name = ""

    # This table has varying formats (5-col and 6-col)
    # 5-col: No. | Description | Rate | Unit | Remarks
    # 6-col: S/N | No. | Description | Rate | Unit | Remarks
    header = rows_raw[0] if rows_raw else []
    header_lower = [h.lower().strip() for h in header]
    is_6col = len(header) >= 6 and "s/n" in header_lower[0]

    for cells in rows_raw[1:]:
        if is_6col:
            sn = cells[0].strip() if len(cells) > 0 else ""
            no_cell = cells[1].strip() if len(cells) > 1 else ""
            desc_cell = cells[2].strip() if len(cells) > 2 else ""
            # In 6-col variant, rate and unit are combined in one cell
            # e.g. "25.9 kg/sq.m"
            rate_unit_cell = cells[4].strip() if len(cells) > 4 else ""
            # cells[3] appears to be empty (Rate col)
            remarks_cell = cells[5].strip() if len(cells) > 5 else ""
        else:
            sn = cells[0].strip() if len(cells) > 0 else ""
            no_cell = cells[0].strip() if len(cells) > 0 else ""
            desc_cell = cells[1].strip() if len(cells) > 1 else ""
            rate_cell = cells[2].strip() if len(cells) > 2 else ""
            unit_cell = cells[3].strip() if len(cells) > 3 else ""
            remarks_cell = cells[4].strip() if len(cells) > 4 else ""
            rate_unit_cell = f"{rate_cell} {unit_cell}".strip()

        # Section header check
        sec_code, sec_name = is_section_header_row(cells)
        if sec_code:
            current_section = sec_code
            current_section_name = sec_name.strip("* ").strip()
            continue

        desc = desc_cell.strip("*").strip()
        if not desc:
            continue

        # Parse rate+unit from combined cell
        value_parsed: dict[str, Any] = {}
        if rate_unit_cell:
            # e.g. "25.9 kg/sq.m" or "2002 kg/cu.m"
            m = re.match(
                r"([\d.]+)\s*(?:[-–]\s*([\d.]+))?\s*(kg/(?:sq\.m|cu\.m|m[23²³]?))?",
                rate_unit_cell,
            )
            if m:
                v1 = float(m.group(1))
                unit_raw = (m.group(3) or "").strip()
                unit = normalize_unit(unit_raw) if unit_raw else ""
                if m.group(2):
                    v2 = float(m.group(2))
                    value_parsed = {"type": "range", "min": min(v1, v2), "max": max(v1, v2), "unit": unit}
                else:
                    value_parsed = {"type": "fixed", "value": v1, "unit": unit}
            else:
                value_parsed = {"type": "tbd", "raw": rate_unit_cell}
                quality_flags.append(f"unparsed_rate_unit: {rate_unit_cell!r} for {desc!r}")

        item_no = (no_cell or sn).strip("*").strip()
        if not item_no:
            item_no = f"_{len(data_rows)+1}"

        data_rows.append({
            "row_id": f"weight-of-building-materials:{current_section}:{item_no}",
            "section": current_section,
            "section_name": current_section_name,
            "item_no": item_no,
            "description": desc,
            "value": value_parsed,
            **({"remarks": remarks_cell} if remarks_cell else {}),
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "$schema": f"{SCHEMA_BASE}/reference_table.schema.json",
        "category": "weight-of-building-materials",
        "data_type": "reference_table",
        "source": {
            "image": meta.get("source_image", ""),
            "url": "https://quantitysurveyoronline.com.my/weight-of-building-materials.html",
            "ocr_engine": meta.get("ocr_engine", ""),
        },
        "data_date": "static",
        "extracted_at": meta.get("extracted_at", datetime.now(timezone.utc).isoformat()),
        "columns": [
            {"name": "section", "description": "Section code (A, B, C...)"},
            {"name": "section_name", "description": "Section name"},
            {"name": "item_no", "description": "Item number"},
            {"name": "description", "description": "Material description"},
            {"name": "value", "description": "Weight/density value with unit"},
        ],
        "row_count": len(data_rows),
        "quality_flags": quality_flags,
        "rows": data_rows,
    }


def parse_timber_strength_group(meta: dict, body: str) -> dict[str, Any]:
    """Parse timber strength group plaintext."""
    quality_flags: list[str] = []
    groups: dict[str, list[str]] = {}
    current_group = None

    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        # Group header: "GROUP A", "GROUP B", etc.
        m = re.match(r"^GROUP\s+([A-Z])$", line, re.IGNORECASE)
        if m:
            current_group = m.group(1).upper()
            groups[current_group] = []
            continue
        # Skip title line
        if "TIMBER STRENGTH GROUP" in line.upper():
            continue
        if line.startswith("Updated"):
            continue
        # Species
        if current_group is not None:
            groups[current_group].append(line)

    data_rows = [
        {"group": g, "species": species_list}
        for g, species_list in sorted(groups.items())
    ]

    extracted_at = meta.get("scraped_at") or meta.get("extracted_at", datetime.now(timezone.utc).isoformat())

    return {
        "schema_version": SCHEMA_VERSION,
        "$schema": f"{SCHEMA_BASE}/strength_group_list.schema.json",
        "category": "timber-strength-group",
        "data_type": "strength_group_list",
        "source": {
            "url": meta.get("source", "https://quantitysurveyoronline.com.my/timber-strength-group.html"),
        },
        "data_date": "static",
        "extracted_at": extracted_at,
        "row_count": len(data_rows),
        "quality_flags": quality_flags,
        "rows": data_rows,
    }


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def convert_file(md_path: Path) -> dict[str, Any] | None:
    """Convert a single markdown file to structured JSON."""
    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    category = md_path.parent.name

    if category == "timber-strength-group":
        return parse_timber_strength_group(meta, body)
    elif category == "building-element-steel-content":
        return parse_building_element_steel(meta, body)
    elif category == "conversion-table":
        return parse_conversion_table(meta, body)
    elif category == "rebar-kg-per-m":
        return parse_rebar_kg_per_m(meta, body)
    elif category == "rebar-hook-bend-lap":
        return parse_rebar_hook_bend_lap(meta, body)
    elif category == "weight-of-building-materials":
        return parse_weight_of_building_materials(meta, body)
    elif category in PRICE_TABLE_CATEGORIES:
        return parse_price_table(category, meta, body)
    else:
        warnings.warn(f"Unknown category: {category}, attempting price_table parse")
        return parse_price_table(category, meta, body)


def write_output(md_path: Path, doc: dict[str, Any]) -> None:
    """Write JSON and JSONL output alongside the markdown file."""
    stem = md_path.stem  # e.g. "latest" or "2026-03-06"
    out_dir = md_path.parent

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(REPO_ROOT))
        except ValueError:
            return str(p)

    # JSON
    json_path = out_dir / f"{stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    print(f"  wrote {_rel(json_path)}")

    # JSONL (one row per line)
    jsonl_path = out_dir / f"{stem}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for row in doc.get("rows", []):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  wrote {_rel(jsonl_path)}")

    # Report quality flags
    flags = doc.get("quality_flags", [])
    if flags:
        print(f"  [WARN] {len(flags)} quality flags:")
        for flag in flags:
            print(f"    - {flag}")


def main() -> None:
    _load_units()

    if len(sys.argv) > 1:
        md_files = [Path(p) for p in sys.argv[1:] if p.endswith(".md")]
    else:
        md_files = sorted(DATA_DIR.rglob("*.md"))

    if not md_files:
        print("No markdown files found.")
        return

    errors = 0
    for md_path in md_files:
        md_path = md_path.resolve()
        try:
            rel = md_path.relative_to(REPO_ROOT)
        except ValueError:
            rel = md_path
        print(f"Processing {rel} ...")
        try:
            doc = convert_file(md_path)
            if doc:
                write_output(md_path, doc)
            else:
                print(f"  [SKIP] no output generated")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            errors += 1

    print(f"\nDone. {len(md_files)} files processed, {errors} errors.")


if __name__ == "__main__":
    main()
