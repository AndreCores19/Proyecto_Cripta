# Research: Hunter Enemy

No NEEDS CLARIFICATION remained after `/speckit-clarify`. These notes record the decisions taken
while reading the existing code (`structures/agenda.py`, `structures/historial.py`,
`model/partida_logica.py`, `model/sala_logica.py`, `data/fabrica_modelo.py`, `dto/ficha_dto.py`).

## R1. Reuse or generalise the agenda heap?

- **Decision**: write a second, small, generic heap (`structures/monticulo.py`) and leave `structures/agenda.py` unchanged.
- **What was compared**:

| | Agenda heap as it is | Agenda heap generalised | New generic heap (chosen) |
|---|---|---|---|
| Item shape | `Evento` with fixed fields | any item, ordering and position hooks as parameters | any `(prioridad, valor)` |
| Order | hard-coded `(tiempo, num_sec)` | parameter | priority `<`, ties by insertion order |
| Undo hooks | every `programar`, `extraer`, `cancelar`, `reprogramar` registers a closure in `Historial` | must be switched off per call or per instance | none: a search must never touch the history |
| Cancel / reprogram by position (`Evento.pos`) | yes, O(log n) | kept | not needed (stale entries are skipped) |
| Risk to measured code | none | the hot path of spec 001's decision (§Measurements there) gets an extra indirection per comparison, and that measurement would have to be redone | none |
| New code | 0 | edits in the agenda + new tests | about 50 lines + tests |

- **Rationale**: the two jobs differ in the things that matter: the agenda needs position tracking and undo registration, the search needs neither and must be read-only with respect to the history. Generalising the agenda would mix them and would put in question the heap decision that spec 001 measured (the hot path would change, so the decision rule would have to be run again). A separate heap keeps the agenda exactly as measured. The cost is the sift-up/sift-down code written twice; each copy is about 25 lines and has its own tests.
- **Alternatives**:
  - Generalise the agenda: rejected for the reasons above.
  - Rebase the agenda on the new heap later: allowed only with a benchmark showing no regression (Constitution VI); not part of this feature.
  - `heapq`: forbidden (Constitution I).

## R2. Search direction

- **Decision**: search backwards from the player's room over **incoming** exits (`Sala.entradas`, each exit knows its `origen`), so one run gives the distance of every room to the player.
- **Rationale**: the player's room is the one thing all hunters share at a given moment. A forward search from each hunter would repeat work and could not be shared. Costs are the same in both directions of a connection (spec 001 FR-005), but a connection may have an exit in one direction only (spec 001 edge case), so a forward search from the player would answer "player to room", not "room to player". Using incoming exits is exact in that case too.
- **Alternatives**:
  - Forward search from the player over outgoing exits: wrong for one-way exits.
  - Forward search from each hunter: correct, but not shareable; it is not discarded as a mode, because `individual` is still a valid way to decide (it also searches backwards from the player but with the hunter's own limit).

## R3. Marking visited rooms without `dict` or `set`

- **Decision**: two integer fields on `Sala`, `busq_marca` (stamp of the last search that reached the room) and `busq_dist`, valid only when `busq_marca` equals the current stamp. Stamps come from one counter shared by every `Busqueda` object (`Busqueda.nueva_estampa()`), and the latest one is kept in `Busqueda.ultima_estampa`.
- **Rationale**: no initialisation pass over the crypt (FR-018), O(1) read and write, deterministic, and no forbidden structure. A room not reached by the current search simply has an old stamp.
- **A shared counter, not one per object**: two `Busqueda` objects (the hunters' and the one of spec 003) with their own counters could produce the same stamp, and a stale `busq_marca` would then look valid. A single counter rules that out.
- **Alternatives**: a `dict` or `set` of visited rooms (forbidden); a list indexed by room id cleared on every search (O(crypt) per search, breaks FR-018).

## R4. When is a reused search still valid?

- **Decision**: a cached search (mode `compartido`) is reused only while all four hold: the player is in the same `Sala` object; `Salida.epoca_puertas` equals the value saved with the search; the deciding hunter's `rango` is not larger than the limit the search used; and `Busqueda.ultima_estampa` equals the stamp saved with the search (no other search has overwritten the room fields since).
- **Rationale**: a decision depends only on the doors, the player's room, the hunter's room and `rango` (FR-010). The hunter's room and `rango` are read at decision time; the rest is what the cache has to guard. `Salida.cerrada` becomes a property whose setter adds 1 to a class counter. Door changes made by the game (`_poner_cerrada`) and the writes that `Historial.deshacer` makes when the player rewinds both use `setattr`, so both bump it. A direct comparison of "the state I used" against "the state now" would cost O(doors); the counter is O(1).
- **If the limit is too small**: the cached search is recomputed with `max(cazador.rango, largest)`, not extended. Extending needs the old frontier and stamps kept alive between turns; a new search is O(region) and happens only when a hunter with a bigger `rango` asks or the state changed. `decidir` also enforces the invariant "limit used >= asking hunter's `rango`" with a `RuntimeError`, so a hunter can never decide from a result that did not reach its `rango`.
- **Another search between two hunter turns** (the "ir a" travel of spec 003): detected by the fourth condition; spec 003 must take stamps from the shared counter or use separate fields (plan §Sharing the room fields).
- **Over-invalidation is accepted**: any door change anywhere invalidates every cache. It costs extra searches, never a wrong decision. The benchmark ("doors change often") measures that cost.
- **Alternatives**:
  - A counter incremented only in `Partida._poner_cerrada`: rejected, because rewinding bypasses it and would leave a stale search.
  - Per-room dirty marks: more precise, much more code, no evidence it is needed.
  - Also guarding on the player's position by a counter instead of identity: not needed, identity of the room object is exact.

## R5. The cost limit of the search

- **Decision**: individual mode uses the hunter's `rango`; shared modes use the largest `rango` among living active hunters, computed when a search is started.
- **Rationale**: distances are exact for every room within the limit, and a hunter only needs distances up to its own `rango` (its room and its neighbours on a route of cost `d ≤ rango`). A limit smaller than `rango` would be wrong; a bigger one only costs time. A hunter activated later with a bigger `rango` finds `rango > limite_guardado` and forces a new search.
- **Alternatives**: unbounded search (O(crypt) for every hunter, breaks FR-018); a fixed constant limit (would hardcode a number unrelated to the catalog).

## R6. Tie-break

- **Decision**: among exits `s` of the hunter's room with `s.costo + dist(s.destino) == d`, keep the one with the lowest `(s.destino.id, s.direccion)`.
- **Rationale**: FR-007 gives the room id; the direction name is the fixed rule the spec's Assumptions add for two exits to the same neighbour. Both are data, not collection order (Constitution II).
- **Alternatives**: first exit in room order (depends on data order, forbidden as a tie-break).
- **The heap's order between equal priorities never reaches a decision**: `MonticuloMinimo` returns equal priorities in insertion order, which follows the order of `Sala.entradas` and `Sala.salidas`. That is a fixed rule of the heap, but it is not what decides anything: the search only keeps minimum distances, which are the same whatever order equal-distance entries come out in, and the final choice uses the explicit `(room id, direction)` rule above. So no tie is resolved by data order (Constitution II). A test shuffles `Sala.salidas` and `Sala.entradas` and checks that every decision is unchanged (tasks T029). Any other feature that reuses the heap (spec 003) must break ties with an explicit rule of its own and must not rely on the heap's insertion order for its results ([contracts/monticulo.md](./contracts/monticulo.md)).

## R7. Reading `cazador` and `rango`

- **Decision**: `FichaEnemigoDTO` gets `rango` (`datos.get("rango")`; `None` becomes 0). `FabricaModelo.crear_enemigo` copies it into `Enemigo.rango`. `Partida` compares `comportamiento` with `"cazador"` the way it already does with `"errante"` and `"rastreador"`.
- **Rationale**: it is the existing path (catalog DTO → repository → factory). No value of `rango` is checked (FR-001). The catalog cache stores the raw entry JSON, so `rango` is cached with it and nothing in the cache format changes.
- **Alternatives**: a separate hunter class: rejected, because the behavior is already a string on `Enemigo` and the turn logic lives in `Partida`.

## R8. The hunter mark in the view

- **Decision**: `EnemigoVistaDTO.cazador` (bool, default `False`), part of `EstadoVistaDTO.enemigos`. `VistaConsola` prints `(cazador)` after the enemy's name. `JuegoService.estado_vista` fills it from `Enemigo.es_cazador()`.
- **Rationale**: the enemy entries are the only place a per-enemy mark can live inside `EstadoVistaDTO`, and the default keeps every existing constructor call and golden file valid. The view stays DTO-only (Constitution III). The spec leaves the form of the mark open (Assumptions); a text suffix is the least intrusive for the console.
- **Alternatives**: a list of hunter ids on `EstadoVistaDTO` (the view would have to join two lists); a colour or symbol (not portable across terminals).

## R9. What the benchmarks are, and the decision rule

- **Decision**: three modes (`individual`, `compartido_sin_reuso`, `compartido`) behind one class; `bench/bench_cazador.py` runs the FR-019 matrix; `bench/bench_ciclo.py` gets a hunters scenario for FR-017. A fixed rule picks the default mode (plan §Measurements).
- **Rationale**: the three modes separate the two effects FR-019 asks about: `individual` vs `compartido_sin_reuso` is "own limit vs shared limit" and per-hunter work; `compartido_sin_reuso` vs `compartido` isolates reuse. A mode "per hunter with reuse" was not added: the cache would need one distance array per hunter (the stamp fields on `Sala` hold one search at a time), and the question the spec asks is answered without it.
- **Alternatives**: measure only two modes (the spec asks for both comparisons, so one would be missing).

## R10. Doors that change in the benchmark

- **Decision**: the benchmark changes doors with `Partida._poner_cerrada` driven by a seeded RNG: one change per player action ("often") or one per 500 ("almost never").
- **Rationale**: it is the same call the game's own rules use (`abrir_puerta`, the automatic closing event), so the epoch counter and the history behave as in a real game, without needing keys or timers in a synthetic crypt. The spec's Assumptions describe these doors as changing "by the game's own rules"; this is the closest deterministic way.
- **Alternatives**: automatic-closing events scheduled in the agenda (the rate would depend on the clock and on enemy speeds, harder to keep at an exact rate).

## R11. Reference crypt

- **Decision**: until the course publishes it, the reference crypt is the synthetic 100-room crypt of the largest `bench_ciclo` scenario with 30 hunters. When the official crypt exists, the same scenario is run on it and that result replaces the synthetic one (spec Clarifications).
- **Also measured**: a variant where every hunter's `rango` reaches the whole crypt (spec edge case "a hunter with a very large `rango`"), since the 20 ms limit still applies there.
- **Alternatives**: wait for the official crypt before measuring: rejected, because the design choices (default mode) need data now.

## R12. Section 5.6 review and the "before" baseline

- **Decision**: the plan includes (a) saving the current `bench_ciclo` and `bench_agenda` output before any change to the event cycle, and (b) a review of the part-one agenda (binary heap vs unsorted and sorted lists) under the new load, with the decision rule of spec 001.
- **Rationale**: the assignment's section 5.6 asks to review the agenda decision when the load changes, and spec 001 did it for variable costs. Hunters add dozens of actors whose moves pay variable costs and whose number of operations per player action can differ, so the number of pending events and the operation mix must be measured again. A "before" file taken after the first edit would hide any slowdown caused by this feature (for example the `Salida.cerrada` property), so it is the first step of implementation. The comparison with it is an investigation trigger (more than 10% slower on average), not an acceptance gate: the spec sets no such criterion.
- **Alternatives**: rely on the spec 001 numbers only: rejected, because the load now includes hunters; take the baseline from git history later: rejected, because the machine and its noise change.
