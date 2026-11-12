# Data Model: Fog of War and Automatic Travel

No persisted data is added. Everything below is in-memory game state, written through the undo
history so that rollback restores it.

## Sala (changed)

| Field | Type | Meaning | Written by |
|---|---|---|---|
| `conocimiento` | int | `0` unknown, `1` sighted, `2` explored (FR-001, FR-004, FR-005) | `Partida._subir`, through `Historial.asignar` |

- Initial value 0. Never decreases except by rollback.
- Level 2 implies the player knows name, exits, costs and (remembered) door states (FR-003).
- Level 1 shows no name, no exits, no contents (FR-004).

## Salida (changed)

| Field | Type | Meaning | Written by |
|---|---|---|---|
| `memoria` | int | `0` never observed, `1` open, `2` closed, as of the last observation (FR-006, FR-007) | `Partida._memorizar_puertas`, through `Historial.asignar` |

- Both faces of a door always hold the same value.
- It is **not** the state shown for a door that touches the player's room: that one is read from the
  real state (continuous observation). `Partida.puerta_recordada(salida)` returns the value to use.
- It never changes `Salida.epoca_puertas` (the hunters' door counter): it is not a door change.

## Partida (changed)

| Field | Type | Meaning |
|---|---|---|
| `conocidas` | list of `Sala` | Rooms with `conocimiento > 0`, in order of discovery; changed with `Historial.lista_agregar` |
| `retrocesos` | int | Count of rewinds done; **not** written through the history; read by a trip to detect a scroll (FR-025) |

## State transitions

```text
Sala.conocimiento
  0 --(an explored room has an exit to it)--> 1
  0|1 --(player enters it, or torch explores it)--> 2
  any --(rollback of the action that raised it)--> previous value

Salida.memoria
  any --(player leaves a room: both faces of each of its doors)--> real state at that moment
  any --(rollback of that move)--> previous value
```

Torch exploration raises the neighbor to 2 and its exits' destinations to 1; it never writes
`memoria`. The door joining the room entered to that neighbor is already observed because it touches
the player's room (clarification Q1).

## Value objects (model, no persistence)

- **Viaje**: destination room, the move function given by the service, the player's life before the
  current step, the value of `Partida.retrocesos` when the trip began.
- **Motivo de parada**: `LLEGADA`, `ENEMIGOS`, `DANO`, `FIN_PARTIDA`, `SIN_RUTA`, `RETROCESO`.
- **Resultado de ruta**: next exit (or none) and the cost `d`.

## DTOs (layer boundary)

| DTO | Fields |
|---|---|
| `SalidaVistaDTO` (changed) | `direccion`, `nombre_destino` (**`None`** when the destination is not explored), `cerrada` (state shown, FR-003), `costo` |
| `MapaVistaDTO` (new) | `id_sala_actual`, `salas` (explored, sorted by id: list of `SalaConocidaDTO`) |
| `SalaConocidaDTO` (new) | `id_sala`, `nombre`, `salidas` (list of `SalidaConocidaDTO`) |
| `SalidaConocidaDTO` (new) | `direccion`, `id_destino` (`None` if the destination is only sighted), `nombre_destino` (`None` if sighted), `costo`, `puerta` (`"abierta"`, `"cerrada"` or `"sin observar"`) |
| `ViajeResultadoDTO` (new) | `aceptado` (bool), `motivo` (text key of the stop reason or of the rejection), `pasos` (int) |

Sighted rooms appear only as an exit of an explored room with no id and no name: the player learns
only that a room exists behind that exit (FR-004).
