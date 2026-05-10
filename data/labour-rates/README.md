# labour-rates

Labour-only rates for construction trades in Malaysia.

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `labour-rates:{section}:{item_no}` |
| `section` | string | Section code: A–F |
| `section_name` | string | Section name |
| `item_no` | string | Item number |
| `description` | string | Trade/task description |
| `price.type` | string | `fixed` or `range` |
| `price.value` | number | Rate in MYR |
| `price.min/max` | number | Rate range in MYR |
| `unit` | string | Canonical unit |

## Sections

| Code | Name |
|------|------|
| A | General |
| B | Structural |
| C | Floor Finishes |
| D | Wall Finishes |
| E | Door |
| F | Sanitary Wares & Fitting |

## Note on "Ditto" rows

Several items use `Ditto` to refer to the preceding item description. In the JSON these are preserved with their full contextual descriptions from the source.

## Sample row

```json
{
  "row_id": "labour-rates:A:1",
  "section": "A",
  "section_name": "GENERAL",
  "item_no": "1",
  "description": "General Labour",
  "price": {"type": "range", "min": 80.0, "max": 100.0, "currency": "MYR", "raw": "RM80.00 - RM100.00"},
  "unit": "day",
  "unit_raw": "Day"
}
```
