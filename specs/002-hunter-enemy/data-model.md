# Data Model: Hunter Enemy

## FichaEnemigoDTO (dto/ficha_dto.py)

| Field | Type | Source | Notes |
|---|---|---|---|
| comportamiento | str | `comportamiento` | unchanged; `"cazador"` marks a hunter |
| **rango** | int | `rango` | **new**; `None` or missing → 0 (FR-001). No range or type check. |

## Enemigo (model/enemigo_logica.py)

| Field | Type | Notes |
|---|---|---|
| **rango** | int | new; copied from the catalog entry by `FabricaModelo.crear_enemigo`; 0 for any behavior that does not use it |
| **es_cazador()** | bool | new; `comportamiento == "cazador"` |

## Salida and Sala (model/sala_logica.py)

| Field | Type | Notes |
|---|---|---|
| Salida.**origen** | Sala | new; the room that owns the exit; set by `Sala.agregar_salida` |
| Salida.**cerrada** | bool (property) | the setter adds 1 to `Salida.epoca_puertas`; undo writes go through it |
| Salida.**epoca_puertas** | int (class attribute) | new; only grows; read by the decider to detect any door change |
| Sala.**entradas** | list of Salida | new; the exits whose `destino` is this room; filled by `Sala.agregar_salida` (`salida.destino.entradas.append(salida)`) |
| Sala.**busq_marca** | int | new; stamp of the last search that reached the room; initial -1 |
| Sala.**busq_dist** | int | new; cost from this room to the player's room, valid only when `busq_marca` is the current stamp |

`entradas`, `busq_marca` and `busq_dist` are not part of the game state: they are not saved, not
undone by `Historial`, and not read by anything but `Busqueda`.

## MonticuloMinimo (structures/monticulo.py)

| Field | Type | Notes |
|---|---|---|
| items | list of nodes | array-based binary heap |
| secuencia | int | next insertion number; reset by `vaciar()` |
| node | (prioridad, secuencia, valor) | ordered by `prioridad` with `<`; equal priorities by `secuencia` |

## Busqueda (model/ruta_cazador.py)

| Field | Type | Notes |
|---|---|---|
| ultima_estampa | int (class attribute) | latest stamp handed out by `nueva_estampa()`; shared by every `Busqueda` object; only grows |
| estampa | int | stamp of this object's latest search |
| frontera | MonticuloMinimo | reused between searches (`vaciar()`) |
| busquedas | int | number of searches run; read by the benchmark |

## DecisorCazador (model/ruta_cazador.py)

| Field | Type | Notes |
|---|---|---|
| modo | str | `"individual"`, `"compartido_sin_reuso"` or `"compartido"` |
| busqueda | Busqueda | one per decider |
| sala_jugador, epoca, limite, estampa | Sala, int, int, int | the cached search of mode `compartido` (the player's room, `Salida.epoca_puertas`, the search limit and its stamp); `None`/-1 when empty |

**Validity of the cached search** (mode `compartido` only):

| Condition | Meaning |
|---|---|
| `jugador.sala is sala_jugador` | the player has not changed room |
| `Salida.epoca_puertas == epoca` | no door has changed since the search |
| `cazador.rango <= limite` | the search reached far enough for this hunter |
| `Busqueda.ultima_estampa == estampa` | no other search has overwritten the room fields since |

If any condition fails, a new search is run with limit `max(cazador.rango, largest rango)` and the cache is replaced (it is recomputed, never extended).

## EnemigoVistaDTO and EstadoVistaDTO (dto/estado_vista_dto.py)

| Field | Type | Source | Notes |
|---|---|---|---|
| EnemigoVistaDTO.**cazador** | bool | `Enemigo.es_cazador()` | **new**, default `False`; part of `EstadoVistaDTO.enemigos` |

## State of a hunter

| State | How it is reached | What it does |
|---|---|---|
| inactive | created in `Sala.inactivos` when the room content is loaded | nothing: no pending event (FR-022) |
| active, shares the player's room | `_entrar_en_sala` activated it; same room as the player | attacks (FR-002) |
| active, elsewhere | same | asks the decider: moves (FR-005) or waits (FR-004) |
| dead | `vida` reaches 0 | removed from `partida.enemigos`; does not count for the search limit |
