# Contract: hunter entry in the catalog (input)

Source: the catalog entry of an enemy, read through `ficha_desde_json` → `FichaEnemigoDTO` (online,
from the catalog cache, or from the offline recording).

```json
{
  "id": "ent_lobo_cazador",
  "clase": "enemigo",
  "nombre": "Lobo",
  "vida_max": 20,
  "ataque": 6,
  "defensa": 1,
  "velocidad": 120,
  "comportamiento": "cazador",
  "rango": 400
}
```

| Field | Required | Default | Meaning |
|---|---|---|---|
| comportamiento | yes | — | `"cazador"` makes the enemy a hunter; `"errante"`, `"rastreador"` and the others are unchanged |
| rango | no | 0 | largest route cost, in exit-cost units, at which the hunter chases (FR-001) |

- `rango` is read for every enemy entry and kept on the enemy, but only the `"cazador"` behavior uses it.
- A hunter entry with no `rango` is a hunter with `rango` 0 (US5-5).
- No range or type check of `rango` (FR-001).
- The cache format does not change: the raw entry, with `rango`, is what is stored.
