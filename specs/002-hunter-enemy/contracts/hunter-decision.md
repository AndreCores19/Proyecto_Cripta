# Contract: hunter decision (`model/ruta_cazador.py`, called from `Partida`)

## Entry point

`Partida._actuar_enemigo(enemigo)` for a hunter:

1. Same room as the player → attack (existing rule, FR-002). Done.
2. Otherwise `salida = self._decidir_cazador(enemigo)`, which is `self.decisor_cazador.decidir(self, enemigo)`.
3. `salida is not None` → the existing move code: change room, log "se mueve hacia …", `_programar_movimiento(enemigo, salida)` (FR-005, FR-006).
4. `salida is None` → the existing wait code: log "espera", schedule `COSTO_ESPERAR` (FR-004).

There is no other way for a hunter to move.

## `DecisorCazador.decidir(partida, cazador, limite_forzado=None)` → `Salida` or `None`

`limite_forzado` is for tests only (it replaces the search limit so the invariant error can be provoked); production code never passes it.

Inputs it may read (FR-010): `Sala.salidas`, `Sala.entradas`, `Salida.costo`, `Salida.cerrada`,
`Salida.destino`, `Salida.origen`, `Salida.direccion`, `Sala.id`, `partida.jugador.sala`,
`partida.enemigos` (only to find the largest `rango`: it decides how far a shared search goes, never the result, so the three modes agree and FR-010 holds), `cazador.sala`, `cazador.rango`.

Inputs it must not read: `Sala.objetos`, `Sala.trampas`, `Sala.inactivos`, whether a room's content
is downloaded, the player's `rastro` marks, the clock.

Invariant: the search whose result is read has a limit at least as large as `cazador.rango`; a cached
search with a smaller limit, or one overwritten by another search since (`Busqueda.ultima_estampa`),
is replaced by a new search. If the invariant fails, `decidir` raises `RuntimeError`.

Effects: it writes only `Sala.busq_marca` / `Sala.busq_dist` and its own cache. It never changes a
door, the history, the agenda or any actor.

Result:

| Situation | Result |
|---|---|
| no route within the search limit, or `d > cazador.rango` | `None` |
| a route of cost `d ≤ cazador.rango` | the open exit `s` of `cazador.sala` with `s.costo + dist(s.destino) == d` and the lowest `(s.destino.id, s.direccion)` |

## Equivalence rule (FR-011, SC-002)

For every mode and every state, the result equals the result of this reference computation: let
`dist(r)` be the least total cost of open exits from room `r` to the player's room, found by
repeated relaxation over all rooms with no stamps, no heap and no limit; `d = dist(cazador.sala)`;
`None` if `d` is infinite or greater than `rango`; otherwise the exit chosen as in the table above.

The reference is written in `tests/` (plain lists, no project structure) and compared with each
mode on seeded random crypts while doors open and close, the player moves, other actors die, and the
player rewinds.

## Modes

| Mode | Searches | Limit |
|---|---|---|
| `individual` | one per hunter turn | the hunter's `rango` |
| `compartido_sin_reuso` | one per hunter turn | `max(` own `rango`, largest of living active hunters `)` |
| `compartido` | one per state (player room, door epoch, limit, no other search since) | `max(` own `rango`, largest of living active hunters `)` |

All three give the same result; they differ only in cost (plan §Measurements).

## Room fields shared with other searches (note for spec 003)

`Sala.busq_marca` / `Sala.busq_dist` hold one search at a time. A later search ("ir a") must either
take its stamps from `Busqueda.nueva_estampa()` (the hunters' cache then detects it and recomputes)
or use its own fields. It must not write `busq_*` with a stamp from another counter.
