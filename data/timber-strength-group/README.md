# timber-strength-group

Malaysian timber species classified into strength groups A–D per the Malaysian Grading Rules (static reference data).

## Data dictionary

| Field | Type | Description |
|-------|------|-------------|
| `group` | string | Strength group: `A`, `B`, `C`, or `D` |
| `species` | array of strings | Timber species in this group |

## Strength group summary

| Group | Strength | Example species |
|-------|----------|-----------------|
| A | Highest | BALAU, CHENGAL, BITIS, KEMPAS |
| B | High | KAPUR, KERUING, MERBAU, KULIM |
| C | Medium | MERANTI (various), RAMIN, DURIAN |
| D | Lower | JELUTONG, PULAI, SESENDOK |

## Sample row

```json
{
  "group": "A",
  "species": ["BALAU", "BALAU, RED", "BITIS", "CHENGAL", "GIAM", "KEKATONG", "KEMPAS", "KERANJI", "MATA ULAT", "MEMPENING", "MERTAS", "NYALAS", "PENAGA", "TUALANG"]
}
```
