# materials-prices

Supply prices for construction materials in Malaysia.

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `materials-prices:{section}:{item_no}` |
| `section` | string | Section code: A–R |
| `section_name` | string | Section name |
| `item_no` | string | Item number within section |
| `description` | string | Material description |
| `price.type` | string | `fixed`, `range`, or `tbd` |
| `price.value` | number | Price in MYR |
| `price.min/max` | number | Price range bounds in MYR |
| `unit` | string | Canonical unit (e.g. `t`, `m³`, `each`) |
| `remarks` | string | Additional notes, e.g. price per kg alongside tonne price |

## Sections

| Code | Name |
|------|------|
| A | Steel Bar (Rebar) |
| B | Concrete |
| C | Plaster, Render & Skim Coat |
| D | Timber & Plywood |
| E | BRC |
| F | Granular Material |
| G | Brick, Block & Panel |
| H | Tiles & Marble |
| I | Paint |
| J | Pipe |
| K | Metal & Steel Work |
| L | Door |
| M | Ceiling Board |
| N | Metal Roofing Sheet |
| O | Premix |
| P | Drain |
| Q | Reinforced Concrete Pile |
| R | Miscellaneous |

## Units

Common units in this category: `t` (tonne), `m³`, `m²`, `m`, `each` (No./Piece), `bag`, `roll`, `drum`, `pail`.

Rebar prices are per tonne; per-kg rate is in `remarks`.
BRC prices are per sheet (2.2 x 6.0m); per-m² rate is in `remarks`.

## Sample row

```json
{
  "row_id": "materials-prices:A:1",
  "section": "A",
  "section_name": "STEEL BAR (REBAR)",
  "item_no": "1",
  "description": "Tensile steel bar, T10, T40 diameter",
  "price": {"type": "fixed", "value": 2520.0, "currency": "MYR", "raw": "RM2,520.00"},
  "unit": "t",
  "unit_raw": "Tonne",
  "remarks": "RM2.52/kg"
}
```

## Files

- `latest.json` — full structured document
- `latest.jsonl` — one row per line for streaming
- `latest.md` — canonical markdown table (generated from JSON)
