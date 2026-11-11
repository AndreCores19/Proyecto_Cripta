# Implementation Plan: Hunter Enemy

**Branch**: `002-hunter-enemy` | **Date**: 2026-11-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-hunter-enemy/spec.md`

## Summary

A new enemy behavior, `cazador`, is added. The catalog entry carries `rango` (cost units; missing
means 0). On its turn a hunter that is not in the player's room asks a search object for the route
cost `d` to the player's room over open exits, and moves through the exit chosen by the spec's
tie-break, or waits. The move goes through the existing `Partida._programar_movimiento`, so its
duration is already the spec 001 rule; the agenda stays the event queue.

The search is a Dijkstra search **run backwards from the player's room** (over incoming exits), so
that one run gives the distance of every room to the player. It is bounded by a cost limit, so its
work is proportional to the region within reach and not to the crypt (FR-018). Rooms are marked
with a per-search stamp stored in plain integer fields on `Sala`, so nothing is cleared between
runs and no `dict` or `set` is used. The search needs a priority queue: this plan adds a generic
hand-written min-heap, `structures/monticulo.py`, and keeps the part-one agenda heap untouched
(research R1).

Three ways of working out decisions are implemented behind one small class so that `--bench` can
compare them (FR-019): one search per hunter turn, one shared search per turn, and one search shared
by all hunters and reused until the state changes. Correctness of all three is checked against an
independent oracle in the tests (FR-011). The default is chosen from the measurements, with a
decision rule fixed in advance (§Measurements).

The hunter is shown in the room view through a boolean field on the enemy entries of the existing
`EstadoVistaDTO`. Catalog reading goes through the existing `FichaEnemigoDTO` and repository.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `requests` (unchanged); no new dependencies

**Storage**: Unchanged. `rango` is one more field of the catalog entry, so it is cached with the
entry by the existing catalog cache (keyed by catalog version) and read from the offline recording
in `--offline`. Nothing about hunters is written to saved games or replay logs.

**Testing**: pytest (`tests/`), one test per acceptance scenario, each citing its FR. An independent
oracle (plain repeated relaxation over lists, in `tests/`) checks every strategy on seeded random
crypts with doors that change.

**Target Platform**: Desktop console (Windows/Linux), headless `--replay` and `--bench`

**Project Type**: CLI game, five-layer architecture (data → logic → service → controller → view)

**Performance Goals**: FR-017 / SC-007: with ≥ 24 active hunters on the reference crypt, the 99th
percentile of the event cycle is ≤ 20 ms and the maximum is reported. FR-018 / SC-008: a small-`rango`
decision in a crypt ≥ 10× larger costs ≤ 2× the decision in the smaller one.

**Constraints**: Constitution I (no `dict`/`set`/`heapq`/`bisect`/`collections`, no graph library;
every auxiliary structure is ours), II (fixed tie-breaks), III (DTOs; no view in `--bench`/`--replay`),
IV (nothing crypt-specific hardcoded), V (no new request), VI (benchmarks deterministic by seed),
VIII (this plan adds no rule).

**Scale/Scope**: Reference-crypt size (the largest scenario of `bench/bench_ciclo.py`, 100 rooms),
24–30 hunters, synthetic crypts of 100 to 1000+ rooms for the FR-018 comparison.

## Constitution Check

*GATE: checked before Phase 0 and re-checked after Phase 1 — PASS.*

### Structures Gate

| Item | Status | Notes |
|---|---|---|
| No `dict`/`set` as index or cache in an evaluated structure | PASS | The distance of each room lives in two integer fields of the room (`busq_marca`, `busq_dist`), validated by a stamp. The search frontier is our heap. The per-state cache is five plain attributes on the decider. Incoming exits are a list on each room. The `dict` that `json` returns while parsing the catalog and skeleton is input parsing, not an index. |
| No `heapq`, `bisect`, `collections` | PASS | `structures/monticulo.py` is hand-written (R1). |
| No graph or pathfinding library | PASS | Bounded Dijkstra written by us in `model/ruta_cazador.py`. |
| Hand-written structures cover hunter pathfinding, route invalidation | PASS | Pathfinding: `MonticuloMinimo` + stamped search. Route invalidation: door epoch counter + player-room identity + limit + "no other search since" check (R4); the oracle in the tests is independent of all of them. |

### Architecture Gate

| Item | Status | Notes |
|---|---|---|
| `model/` and `structures/` import nothing from `view/` or `controller/` | PASS | `model/ruta_cazador.py` imports only `structures/monticulo.py`. |
| `--replay` and `--bench` create no view class | PASS | New `bench/bench_cazador.py` and the new `bench_ciclo` scenario build `Partida` objects and never import `view/`. Replay already runs the controller with `vista=None` (spec 001). A test runs a replay of a game with a hunter and checks that no `view/` class is instantiated. |
| DTOs at every layer boundary | PASS | The hunter mark is a boolean on `EnemigoVistaDTO`, an entry of `EstadoVistaDTO.enemigos`. The view never receives `Enemigo`. |

### Process Gate

| Item | Status | Notes |
|---|---|---|
| `spec.md` committed before implementation | PASS | Commit `3ad9823` (spec and clarifications). Spec corrections go in their own commit. |
| Every task cites its FR | PENDING | Enforced when `tasks.md` is generated. |
| Every scenario has a test citing its FR | PENDING | Mapping in [quickstart.md](./quickstart.md). |

### Principles

| Principle | Status | Notes |
|---|---|---|
| II. Determinism | PASS | Decisions are made from distances and from the explicit tie-break `(room id, direction name)`, both fixed. Distances are minima, so they do not depend on the order in which equal-priority entries leave the heap. The heap's own order between equal priorities (insertion order) is a fixed rule that never reaches a decision, and no tie is resolved by data order or by the iteration order of a collection. A test permutes the order of `Sala.salidas` and `Sala.entradas` and checks that decisions do not change (T029). Benchmark crypts come from seeded `random.Random`. |
| IV. No hardcoded data | PASS | `"cazador"` is a behavior name, like `"errante"` and `"rastreador"` already in `Partida`. `rango` comes from the catalog; the default 0 is a spec rule (FR-001). |
| V. Network budget | PASS | No new request. A hunter moving into a room whose content is not downloaded does not trigger a download: only `JuegoService.mover` (the player) calls `poblar_sala`. |
| VI. Evidence-backed performance | PASS (pending data) | Strategy choice, the 20 ms claim and the agenda decision under the new load come only from §Measurements. The "before" baseline is saved before any change. |
| VIII. What goes where | PASS | Search, heap and stamps are design; the rules stay in the spec. |

## Design

### Where each requirement lands

| FR | Layer | Change |
|---|---|---|
| FR-001 | dto + data + model | `FichaEnemigoDTO.rango` (`datos.get("rango")`, `None` → 0, no other check). `FabricaModelo.crear_enemigo` passes it to `Enemigo.rango`. `Enemigo.es_cazador()` is `comportamiento == "cazador"`. |
| FR-002 | model | Already the first rule of `Partida._actuar_enemigo` for every enemy sharing the player's room. No change. |
| FR-003, FR-004, FR-005 | model | New branch in `_actuar_enemigo`: `comportamiento == "cazador"` → `salida = self._decidir_cazador(enemigo)`. `None` falls into the existing wait branch (`COSTO_ESPERAR`). |
| FR-006 | model | A non-`None` exit goes to the existing `_programar_movimiento(enemigo, salida)` (spec 001). No second movement path. |
| FR-007 | model | The decider scans the open exits of the hunter's room and keeps the one with the lowest `(destino.id, direccion)` among those with `salida.costo + dist(destino) == d`. |
| FR-008, FR-010 | model | The search reads only the skeleton (`Sala.salidas`, `Salida.costo`, `Salida.cerrada`) and the player's room. Room content (`objetos`, `trampas`, `inactivos`) is never read. |
| FR-009 | model | The search skips closed exits. Nothing in it can write a door. |
| FR-011, FR-012 | model | The decision is made inside the enemy turn with the state at that moment. Reuse (E2) is guarded by the door epoch, the player's room and the bound (R4). |
| FR-013 | model | `_decidir_errante` and `_decidir_rastreador` are not touched. |
| FR-014 | all | No new source of randomness. Stamps and the heap's insertion counter are deterministic. A replay test with hunters compares the final state of a recorded and a replayed game. |
| FR-015 | data | Hunters come only from catalog entries. |
| FR-016 | service + dto + view | `EnemigoVistaDTO.cazador` (bool, default `False`). `JuegoService.estado_vista` fills it from `Enemigo.es_cazador()`. `VistaConsola` prints `(cazador)` after the name. Rooms without hunters print exactly as before ([contracts/room-view-hunter.md](./contracts/room-view-hunter.md)). |
| FR-017 | bench | `bench/bench_ciclo.py` gets a scenario with 30 hunters (§Measurements). Its report already gives the 99th percentile and the worst cycle. The "before" results are saved first (§Measurements, step 0). |
| FR-018 | model | Bounded search with stamps: no per-run initialisation of the crypt; it stops once the popped distance would exceed the limit, and the limit is never smaller than the asking hunter's `rango` (§The search, §The decider). |
| FR-019 | bench | New `bench/bench_cazador.py` (§Measurements). |
| FR-020 | bench | Crypts come from `random.Random(seed)`. |
| FR-021 | bench | `bench/` imports nothing from `view/` (checked by `grep`). |
| FR-022 | model | No change: an enemy is activated only by `_entrar_en_sala`; before that it sits in `Sala.inactivos` with no pending event, so it takes no turns. |

### The generic min-heap (`structures/monticulo.py`)

Own binary heap, array-based. Contract in [contracts/monticulo.md](./contracts/monticulo.md):
`insertar(prioridad, valor)`, `extraer()`, `proximo()`, `vaciar()`, `len()`. Priorities are any
values that support `<` (numbers or tuples); two entries whose priorities are equal under `<` come
out in insertion order. There is no decrease-key: a search inserts a room again with a better cost
and skips the stale entry when it comes out. Complexity: O(log n) for `insertar` and `extraer`,
O(1) for `proximo` and `vaciar`. Spec 003 ("ir a") reuses it unchanged.

Reuse of the agenda heap was evaluated and rejected; the reasons are in research R1.

### The search (`model/ruta_cazador.py`)

`Busqueda.calcular(origen, limite)`:

1. New stamp `e` from `Busqueda.nueva_estampa()`: one counter shared by **every** `Busqueda` object (and by any other search that uses the room fields, see "Sharing the room fields"), so a stamp never repeats. Mark `origen` (`busq_marca = e`, `busq_dist = 0`) and insert it with priority 0.
2. Extract `(d, sala)`. If `d > limite`, **stop the search**. If `d > sala.busq_dist`, skip (stale entry).
3. For each **incoming** exit `x` of `sala` (`Sala.entradas`) that is open: `nd = d + x.costo`, `v = x.origen`. If `nd > limite`, skip: the entry is never inserted. An exit that lands exactly on `limite` is kept, because `d == rango` must still move. If `v.busq_marca != e` or `nd < v.busq_dist`, set both fields and insert `(nd, v)`.
4. The distance of room `r` to the player is `r.busq_dist` when `r.busq_marca == e`, else "farther than `limite`, or no route".

**Stop rule (FR-018)**: step 3 never inserts a distance above `limite`, so step 2 never pops one; the explicit stop in step 2 is the guard that keeps this true if step 3 is edited. A search therefore never processes a room whose distance exceeds the limit it serves, and the limit is always at least the `rango` of the hunter that asked (next section).

Running backwards gives, for every room, the cost of going **to** the player, even when a connection has an exit in one direction only (spec 001 edge case: an exit with no opposite). All costs are exact for rooms with distance ≤ `limite` (Dijkstra with pruning). Cost: O(V_r log V_r + E_r) with V_r, E_r the rooms and exits within `limite`; no O(V) setup.

### The decider (`model/ruta_cazador.py`, class `DecisorCazador`)

`decidir(partida, cazador, limite_forzado=None)` returns the exit to take or `None` (wait). `limite_forzado` exists only so that tests can force a limit; production code never passes it.

1. `limite`: `cazador.rango` for the individual mode; `max(cazador.rango, the largest rango among living active hunters in partida.enemigos)` for the shared modes (the `max` with the asking hunter's own `rango` keeps the limit correct even if that hunter is not yet in `partida.enemigos`). Reading `partida.enemigos` only decides **how far** the search goes; the decision itself never depends on other hunters (FR-010), and the three modes give the same result. If `limite_forzado` is given, it replaces this limit.
2. Get a stamp: run `calcular(jugador.sala, limite)` unless the mode reuses a valid earlier one. **Invariant: the limit of the search whose stamp is used is never smaller than `cazador.rango`.** A cached search whose limit is smaller is not used: it is replaced by a new search (below). `decidir` raises `RuntimeError` if the invariant does not hold; by construction it never does, and a test forces the case with `limite_forzado` smaller than `cazador.rango`.
3. `d = distancia(cazador.sala)`. If it is `None` or `d > cazador.rango`: return `None`. Because of the invariant, `None` really means "no route, or `d > rango`", never "the search did not reach this far".
4. Over the open exits `s` of `cazador.sala`: candidate if `distancia(s.destino)` exists and `s.costo + distancia(s.destino) == d`. Keep the candidate with the lowest `(s.destino.id, s.direccion)`. Return it.

| Mode | Search per decision | Limit | Reuse |
|---|---|---|---|
| `individual` | one per hunter turn | own `rango` | none |
| `compartido_sin_reuso` | one per hunter turn | `max(own rango, largest)` | none |
| `compartido` | one per **state** | `max(own rango, largest)` | until the state changes |

State = `(player's room, door epoch, limit)`. The cached search is valid when all four hold:

1. `jugador.sala is sala_guardada` (the player is in the same room).
2. `Salida.epoca_puertas == epoca_guardada` (no door has changed).
3. `cazador.rango <= limite_guardado` (the search reached far enough for the hunter now asking).
4. `Busqueda.ultima_estampa == estampa_guardada` (no other search has run since: see "Sharing the room fields").

If (3) fails (a hunter with a bigger `rango` was activated, or is simply the first one asking), the cached search is **recomputed with the new limit, not extended**. Extending would mean keeping the frontier and the stamps of the old search alive between turns; a new search costs O(region) anyway and only happens when a hunter with a bigger `rango` asks or the state changed. The new limit is `max(cazador.rango, largest)` and replaces the cache, so the next hunters with a smaller or equal `rango` reuse it.

`Salida.cerrada` becomes a property whose setter adds 1 to the class counter `Salida.epoca_puertas`. Every door change, including the writes that `Historial.deshacer` makes when the player rewinds, goes through `setattr`, so it bumps the counter; a cache can never survive a door change (R4). The counter only grows; a cache compares it for equality with the value it saved, so other `Partida` objects in the same process can only cause extra searches, never a stale decision.

`Partida` creates the decider in `__init__` (default chosen in §Measurements) and exposes it as `partida.decisor_cazador` so the benchmark can swap it. `_decidir_cazador(enemigo)` is `self.decisor_cazador.decidir(self, enemigo)`.

### Sharing the room fields with other searches (note for spec 003)

`busq_marca` and `busq_dist` hold the result of **one** search at a time. If another search writes them between two hunter turns, a cached stamp would no longer match the rooms, and the decider would read "not reached" for rooms that were reached, deciding to wait when it should move. The cache must detect this, or the other search must use other fields. This plan does the first, and spec 003 ("ir a") must follow one of two rules:

- **Rule A (preferred, needs nothing else)**: the "ir a" search takes its stamps from `Busqueda.nueva_estampa()` (use `Busqueda`, or call that method). The counter is shared by all searches, so stamps never collide, and `Busqueda.ultima_estampa` records the latest one. Condition 4 of the cache check then fails after an "ir a" run, and the next hunter decision recomputes. Cost: one extra search per "ir a" run, only when hunters are active.
- **Rule B**: "ir a" adds its own fields to `Sala` (for example `ira_marca`, `ira_dist`) and never touches `busq_*`; then it cannot disturb the hunters' cache and condition 4 is never triggered by it.

Either way, both searches must never run at the same time (the game is single-threaded, and a decision reads its result right after computing it). Hunters in modes `individual` and `compartido_sin_reuso` compute a fresh search on every decision, so they are not affected by any other search. A test runs an unrelated search between two hunter turns and checks that the decision equals the reference (US3, FR-011).

### Complexity (engine)

- Decision, `individual`: O(V_r log V_r + E_r), r = region within the hunter's `rango`.
- Decision, `compartido`: O(1) validity check + O(exits of the hunter's room) when the state is unchanged; one search O(V_R log V_R + E_R) per state change (R = largest `rango`).
- `calcular` never touches rooms outside the region it reaches (stamps), so FR-018 holds for `individual` and for `compartido` when the largest `rango` is small.
- Cost of the door counter: O(1) per door write.

## Measurements (Constitution VI, FR-017 to FR-020)

Everything is deterministic by seed (`random.Random(seed)`), local, without network or rendering,
and imports nothing from `view/`.

**0. Baseline "before" (first implementation step, before any code edit)**: before touching
anything that sits in the event cycle (`model/`, `structures/`, `data/`, `service/`, `dto/` for this
feature), run on the current code and save the output unchanged:

```powershell
python -m bench.bench_ciclo   > specs/002-hunter-enemy/bench-antes-ciclo.txt
python -m bench.bench_agenda  > specs/002-hunter-enemy/bench-antes-agenda.txt
```

This is the first task of the implementation phase, ahead of every other task. After the last
change, run the same commands into `bench-despues-ciclo.txt` and `bench-despues-agenda.txt`. The
three part-one scenarios of `bench_ciclo` (`normal`, `grande`, `extremo`, no hunters) keep the
part-one criterion of p99 <= 20 ms. Their average per cycle is also compared with the "before" file
as an **investigation trigger, not an acceptance gate**: if the average is more than 10% slower (best
of 3 runs each, same machine, because the machine noise seen in spec 001 reached 2x), the cause is
looked for and written down before moving on. It does not fail the feature by itself. The likely
cause would be `Salida.cerrada` becoming a property or the extra list append in `agregar_salida`.

**1. Event cycle with hunters (FR-017, SC-007)** — extend `bench/bench_ciclo.py`.
`armar_partida_cazadores(num_salas, num_enemigos, num_cazadores, semilla)`: a chain of rooms with
costs from the same set as `armar_partida_costos`, `num_enemigos - num_cazadores` wanderers and
`num_cazadores` hunters with `rango` drawn from the values (100, 300, 1000). Each entry of
`ESCENARIOS` becomes `(nombre, salas, enemigos, cazadores)`, with `cazadores` = 0 for the three
part-one scenarios (their builder and output do not change); `ejecutar` builds the game with
`armar_partida_cazadores` when `cazadores > 0` and with `armar_partida` otherwise. Two new scenarios,
run with the same 3000 player actions and the same report (average, p99, worst):

- `("cazadores", 100, 300, 30)`: 30 hunters with the `rango` values above.
- `("cazadores_rango_total", 100, 300, 30)`: the same crypt with every hunter's `rango` set to 1000000, so each decision can reach the whole crypt (spec edge case "a hunter with a very large `rango`").

Verdict for every scenario in the file: p99 <= 20 ms. `bench_ciclo.py` uses **one convention** matching
the spec's "at most 20 ms": the single comparison `p99 < LIMITE_MS` becomes `p99 <= LIMITE_MS`, and the
closing line states the same rule ("p99 <= 20 ms"). It applies to the three part-one rows and to the
hunters rows alike, so no row is judged by a different rule. The measured numbers do not change; only
a p99 of exactly 20.0 ms would be judged differently. The baseline files saved before any change
(`bench-antes-ciclo.txt`) keep the old wording of the verdict; compare the numbers, not the verdict
word. The worst cycle is printed as information. When the course publishes the
reference crypt, the measurement is repeated with it and that result prevails (spec Clarifications).

**2. Comparisons (FR-019)** — new `bench/bench_cazador.py`, one table per row:

| Comparison | Modes run | Door situations |
|---|---|---|
| one hunter vs many (1, 10, 30, 100 hunters) | `compartido` | doors almost fixed |
| small vs large `rango` (200 vs 5000 on 100 and 1000 rooms) | `compartido` | doors almost fixed |
| one search per hunter vs shared | `individual` vs `compartido_sin_reuso` vs `compartido` | often / almost never |
| reusing vs always recomputing | `compartido` vs `compartido_sin_reuso` | often / almost never |

Doors: the benchmark opens or closes seeded random doors through `Partida._poner_cerrada`, the same
call the game's own door rules use. "Often" = one door change per player action; "almost never" =
one per 500 player actions. Each cell reports microseconds per player action (average of 3000) and
the number of searches run. Before timing, every mode runs the same seeded action list and the
program asserts that all hunter decisions are identical (FR-019, FR-011).

**3. Scaling with crypt size (FR-018, SC-008)** — same bench: one hunter with `rango` 200 in crypts
of 100 and 1000 rooms, built so that the region within `rango` is identical (same local layout, the
rest of the crypt added around it). Output: µs per decision in each, and their ratio.

**4. Review of the part-one agenda under the new load (assignment section 5.6)**: extend
`bench/bench_agenda.py` (measurement code only), as spec 001 did:

- **What changes in the load**: dozens of active hunters, each with one pending event like any enemy, and variable move costs (spec 001). A hunter's move is paid at the exit's cost and its attack or wait at 100, so the mix of operations per player action and the number of pending events can differ from the wanderers-only load.
- **Operations per player action**: run `contar_operaciones` on `armar_partida_cazadores` with 300, 1000 and 3000 enemies, 30 of them hunters (and a run with 10% hunters). Output: `programar`, `extraer`, `cancelar`, `reprogramar` per action and the maximum number of pending events, next to the wanderers-only run of spec 001.
- **Candidates**: the same three as part one (binary heap, unsorted list, sorted list), same sizes (100, 300, 1000, 3000) and the variable-increment model of spec 001, re-run in the same session as the hunters counts so they can be compared.
- **Decision rule**: the one of spec 001. Keep the binary heap if it is the fastest, or within 10% of the fastest, at every size >= 300. If it fails, the numbers go in the table below and the agenda decision is reopened in a separate commit.
- **Output** is saved to `specs/002-hunter-enemy/bench-agenda-cazadores.txt`.

**Decision rule for the hunter mode (fixed before measuring)**:
- The default mode is `compartido` if, in every row of (2), it is the fastest or within 10% of the fastest of its row, and (1) and (3) pass (p99 <= 20 ms in both hunters scenarios; ratio ≤ 2).
- If `compartido` fails a row, the default becomes the fastest mode that passes (1) and (3); if none passes, the plan is reopened in a separate commit.
- `individual` stays in the code in every case: it is the baseline of the comparison and the reference for the equivalence tests.

| Measurement | Result | Decision |
|---|---|---|
| p99 event cycle, 30 hunters, 100 rooms | *pending (task)* | |
| p99 event cycle, 30 hunters whose `rango` reaches the whole crypt | *pending* | |
| one hunter vs many | *pending* | |
| small vs large `rango` | *pending* | |
| per hunter vs shared, doors often / almost never | *pending* | |
| reuse vs recompute, doors often / almost never | *pending* | |
| decision time ratio, 1000 vs 100 rooms, same region | *pending* | |
| agenda under 30 hunters, variable costs: ops per action, max pending (300 / 1000 / 3000 enemies) | *pending* | |
| agenda candidates under the new load, µs per extract + schedule at n = 300, 1000, 3000 (heap / unsorted / sorted) | *pending* | heap kept if the rule passes |
| event cycle before vs after, no hunters (`normal`, `grande`, `extremo`) | *pending* | |

## Project Structure

### Documentation (this feature)

```text
specs/002-hunter-enemy/
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── monticulo.md
│   ├── hunter-decision.md
│   ├── catalog-hunter.md
│   └── room-view-hunter.md
├── checklists/requirements.md
├── bench-antes-ciclo.txt          # baseline, saved before any code change
├── bench-antes-agenda.txt         # baseline, saved before any code change
├── bench-despues-ciclo.txt        # same commands after the last change
├── bench-despues-agenda.txt
├── bench-agenda-cazadores.txt     # section 5.6 review under hunters
├── bench-cazador.txt              # FR-019 / FR-018 comparisons
├── estado-sin-cazadores-antes.txt # seeded games without hunters, captured before any change (SC-006)
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
structures/monticulo.py        # new: generic min-heap (ties by insertion order); reused by spec 003
model/ruta_cazador.py          # new: Busqueda (bounded backwards search with stamps), DecisorCazador (3 modes)
model/sala_logica.py           # Salida.cerrada property + class counter epoca_puertas, Salida.origen;
                               #   Sala.entradas, busq_marca, busq_dist; agregar_salida fills origen/entradas
model/enemigo_logica.py        # + rango, es_cazador()
model/partida_logica.py        # _decidir_cazador, "cazador" branch in _actuar_enemigo, decisor_cazador
structures/agenda.py           # unchanged
dto/ficha_dto.py               # FichaEnemigoDTO.rango (missing → 0)
dto/estado_vista_dto.py        # EnemigoVistaDTO.cazador (bool, default False)
data/fabrica_modelo.py         # crear_enemigo passes rango
service/juego_service.py       # estado_vista / enemigos_en_sala fill EnemigoVistaDTO.cazador
view/vista_consola.py          # enemy line shows (cazador)
bench/bench_ciclo.py           # armar_partida_cazadores + "cazadores" scenario
bench/bench_agenda.py          # section 5.6: part-one candidates under hunters + variable costs
bench/bench_cazador.py         # new: FR-019 comparisons and FR-018 scaling
main.py                        # --bench also runs bench_cazador
tests/test_monticulo.py        # new: order, ties, stale entries, 1000 random inserts vs sorted list
tests/test_cazador_decision.py # new: US1, US2 scenarios, FR-001 default rango, FR-022 inactive
tests/test_cazador_equivalencia.py # new: US3 + FR-014; seeded random crypts vs independent oracle,
                               #   all modes, doors change, player moves, deaths, rewind, another
                               #   search between turns, shared cache with a bigger-rango hunter
tests/test_cazador_conocimiento.py # new: US4 (fog, content not downloaded, same result either way)
tests/test_catalogo_cazador.py # new: US5 (catalog entry, no rango, other behaviors unchanged)
tests/test_vista_cazador.py    # new: US6 (mark, room without hunters unchanged)
tests/test_bench_cazador.py    # new: US7 (seed determinism, no view class, modes agree)
tests/test_replay_cazador.py   # new: record + replay a game with a hunter (FR-014, FR-021)
tests/test_puertas.py          # +: Salida.origen, Sala.entradas, door epoch counter
tests/mapas_cazador.py         # new helper: fake crypt builders and the independent oracle
tests/estado_sin_cazadores.py  # new helper: final state of seeded games without hunters
tests/capturar_estado_sin_cazadores.py # new: writes estado-sin-cazadores-antes.txt (run once, before any code change)
```

**Structure Decision**: existing single-project layered layout. This feature adds one structure,
one model module, one benchmark module and test files; every other change is a few lines in files
that already hold the related part-one logic.

## Complexity Tracking

No constitution violations to justify. The second heap (research R1) is a design trade-off, not a
violation.
