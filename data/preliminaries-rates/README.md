# preliminaries-rates

Rates for construction preliminaries in Malaysia.

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | `preliminaries-rates:{section}:{item_no}` |
| `section` | string | Section code: A–V |
| `section_name` | string | Section name |
| `item_no` | string | Item number |
| `description` | string | Item description |
| `price.type` | string | `fixed`, `range`, `formula`, `item`, or `tbd` |
| `unit` | string | Canonical unit |
| `remarks` | string | Additional conditions/notes |

## Formula prices

Some items (CIDB levy, insurance) are expressed as a percentage of contract sum:
```json
{"type": "formula", "formula": "0.125% of contract_sum"}
```

## Sections

| Code | Name |
|------|------|
| A | Temporary site office & buildings |
| B | Site security |
| C | Light and power |
| D | Water for the work |
| E | Project Signboard |
| F | Hoarding |
| G | Survey instruments |
| H | Safety precaution |
| I | Fire protection |
| J | Site management personnel |
| K | Silting Traps |
| L | CIDB - Levy |
| M | Insurance of work |
| N | Contract document stamping fee |
| O | Washing trough for vehicles |
| P | Provision of Workers' Quarters |
| Q | Hire portable toilet |
| R | Plant & Equipment |
| S | Scaffolding |
| T | Diesel |
| U | Disposal of construction waste |
| V | Traffic management & control |

## Sample row

```json
{
  "row_id": "preliminaries-rates:L:0",
  "section": "L",
  "section_name": "CIDB - Levy",
  "item_no": "0",
  "description": "CIDB - Levy",
  "price": {"type": "formula", "formula": "0.125% of contract_sum", "raw": "0.125% Of Contract Sum"},
  "unit": "—",
  "unit_raw": ""
}
```
