# building-element-steel-content

Approximate steel reinforcement content by building element type (static reference data).

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `building-element-steel-content:_:{item_no}` |
| `item_no` | string | Row number |
| `description` | string | Building element type |
| `value.type` | string | `fixed` or `range` |
| `value.value` | number | Steel content in kg/m³ (for fixed type) |
| `value.min/max` | number | Steel content range in kg/m³ (for range type) |
| `value.unit` | string | Unit: `kg/m³` |

## Data quality note

Row 2 ("Warehouse, girder bridges, rectangular tanks") has a corrupt OCR value `385-135 kg/m³` where 385 > 135. This is flagged in `quality_flags` and the values are stored as `min=135, max=385` with the flag `corrupt_range`. The correct range is likely `85–135 kg/m³`.

## Sample row

```json
{
  "row_id": "building-element-steel-content:_:7",
  "item_no": "7",
  "description": "Offices, shops & hotels",
  "value": {"type": "fixed", "value": 75.0, "unit": "kg/m³"}
}
```
