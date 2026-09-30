# M1 parse-error audit (P0 guard review)

Source: `logs/m1_parse_errors.jsonl` · filtered **us_up** + **NS** packs only.

## Totals by pack

| Pack | errors | unique surfaces | on span_after | on span_before only |
| --- | ---: | ---: | ---: | ---: |
| ns_div10_claim | 216 | 39 | 96 | 16 |
| ns_div10_evid | 638 | 77 | 0 | 0 |
| ns_x10_claim | 232 | 41 | 0 | 24 |
| ns_x10_evid | 232 | 41 | 0 | 24 |
| us_up_x1000 | 392 | 38 | 40 | 56 |

## US_up (~23% guard)

### By error type

- **pint: DimensionalityError (mass-per-weight; not convertible to flat mg)**: 272
- **pint: DimensionalityError (incompatible dimensions)**: 120

### By unit / surface shape

- per-body-size (mg/kg): **136**
- per-body-size (g/kg): **136**
- volume (ml): **80**
- volume (l): **40**

### Top categories — 5 example surfaces each

**pint: DimensionalityError (mass-per-weight; not convertible to flat mg)**
- `1.0 mg/kg` (?)
- `1.0 g/kg` (?)
- `1.0 mg/kg` (?)
- `1.0 g/kg` (?)
- `1.0 mg/kg` (?)

**pint: DimensionalityError (incompatible dimensions)**
- `0.5 ml` (before)
- `0.5 mL` (before)
- `0.5 L` (AFTER)
- `0.5 ml` (before)
- `0.5 mL` (before)


## NS (~27% logged)

### By error type

- **pint: DimensionalityError (mass-per-weight; not convertible to flat mg)**: 818
- **pint: DimensionalityError (incompatible dimensions)**: 500

### By unit / surface shape

- per-body-size (mg/kg): **670**
- volume (ml): **480**
- per-body-size (mg/kg/day): **80**
- per-body-size (g/kg): **68**
- volume (l): **20**

### Top categories — 5 example surfaces each

**pint: DimensionalityError (mass-per-weight; not convertible to flat mg)**
- `1.0 mg/kg` (?)
- `10.0 mg/kg` (?)
- `25.0 mg/kg` (?)
- `250.0 mg/kg` (?)
- `5.0 mg/kg` (?)

**pint: DimensionalityError (incompatible dimensions)**
- `0.5 ml` (before)
- `0.5 mL` (before)
- `5.0 ml` (?)
- `5.0 mL` (?)
- `3.0 ml` (?)

## Interpretation (for guard decision)

- **All filtered errors in this log slice are `m1_lib.pint` + `DimensionalityError`.**
- Dominant pattern: **mass-per-weight** (`mg/kg`, `g/kg`, …) and **volume** (`mL`, `L`) — pint path tries `_to_mg_string` on non-mass dimensions.
- **IU / kIU:** surfaces containing IU often fail the same way; **×1000 can yield `kIU` / scaled IU strings** that are not registered as pint mass units.
- **`on_span_after`:** most failing surfaces match **edited `span_after`** (gate target), not arbitrary context.
- NS pack error counts exceed amendment-2 **span totals** because the log is **append-only across multiple runs**; rates in job 61599 used in-run counters (430 spans / 98 errors us_up).

