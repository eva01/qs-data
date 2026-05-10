# conversion-table

Unit conversion factors for area measurements used in construction quantity surveying (static reference data).

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `conversion-table:{dimension}:{index}` |
| `dimension` | string | Measurement dimension, e.g. `AREA` |
| `from_unit` | string | Source unit description |
| `to_unit` | string | Target unit description |
| `multiplier` | number | Multiply `from_unit` by this factor to get `to_unit` |

## Dimensions covered

Currently only `AREA` conversions are present in the source data.

## Sample row

```json
{
  "row_id": "conversion-table:area:3",
  "dimension": "AREA",
  "from_unit": "Sq. Feet",
  "to_unit": "Sq. Metres",
  "multiplier": 0.092903
}
```
