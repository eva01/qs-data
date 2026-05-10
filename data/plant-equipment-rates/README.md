# plant-equipment-rates

Hire rates for plant and equipment in Malaysia.

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `plant-equipment-rates:{section}:{item_no}` |
| `section` | string | Section code: A–E |
| `section_name` | string | Section name |
| `item_no` | string | Item number |
| `description` | string | Equipment description |
| `price.type` | string | `fixed` or `range` |
| `price.value` | number | Primary rate (usually daily) in MYR |
| `unit` | string | Primary unit (`day (8h)` or `month`) |
| `alt_prices` | array | Alternative rate, e.g. monthly alongside daily |

## Dual rates

Many plant items have both a daily (8-hour) and monthly rate, formatted as:
`RM550.00 / RM8,300.00` with unit `Day (8 hours) / Month`.

In JSON, the primary price is the daily rate and the monthly rate appears in `alt_prices[0]`.

## Sections

| Code | Name |
|------|------|
| A | Generator |
| B | Lorry |
| C | Crane |
| D | Pump |
| E | Scaffolding |

## Sample row

```json
{
  "row_id": "plant-equipment-rates:C:1",
  "section": "C",
  "section_name": "CRANE",
  "item_no": "1",
  "description": "Mobile crane, 16 tonne (incl. diesel for Day only)",
  "price": {"type": "fixed", "value": 600.0, "currency": "MYR"},
  "unit": "day (8h)",
  "unit_raw": "Day (8 hours)/ Month",
  "alt_prices": [{"price": {"type": "fixed", "value": 11500.0, "currency": "MYR"}, "unit": "month"}]
}
```
