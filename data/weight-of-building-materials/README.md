# weight-of-building-materials

Weight and density reference for common building materials (static reference data).

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `weight-of-building-materials:{section}:{item_no}` |
| `section` | string | Section code: A–E |
| `section_name` | string | Section name |
| `item_no` | string | Item number |
| `description` | string | Material description |
| `value.type` | string | `fixed` or `range` |
| `value.value` | number | Weight/density value |
| `value.unit` | string | Unit: `kg/m²` (area-based) or `kg/m³` (volumetric) |

## Sections

| Code | Name |
|------|------|
| A | Blockwork, Walling |
| B | Brickwork |
| C | Glass |
| D | Glass Fiber |
| E | Glazing, Patent |

## Unit conventions

- `kg/m²` values are per unit thickness (e.g. per 1" thick)
- `kg/m³` values are volumetric density

## Sample row

```json
{
  "row_id": "weight-of-building-materials:B:1",
  "section": "B",
  "section_name": "BRICKWORK",
  "item_no": "1",
  "description": "Common brick",
  "value": {"type": "fixed", "value": 2002.0, "unit": "kg/m³"}
}
```
