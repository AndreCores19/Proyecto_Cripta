# Data Model: Timeline

Names follow the code base (Spanish identifiers). "Mutable" means it can change after the crypt is
built; everything else is rebuilt from the skeleton.

## Entities

### AccionGrabada (action record)

| Field | Type | Rule |
|---|---|---|
| `numero` | int ≥ 1 | position among the surviving actions (FR-003); continues from the last survivor after a scroll (FR-010) |
| `reloj` | int ≥ 0 | clock at the decision, before the action; strictly increasing along the vector |
| `tipo` | text | one of `mover`, `esperar`, `atacar`, `recoger`, `soltar`, `equipar`, `usar`, `abrir` |
| `argumento` | text or none | direction (`N/S/E/O`), enemy id, or object instance id; none for `esperar` |

Stored as three parallel vectors (`relojes`, `tipos`, `argumentos`) so the clock search touches only
ints. Never holds a reference to a live object.

### RegistroEstado (checkpoint / state record)

Internal to `model/`. It is never written to the save file (the timeline is rebuilt by load).

| Group | Fields |
|---|---|
| partida | `reloj`, `num_sec`, `azar` (`array('I')`, 625 words + the `gauss_next` marker), `acciones_jugador`, `enemigos_derrotados`, `terminada`, `victoria`, `abrio_puerta_salida`, `retrocesos`, `modo_decisor`, `siguiente_instancia` |
| jugador | `id_sala`, `vida`, `velocidad`, `id_arma`, `id_armadura`, `efectos` (list), `inventario` (objects in order), `cursor` (position or none) |
| objeto (inventory or floor) | `id_instancia`, `id_catalogo`, `equipado` |
| enemigo activo | `id_enemigo`, `id_sala`, `vida`, `velocidad`, `efectos`, `evento` (ref) |
| efecto | `tipo`, `dano`, `fin`, `cambio_aplicado`, `cantidad`, `evento` (ref) |
| sala tocada | `id_sala`, `conocimiento`, `rastro`, `objetos` (floor, in order), `inactivos` (ids, in order), `trampas` (`id_instancia`, `armada`, `evento` ref), `poblada` |
| salida tocada | `id_sala`, `direccion`, `cerrada`, `memoria` |
| `conocidas` | room ids in discovery order |
| agenda | list of events: `tiempo`, `num_sec`, `tipo`, `dueno` (ref), `datos` (ref) |

References are `(kind, key)`: `jugador`; `enemigo` + id; `efecto` + (owner ref, type); `trampa` + id;
`salida` + (room id, direction); `ninguno`. They are resolved while restoring with sorted vectors
and the binary search (no `dict`).

Not stored (derived or not shown): the message buffer (`Bitacora`), the hunter's search cache, the
undo history, the room names and exits (skeleton), catalog data.

Invariants: `restaurar(capturar(p))` followed by the same actions gives the same summaries as `p`
(tested at every decision); the record never shares a mutable object with the live game.

### LineaTiempo (`structures/linea_tiempo.py`)

| Field | Meaning |
|---|---|
| `k` | checkpoint spacing, positive int; saved with the game |
| `relojes`, `tipos`, `argumentos` | action vectors, index = `numero − 1` |
| `reloj_decision_pendiente` | clock of decision n+1 (the live clock), or none if the game ended |
| `reloj_final` | clock at which the game ended or the current clock |
| `puntos` | checkpoint vector; `puntos[i]` is the state with `i·K` actions taken |
| `omitidos` | ledger of skipped effects (`EfectoOmitido`), chronological |

Operations: `agregar_accion`, `punto_para(boundary)`, `ultimo_menor_o_igual(t)`,
`recortar(n)` (also retags the ledger), `omitidos_en(boundary)`, `__len__`. Invariants:
`len(puntos) ≤ ⌊A/K⌋ + 1` (**no checkpoint is ever off the K grid**, FR-019); `relojes` strictly
increasing; all checkpoints have boundary ≤ A.

State transitions:

- *start*: `puntos = [capture]`, no actions.
- *action succeeded*: append record; if A is a multiple of K, append a checkpoint of the live state
  (the state with A actions taken, i.e. before action A+1).
- *scroll read* (n = actions left): `recortar(n)` deletes records and checkpoints above n from the
  end, retags the ledger entries above n to n (marked "re-apply"), appends `contador(value)`. No
  checkpoint is taken.
- *game ended*: `reloj_final` fixed; no pending decision.

### EfectoOmitido (ledger entry: an effect the undo deliberately skips)

| Field | Type | Rule |
|---|---|---|
| `etiqueta` | int >= 0 | boundary (actions taken) at which a re-simulation applies it; equals the number of the action in progress when it happened, and is lowered to n by a scroll to n |
| `reaplicar` | bool | false while it is only a candidate in the last-5-actions window; true once a scroll kept it |
| `tipo` | text | `poblar`, `suelo_quitar`, `suelo_poner`, `inv_agregar`, `inv_quitar`, `contador` |
| datos | by type | `poblar`: room id, instance counter at the start; `suelo_quitar`: room id, instance id; `suelo_poner`: room id, object record; `inv_agregar`: object record; `inv_quitar`: instance id; `contador`: value |

Where each comes from, and why every other skipped effect is not needed, is the table in research R6
(consumed scroll, scroll objects moved by reverted actions, instance counter, rooms populated by
reverted moves).

Rules: entries are chronological; a window entry (`reaplicar` false) older than the history
capacity (5) is dropped after each recorded action; a query applies the entries tagged b, in order, when its scratch world is **at the decision point with b actions taken**
(the state just before action b+1: right after loading a checkpoint of boundary b, or after replaying action b and
running the events up to the player's turn); entries tagged below the checkpoint's boundary are skipped; an instant
t with `c_b ≤ t < c_{b+1}` (after action b, before the turn) does **not** see them, because the effects happened
at or after the turn. The ledger is bounded by the last 5 actions plus what scroll reads kept.

### Instant / decision mapping (FR-001, FR-002, FR-003)

For an instant t with 0 ≤ t ≤ clock: `k = ultimo_menor_o_igual(t)` over the decision clocks
`c_1 … c_{n+1}`.

| Case | Target state | Re-simulation |
|---|---|---|
| `c_k == t` | before action k (boundary k−1) | from the checkpoint to boundary k−1 |
| `c_k < t` | after action k, events with time ≤ t run | to boundary k−1, play action k, run events to t |

For `#k`: valid when 1 ≤ k ≤ n (the pending decision n+1 is rejected, FR-003); target = before action
k. In both cases at most K actions are applied (FR-020).

### ResumenHistoriaDTO (FR-004)

| Field | Type |
|---|---|
| `reloj` | int (the requested instant, or the decision clock for `#k`) |
| `id_sala`, `nombre_sala` | room of the player |
| `jugador` | `JugadorVistaDTO` (existing: life, stats, equipment, effects) |
| `inventario` | list of `ObjetoInventarioDTO` (existing) |
| `enemigos` | list of `EnemigoVistaDTO` (existing) in the player's room, with life |
| `mapa` | `MapaVistaDTO` (existing, spec 003) as known at that moment |

### RespuestaHistoriaDTO

| Field | Type |
|---|---|
| `aceptada` | bool |
| `motivo` | text or none: `despues_del_reloj`, `accion_inexistente`, `argumento_invalido` |
| `resumen` | `ResumenHistoriaDTO` or none |
| `termino_antes` | bool; true only for `--replay --hasta` past the end (FR-015) |
| `reloj_final` | int, filled with `termino_antes` |

### FichasCongeladas

`VectorBusqueda` keyed by ficha id, value = the ficha DTO, filled by the factory's observer.
Read-only in the scratch world.

## Relationships

`JuegoService` 1—1 `LineaTiempoPartida` 1—1 `LineaTiempo`; `LineaTiempo` 1—n `RegistroEstado` and 1—n `EfectoOmitido`.
`Reproductor` is created per query and owns the scratch `Partida`; nothing in it is referenced by
the live game. `Historial` (part one) is unrelated to the timeline and is never read by it.
