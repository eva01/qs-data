# all-in-rates-structure

All-in unit rates for structural works in Malaysia (supply + labour combined).

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `all-in-rates-structure:{section}:{item_no}` |
| `section` | string | Section code: A–G |
| `section_name` | string | Section name |
| `item_no` | string | Item number (may be nested: `a`, `b`, `c`...) |
| `description` | string | Work item description |
| `price.type` | string | `fixed`, `range`, or `tbd` |
| `price.value` | number | Rate in MYR |
| `unit` | string | Canonical unit |

## Sections

| Code | Name |
|------|------|
| A | Piling Works |
| B | Excavation |
| C | Bedding |
| D | Reinforced Concrete (Normal) |
| E | Formwork |
| F | Reinforcement Bar |
| G | BRC |

## Sample row

```json
{
  "row_id": "all-in-rates-structure:D:1",
  "section": "D",
  "section_name": "REINFORCED CONCRETE (NORMAL)",
  "item_no": "1",
  "description": "Supply and cast reinforced concrete Grade 20 in foundations, ground beams, etc.",
  "price": {"type": "fixed", "value": 393.7, "currency": "MYR", "raw": "RM393.70"},
  "unit": "m³",
  "unit_raw": "M3"
}
```
