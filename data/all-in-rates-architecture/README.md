# all-in-rates-architecture

All-in unit rates for architectural works in Malaysia (supply + labour combined).

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `all-in-rates-architecture:{section}:{item_no}` |
| `section` | string | Section code: A–I |
| `section_name` | string | Section name |
| `item_no` | string | Item number |
| `description` | string | Work item description |
| `price.type` | string | `fixed` or `range` |
| `price.value` | number | Rate in MYR |
| `unit` | string | Canonical unit |

## Sections

| Code | Name |
|------|------|
| A | Brickwall & Lightweight Blockwall |
| B | Painting |
| C | Floor Finishes |
| D | Floor Screed & Coatings |
| E | Ceiling Finishes |
| F | Wall Finishes |
| G | Metal & Steel Work |
| H | Roofing |
| I | Waterproofing |

## Sample row

```json
{
  "row_id": "all-in-rates-architecture:A:1",
  "section": "A",
  "section_name": "BRICKWALL & LIGHTWEIGHT BLOCKWALL",
  "item_no": "1",
  "description": "115mm thick brickwall in cement & sand brick reinforced with expanded metal brickwork reinforcement at every 4th course",
  "price": {"type": "fixed", "value": 43.6, "currency": "MYR", "raw": "RM43.60"},
  "unit": "m²",
  "unit_raw": "M2"
}
```
