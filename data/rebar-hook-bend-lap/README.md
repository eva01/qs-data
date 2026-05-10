# rebar-hook-bend-lap

Reference table for rebar hook, bend, lapping, and tying allowances (static data).

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `rebar-hook-bend-lap:{steel_type}:{measurement}:{bar_size}` |
| `steel_type` | string | `mild_steel` or `high_yield` |
| `bar_size_mm` | integer | Bar diameter in mm |
| `measurement` | string | Measurement type (see below) |
| `formula_multiplier` | number | Factor applied to D (bar diameter) |
| `value_mm` | integer | Minimum value in mm |

## Measurement types

| Code | Description | Standard |
|------|-------------|---------|
| `hook_allowance_mm` | Hook allowance (9D mild / 11D high yield) | BS 4449 |
| `bend_allowance_mm` | Bend allowance (5D mild / 5.5D high yield) | BS 4449 |
| `rebar_lapping_mm` | Lapping length (40D both) | BS 4449/4461 |
| `tying_allowance_mm` | Tying allowance (24D both) | BS 4449/4461 |

## Bar sizes covered

6, 8, 10, 12, 16, 20, 25, 32, 40 mm diameter.

## Note

All values are nominal minimums and may vary due to cutting tolerance.

## Sample row

```json
{
  "row_id": "rebar-hook-bend-lap:high_yield:rebar_lapping_mm:25",
  "steel_type": "high_yield",
  "bar_size_mm": 25,
  "measurement": "rebar_lapping_mm",
  "formula_multiplier": 40.0,
  "value_mm": 1000
}
```
