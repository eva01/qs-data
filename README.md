# qs-data

Malaysian construction cost data scraped from [Quantity Surveyor Online](https://quantitysurveyoronline.com.my) (licensed subscriber access), structured as a machine-readable knowledge base.

## Quick start for LLMs

1. Fetch `manifest.json` to discover all categories, their data dates, row counts, and file URLs.
2. Fetch the category `latest.json` you need — each file is self-describing with schema version, data date, and structured rows.
3. For streaming or partial reads, use `latest.jsonl` (one JSON object per line).

```
https://raw.githubusercontent.com/eva01/qs-data/master/manifest.json
https://raw.githubusercontent.com/eva01/qs-data/master/data/materials-prices/latest.json
https://raw.githubusercontent.com/eva01/qs-data/master/data/materials-prices/latest.jsonl
```

## Repository structure

```
manifest.json                   # LLM entry point — index of all categories
schemas/
  price_table.schema.json       # JSON Schema for price tables
  reference_table.schema.json   # JSON Schema for reference tables
  strength_group_list.schema.json
vocab/
  units.json                    # Raw unit string → canonical unit mapping
  categories.json               # Category metadata array
data/
  <category>/
    latest.json                 # Latest data as structured JSON
    latest.jsonl                # Latest data as JSONL (one row per line)
    latest.md                   # Latest data as canonical markdown (generated)
    <YYYY-MM-DD>.json           # Historical snapshots (same structure)
    <YYYY-MM-DD>.jsonl
    <YYYY-MM-DD>.md             # Original OCR source
tools/
  md_to_json.py                 # Convert markdown → JSON + JSONL
  json_to_md.py                 # Convert JSON → canonical markdown
  build_manifest.py             # Regenerate manifest.json
```

## Data types

### `price_table`

Categories: `all-in-rates-architecture`, `all-in-rates-structure`, `labour-rates`, `materials-prices`, `plant-equipment-rates`, `preliminaries-rates`

Each row has:
- `row_id`: unique identifier `{category}:{section}:{item_no}`
- `section`: section code letter (A, B, C...)
- `section_name`: human-readable section name
- `item_no`: item number string (e.g. `"1"`, `"3a"`)
- `description`: full item description
- `price`: structured price object — see below
- `unit`: canonical unit (e.g. `"m²"`, `"t"`, `"each"`)
- `unit_raw`: original unit string
- `alt_prices`: (optional) array of alternative prices, e.g. daily + monthly rates
- `remarks`: (optional) notes from the source

Price object types:
- `{"type": "fixed", "value": 2520.0, "currency": "MYR"}` — single price
- `{"type": "range", "min": 150.0, "max": 250.0, "currency": "MYR"}` — price range
- `{"type": "formula", "formula": "0.125% of contract_sum"}` — percentage of contract sum
- `{"type": "item"}` — lump item, priced separately
- `{"type": "tbd"}` — no price given

### `reference_table`

Categories: `building-element-steel-content`, `conversion-table`, `rebar-hook-bend-lap`, `rebar-kg-per-m`, `weight-of-building-materials`

Static reference data. Row structure varies by category — see the `columns` field in each JSON file or the per-category README.

### `strength_group_list`

Category: `timber-strength-group`

Malaysian timber species classified into groups A–D. Each row: `{"group": "A", "species": ["BALAU", "CHENGAL", ...]}`.

## All categories

| Slug | Display name | Type | Data date | Rows |
|------|-------------|------|-----------|------|
| all-in-rates-architecture | All-In Rates (Architecture) | price_table | 2026-03-06 | 57 |
| all-in-rates-structure | All-In Rates (Structure) | price_table | 2026-03-06 | 66 |
| building-element-steel-content | Building Element Steel Content | reference_table | static | 9 |
| conversion-table | Conversion Table | reference_table | static | 17 |
| labour-rates | Labour Rates | price_table | 2025-11-19 | 44 |
| materials-prices | Materials Prices | price_table | 2026-03-06 | 190 |
| plant-equipment-rates | Plant & Equipment Rates | price_table | 2025-11-19 | 63 |
| preliminaries-rates | Preliminaries Rates | price_table | 2026-03-30 | 43 |
| rebar-hook-bend-lap | Rebar Hook, Bend & Lap | reference_table | static | 72 |
| rebar-kg-per-m | Rebar kg/m | reference_table | static | 15 |
| timber-strength-group | Timber Strength Group | strength_group_list | static | 4 |
| weight-of-building-materials | Weight of Building Materials | reference_table | static | 18 |

## Sample query patterns

**"What is the price of Grade 30 ready-mix concrete?"**
Fetch `data/materials-prices/latest.json`, filter rows where `section == "B"` and `description` contains `"Grade 30"`.

**"What is the all-in rate for laying 300x300mm homogeneous floor tiles?"**
Fetch `data/all-in-rates-architecture/latest.json`, filter section `"C"` (Floor Finishes).

**"What CIDB levy rate applies to construction contracts?"**
Fetch `data/preliminaries-rates/latest.json`, filter section `"L"`.

**"What is the mass per metre for T16 rebar?"**
Fetch `data/rebar-kg-per-m/latest.json`, filter `diameter_mm == 16`.

**"Is Chengal a Group A timber?"**
Fetch `data/timber-strength-group/latest.json`, check `rows[0].species`.

## Tools

```bash
# Convert all markdown to JSON+JSONL
python3 tools/md_to_json.py data/*/latest.md

# Regenerate canonical markdown from JSON
python3 tools/json_to_md.py data/*/latest.json

# Rebuild manifest.json
python3 tools/build_manifest.py
```

No external dependencies — uses Python 3.9+ standard library only.

## Source

Data sourced from [Quantity Surveyor Online](https://quantitysurveyoronline.com.my) (licensed subscriber access). Currency: MYR. Region: Malaysia.
