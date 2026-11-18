# Data Model: Crypt Solvability Verification

Nothing is added to the game state: the verification reads the rooms and writes nothing into them.
Everything below is new data that lives only for one verification, plus one small file per crypt.

## Entities from the spec and where they live

| Spec entity | In the program |
|---|---|
| Crypt skeleton | The rooms the data layer already builds (`Sala`, `Salida`: `cerrada`, `llave`). Read only. |
| Key | A text id (`itm_llave_...`) named by closed exits (`Salida.llave`) and by the key query. |
| Key location | `LlaveUbicacionDTO` (data layer) → `LlaveLogica` (model). |
| Order of keys | `ResultadoVerificacion.orden`: key ids in the order they were taken. |
| Blocked frontier | `ResultadoVerificacion.frontera`: closed exits from reached rooms to rooms not reached. |
| Cycle | `ResultadoVerificacion.ciclos`: list of cycles; each a list of links. |
| Verdict and report | `ReporteVerificacionDTO` (service → view and adapters). |

## DTOs (no model imports)

| DTO | Fields |
|---|---|
| `LlaveUbicacionDTO` | `id_llave` (text), `id_sala` (room id), `id_enemigo` (text or `None`) |
| `UbicacionLlaveDTO` | `id_llave`, `id_sala` (or `None` if the key is not in the key list), `id_enemigo` |
| `PuertaFronteraDTO` | `id_sala` (origin), `direccion`, `id_destino`, `id_llave` (or `None`: the exit names no key) |
| `EslabonCicloDTO` | `id_llave`, `id_sala` (where the key is), `id_llave_guardia`, `puerta` (a `PuertaFronteraDTO`: the frontier door that guards it) |
| `ReporteVerificacionDTO` | `id_cripta`, `resoluble` (bool), `orden` (list of key ids), `llaves_inalcanzables` (list of `UbicacionLlaveDTO`, sorted by id), `puertas_frontera` (sorted by `(id_sala, direccion)`), `ciclos` (list of lists of `EslabonCicloDTO`), `solicitudes` (requests made by the verification, for information) |

When the crypt is solvable, `llaves_inalcanzables`, `puertas_frontera` and `ciclos` are empty lists.

## Model objects (one verification)

- **`LlaveLogica`**: `id`, `id_sala`, `id_enemigo`, `obtenida` (bool), `pendientes` (list of `Salida`: closed
  exits waiting for this key), `visita` (the id of the key from which the cycle walk reached it, or `None`).
- **Per-room lists** (indexed by the room's position in the binary-search vector): `alcanzada` (bool),
  `llaves_en` (list of `LlaveLogica`), `etiqueta_llave` and `etiqueta_puerta` (the guard sweep).
- **`ResultadoVerificacion`**: `resoluble`, `orden`, `inalcanzables` (list of `LlaveLogica`), `frontera`
  (list of `Salida`), `sin_abrir` (closed exits whose key is missing or absent, see plan point 1), `ciclos`.

## The key file

`cache/llaves/<id_cripta>.json`:

```json
{"version": "<crypt version>", "llaves": [{"id": "...", "sala": 0, "enemigo": "..."}]}
```

`enemigo` is absent for a key lying in a room. The file is valid only while `version` equals the crypt's
version ([cache-llaves.md](./contracts/cache-llaves.md)).

## Rules the model checks

- A key id appears once in the key list; a second entry with the same id is ignored (FR-002, plan point 9:
  the one with the lowest room id wins, so that the result does not depend on the listing order).
- A door has the same key on both faces (as the rooms are built); the pass reads the key of the face it
  crosses.
- The pass never changes `Salida.cerrada`, never opens a door in the game, and never reads the player's
  knowledge.
