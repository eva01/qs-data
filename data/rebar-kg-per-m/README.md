# rebar-kg-per-m

Reference table for steel reinforcement bar properties (static data).

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `rebar-kg-per-m:_:{diameter_mm}` |
| `diameter_mm` | integer | Bar diameter in mm |
| `cross_section_area_mm2` | number | Cross-sectional area in mm² |
| `mass_per_m_kg` | number | Mass per linear metre in kg/m |
| `mass_per_12m_kg` | number | Mass per 12-metre bar length in kg |

## Bar sizes covered

6, 9, 10, 12, 13, 14, 16, 18, 20, 22, 25, 28, 32, 35, 38 mm diameter.

## Sample row

```json
{
  "row_id": "rebar-kg-per-m:_:16",
  "diameter_mm": 16,
  "cross_section_area_mm2": 201.1,
  "mass_per_m_kg": 1.579,
  "mass_per_12m_kg": 18.948
}
```
