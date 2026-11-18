# Implementation Plan: Fog of War and Automatic Travel

**Branch**: `003-fog-of-war` | **Date**: 2026-11-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-fog-of-war/spec.md`

## Summary

The player's knowledge becomes game state kept **on the crypt itself**: each room carries a
knowledge level (unknown, sighted, explored) and each door face carries the state remembered at the
last observation (never observed, open, closed). Both are small integers changed only through the
undo history, so the rollback scroll reverts them with everything else, and a game that is saved and
loaded (re-executed from its command list) rebuilds them exactly. A list of the rooms that are not
unknown, in order of discovery, lets the known map be read without walking the whole crypt.

Door observation is continuous (spec clarification Q2): while the player stands in a room, the
doors of that room are read from their real state; the remembered state is written when the player
**leaves** the room (and the torch never writes door memory but the one joining the two rooms,
clarification Q1). So no extra event or hook on door changes is needed.

"ir a" is a bounded Dijkstra run **backwards from the destination** over explored rooms and over
exits remembered as open, stopped as soon as the player's room comes out of the queue. One run gives
both the cost and the first step with the same tie-break as the hunter. The search reuses the
hand-written heap of spec 002 and the stamp scheme of the hunter search (rule A of the spec 002 plan),
so it never needs clearing and never disturbs the hunters' reuse of their own search.

A trip is a small object that performs one ordinary player move per step, recomputes the route
before each step, and stops for one of the reasons of FR-022. The controller writes the order as a
comment and each step as an individual move in the game log, so replay and saved games re-execute
the moves only.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `requests` (unchanged); no new dependencies

**Storage**: Unchanged. Knowledge is not a new file: saved games and logs store the seed and the
command list and are re-executed (spec 001/002 convention), so knowledge is rebuilt, never stored.
The log gains comment lines (contract [bitacora-comentarios.md](./contracts/bitacora-comentarios.md)).

**Testing**: pytest (`tests/`), one test per acceptance scenario, each citing its FR. An
independent oracle (plain repeated relaxation over lists, in `tests/`) checks every route and every
tie-break on seeded random crypts with doors that change.

**Target Platform**: Desktop console (Windows/Linux), headless `--replay` and `--bench`

**Project Type**: CLI game, five-layer architecture (data → logic → service → controller → view)

**Performance Goals**: FR-026 / SC-007: computing one step of "ir a" with the full known map of the
reference crypt takes at most 5 ms. The part-one and spec 002 event-cycle scenarios keep their
20 ms limit on the 99th percentile.

**Constraints**: Constitution I (no `dict`/`set`/`heapq`/`bisect`/`collections`, no graph library),
II (fixed tie-breaks), III (DTOs; no view in `--bench`/`--replay`), IV (nothing crypt-specific
hardcoded), V (no new request: exploring never downloads room content), VI (benchmarks
deterministic by seed), VIII (this plan adds no rule; see "Points for the spec").

**Scale/Scope**: The largest published crypt (cripta-06) has 300 rooms, so the verdict is measured with a
synthetic crypt of 300 rooms; synthetic crypts of 100, 500 and 1000 rooms are reported for information
(100 is the size of the largest `bench/bench_ciclo.py` scenario).

## Constitution Check

*GATE: checked before Phase 0 and re-checked after Phase 1 — PASS.*

### Structures Gate

| Item | Status | Notes |
|---|---|---|
| No `dict`/`set` as index or cache in an evaluated structure | PASS | Known map = two integer fields (`Sala.conocimiento`, `Salida.memoria`) plus a plain list of discovered rooms. The route search marks rooms with the existing per-search stamp fields. The frontier is our heap. |
| No `heapq`, `bisect`, `collections` | PASS | Reuses `structures/monticulo.py`; display order uses our `structures/ordenamientos.py`. |
| No graph or pathfinding library | PASS | The search is written by us in `model/ruta_conocida.py`. |
| Hand-written structures cover known map, undo history | PASS | Known map: fields + discovery list. Undo: every write goes through the existing `Historial` (`asignar`, `lista_agregar`). |

### Architecture Gate

| Item | Status | Notes |
|---|---|---|
| `model/` and `structures/` import nothing from `view/` or `controller/` | PASS | New model files import only `structures/` and other model files. |
| `--replay` and `--bench` create no view class | PASS | `bench/bench_ir_a.py` builds `Partida` objects directly. Replay already runs with no view; `ir a` and `mapa` print through the controller's guarded helpers. A test replays a game with a trip and checks that no `view/` class is instantiated. |
| DTOs at every layer boundary | PASS | `MapaVistaDTO`, `ViajeResultadoDTO`, and a changed `SalidaVistaDTO` (destination name may be absent). The view never receives a `Sala`. |

### Process Gate

| Item | Status | Notes |
|---|---|---|
| `spec.md` committed before implementation | PASS | Commits `0773eaf` and `64b8c88`. A spec correction goes in its own commit first (Constitution VII). |
| Every task cites its FR | PASS | Every task of `tasks.md` (T001 to T056) cites its FRs. |
| Every scenario has a test citing its FR | PASS | Mapping in [quickstart.md](./quickstart.md) and the scenario-coverage list of `tasks.md`; T051 maps every Appendix B case. |

### Principles

| Principle | Status | Notes |
|---|---|---|
| II. Determinism | PASS | Route ties use `(room id, direction name)`, as the hunter. Knowledge depends only on the player's moves, the torch effect and door states, all deterministic. The discovery list is in order of discovery and is sorted by room id for display with our sort. |
| IV. No hardcoded data | PASS | Nothing about a crypt appears in code. |
| V. Network budget | PASS | Exploring (also by the torch) reads only the skeleton. Only `JuegoService.mover` calls `poblar_sala`, for the room the player enters, as today. |
| VI. Evidence-backed performance | PASS | The 5 ms claim and the cost of the bookkeeping on the event cycle come only from §Measurements: see `specs/003-fog-of-war/bench-ir-a.txt` (route and whole step), `bench-antes-ciclo.txt` and `bench-despues-ciclo.txt`. |
| VIII. What goes where | PASS | Structures and algorithms stay here; the rules stay in the spec. Gaps found while planning are listed in "Points for the spec" instead of being decided. |

## Design

### Where each requirement lands

| FR | Layer | Change |
|---|---|---|
| FR-001, FR-002 | model | `Sala.conocimiento` (0 unknown, 1 sighted, 2 explored). `Partida.__init__` explores the starting room before any action (not inside a history frame, so it is never undone). |
| FR-003 | model + service | An explored room shows name, exits, costs and door states. The door state shown is `Partida.puerta_recordada(salida)`: the real state if the door touches the player's room, otherwise the stored `Salida.memoria`. |
| FR-004, FR-005 | model | Exploring a room marks each exit's destination sighted when it is unknown. A room never touched stays 0. |
| FR-006 | model | Continuous observation by derivation (R3): doors touching the player's room are read live; `Partida._memorizar_puertas(sala)` writes `memoria` for both faces of every door of the room the player is leaving. |
| FR-007 | model | `memoria` changes only in `_memorizar_puertas`; a real change elsewhere does not touch it. |
| FR-008, FR-009 | model | When the player enters a room and the torch effect is active, `_explorar_vecinas` explores every neighbor through any exit. It reads only name and exits (skeleton). It never calls `_entrar_en_sala`, `activar_enemigo` or `activar_trampas`, and writes `memoria` only for the door joining the room entered to that neighbor (Q1: that door is touched by the player's room). |
| FR-010, FR-011 | service + view | `estado_vista` builds exits from knowledge (destination name only if the destination is explored). The skeleton is never shown directly. |
| FR-012 | model | Knowledge is derived from re-executing the saved command list (R5); a test saves, loads and compares. |
| FR-013, FR-014 | model | Every write to `conocimiento`, `memoria` and the discovery list goes through `Historial.asignar` / `lista_agregar` inside the action frame of the move. No new randomness. |
| FR-015 | controller + service + view | Command `mapa` → `JuegoService.mapa_vista()` → `MapaVistaDTO` → `VistaConsola.mostrar_mapa`. No game action, no time. |
| FR-016 | service + model | `ir a <id>`: the room must have `conocimiento == 2` or the order is rejected with no state change (contract [comando-ir-a.md](./contracts/comando-ir-a.md)). |
| FR-017, FR-018 | model | `RutaConocida` (R2): backwards search from the destination over explored rooms and over exits whose remembered state is open. Tie-break `(destino.id, direccion)`, as the hunter. |
| FR-019 | service | Each step is `JuegoService.mover` (the same path as the `w/a/s/d` commands), so time, clock events and trap/victory handling are the ones of an ordinary move. |
| FR-020 | model | The route is computed again inside every step, with the knowledge at that moment. Nothing is kept between steps. |
| FR-021 | model | The search and the trip never call `abrir_puerta`. |
| FR-022, FR-023, FR-028 | model + service + view | `Viaje` (R4) checks a rewind first at the start of each step, then the other reasons before and after the step (order in §Trips); a refused move stops the trip with `SIN_RUTA` (guard); the reason goes into `ViajeResultadoDTO` and is printed by the controller. |
| FR-024 | controller + adapters | Comment line for the order, one move line per step (R5, contract [bitacora-comentarios.md](./contracts/bitacora-comentarios.md)). |
| FR-025 | model + service | A scroll is a separate command, so it reverts the last step's history frame. `Partida` counts rewinds in a plain counter outside the history; a live trip notices a change and stops without another step. |
| FR-026, FR-027 | bench | New `bench/bench_ir_a.py` (§Measurements). |

### Knowledge on the crypt (`model/sala_logica.py`, `model/partida_logica.py`)

- `Sala.conocimiento`: integer, constants `DESCONOCIDA = 0`, `AVISTADA = 1`, `EXPLORADA = 2`.
  Plain field, like `rastro` and the stamp fields: no index, no hash.
- `Salida.memoria`: integer, constants `NO_OBSERVADA = 0`, `ABIERTA = 1`, `CERRADA = 2`. Both faces
  of a door always hold the same value (as `_poner_cerrada` does for `cerrada`), so one observation
  from either side serves the other.
- `Partida.conocidas`: list of the rooms whose level is above 0, in order of discovery. A room is
  appended the first time it leaves level 0, through `historial.lista_agregar`, so rollback removes
  it.
- `Partida._subir(sala, nivel)`: if `nivel > sala.conocimiento`, `historial.asignar(sala,
  "conocimiento", nivel)` and, if it came from 0, `lista_agregar(conocidas, sala)`. Knowledge never
  goes down except by rollback.
- `Partida._explorar(sala)`: `_subir(sala, EXPLORADA)`, then `_subir(destino, AVISTADA)` for each
  exit whose destination is below `AVISTADA`. Cost O(exits of the room).
- `Partida._explorar_vecinas(sala)`: for each exit of `sala`, `_explorar(destino)`. Cost O(deg²).
- `Partida._memorizar_puertas(sala)`: for each exit of `sala`, `historial.asignar` of `memoria` on the
  exit and on its opposite (value from the current real `cerrada`). Cost O(exits).
- `Partida.puerta_recordada(salida)`: `NO_OBSERVADA` aside, returns the real state if
  `salida.origen is jugador.sala or salida.destino is jugador.sala`, else `salida.memoria`.
- `Partida.mover` (inside the action frame): `_memorizar_puertas(sala que deja)` before changing the
  room; after `_entrar_en_sala(destino)`: `_explorar(destino)` and, if
  `jugador.efecto_activo("antorcha")`, `_explorar_vecinas(destino)`. Torch exploration does not call
  `_entrar_en_sala` and does not run the trap code, so nothing is activated (FR-009).

### The route search (`model/ruta_conocida.py`, class `RutaConocida`)

`siguiente_paso(partida, destino)` returns `(salida, d)` for the next step, `(None, 0)` when the
player is already in `destino`, or `(None, None)` when no known route exists.

1. New stamp from `Busqueda.nueva_estampa()` (rule A of spec 002: one stamp counter for every search
   that uses the room fields, so the hunters' cached search is detected as stale and recomputed).
   The stamp is the very first step, before any early return, so even a search that finds no route (or
   an order whose player is already in `destino`) invalidates the hunters' cached search. The object keeps
   one `MonticuloMinimo` and calls `vaciar()` on it before every search: the search stops as soon as the
   player's room is extracted, so entries are left over (`Busqueda.calcular` instead creates a local
   heap per call).
   Mark `destino` with distance 0 and insert it in the heap.
2. Extract `(d, sala)`. If `sala is jugador.sala`, stop: its distance is final. Skip a stale entry.
3. For each incoming exit `x` of `sala` (`Sala.entradas`) with `x.origen.conocimiento == EXPLORADA`
   and `puerta_recordada(x) == ABIERTA`: `nd = d + x.costo`; relax `x.origen` with the stamp fields and
   insert it. `destino` is explored by FR-016, and the player's room is explored by construction.
4. If the player's room was not reached: `(None, None)`. Otherwise `d` is its distance. Over the
   exits `s` of `jugador.sala` with `puerta_recordada(s) == ABIERTA`, `s.destino.conocimiento ==
   EXPLORADA` and the destination marked with this stamp, with `s.costo + dist(s.destino) == d`,
   keep the one with the lowest `(s.destino.id, s.direccion)`.

Every neighbor with `s.costo + dist = d` has `dist < d`, because costs are at least 1, so it left the
heap before the player's room did and its distance is final when step 2 stops. Work is proportional
to the explored region closer to the destination than the player, not to the crypt. Cost: O(V_k log
V_k + E_k) over that region.

### Trips (`model/viaje_logica.py`, class `Viaje`)

`Viaje(partida, destino, mover)` receives the service's move function (so the step also downloads the
room content, exactly as `w/a/s/d` do). `paso()` returns `None` while the trip goes on, or a stop
reason: `FIN_PARTIDA`, `LLEGADA`, `ENEMIGOS`, `DANO`, `SIN_RUTA`, `RETROCESO`.

The console cannot interrupt a running trip (clarification 2026-11-12): the rewind check below exists for
the step-level case, where a test or a future interface drives the steps one at a time and reads a scroll
between two of them.

Order (FR-022 as amended on 2026-11-17). The order "end of the game, arrival, enemies in the room, damage,
no route, scroll" applies to the reasons met by a step. A rewind that happened since the previous step is
detected **first**, at the start of `paso()`, before the next step is taken, and takes precedence. So `paso()`
does, in this order:

1. If `Partida.retrocesos` differs from the value stored when the trip began, stop `RETROCESO` (FR-025).
   No step is taken.
2. If the game has ended, stop `FIN_PARTIDA`; if the player is in `destino`, stop `LLEGADA` (also when the
   trip begins there: no time is consumed).
3. Compute the route; if there is none, stop `SIN_RUTA` with no time consumed (FR-022).
4. Record the player's life and call `mover(direccion)`. **Guard (FR-028):** if `mover` returns `False`
   (the route named an exit but the move was refused, which the route search should make impossible because it
   only uses exits open in the player's room), stop `SIN_RUTA` instead of looping or retrying; the direction is
   not recorded and no time is consumed.
5. After a completed step, check in order: game ended (`FIN_PARTIDA`), player in `destino` (`LLEGADA`),
   alive enemies of `Partida.enemigos` in the player's room (`ENEMIGOS`, whoever arrived there, clarification
   2026-11-12), life lower than before (`DANO`); otherwise the trip goes on.

When several of the reasons of step 5 hold, the first in this order, which is the order of FR-022, is
reported (clarification 2026-11-12). The rewind of step 1 is not part of that comparison: it is detected
before any step (clarification 2026-11-17).

`JuegoService.ir_a(id_sala)` rejects an unexplored room, builds the `Viaje`, loops `paso()` until a
reason comes out and returns a `ViajeResultadoDTO(motivo, pasos, direcciones)`.
`Partida.retroceder` adds 1 to `Partida.retrocesos`, a plain attribute that is **not** written
through the history (a rewind of a rewind never exists).

### Controller, log and view

- `Controlador._cmd_ir_a`: `ir a <id>`. On rejection it writes `# ir a <id>` to the log and shows a
  message. On acceptance it writes the comment first, then runs the trip; for every step taken it
  records the direction as a move in the log and in the saved command list, so re-executing the list
  replays plain moves. The order itself is never stored in the saved command list (it would run the
  steps twice).
- `Controlador._cmd_mapa`: shows the known map. It changes no state; like `inv` today it is recorded
  as an ordinary command line, and replay runs it harmlessly.
- `BitacoraPartida.comentar(texto)` writes `# texto`. `LectorBitacora.leer` skips lines starting with
  `#`. Old logs have no such lines, so the format version stays 1.
- `SalidaVistaDTO.nombre_destino` is `None` for a sighted destination; `VistaConsola.mostrar_estado`
  prints `sin explorar` instead of the name (contract [vista-sala-niebla.md](./contracts/vista-sala-niebla.md)).
- `MapaVistaDTO` and `VistaConsola.mostrar_mapa` ([comando-mapa.md](./contracts/comando-mapa.md)).

### Complexity (engine)

- Exploration on a move: O(deg) without torch, O(deg²) with torch, plus O(deg) door memory.
- One "ir a" step: O(V_k log V_k + E_k) over the known region closer to the destination than the
  player, plus O(deg) for the tie-break.
- Rollback: the history already restores each recorded write; the new writes add O(deg) or O(deg²)
  entries to the frame of a move.

## Measurements (Constitution VI, FR-026, FR-027)

Everything is deterministic by seed (`random.Random(seed)`), local, without network or rendering, and
imports nothing from `view/`.

**0. Baseline "before" (first implementation step, before any code edit)**: run on the current code
and save unchanged:

```powershell
python -m bench.bench_ciclo   > specs/003-fog-of-war/bench-antes-ciclo.txt
```

After the last change run the same command into `bench-despues-ciclo.txt`. All scenarios keep the p99
≤ 20 ms limit. The average per cycle is compared with the "before" file as an investigation trigger
(more than 10% slower, best of 3 runs), not as a gate, as in spec 002. The likely cause would be the
exploration and door memory work in `Partida.mover`.

**1. One step of "ir a" (FR-026, SC-007)** — new `bench/bench_ir_a.py`. Synthetic crypt of **300 rooms**
(the largest published crypt, cripta-06) with costs from the same set as `bench_cazador`,
all rooms explored and all doors remembered open, seeded; the player and the destination are drawn
per repetition from the seeded generator, far apart. It measures `RutaConocida.siguiente_paso` alone
(microseconds; 2000 repetitions for 100 and 300 rooms, 300 for 500 and 1000 rooms) and, for information, a whole step (route plus move plus event
cycle). Verdict: the 99th percentile of the route computation with 300 rooms is ≤ 5 ms; the maximum is
printed. Repeated for 100, 500 and 1000 rooms, as information. The first measurement with 300 rooms was above
the wanted margin, so the heap comparisons and the route loop were optimized; before and after numbers are in
`docs/DECISIONES.md` §5.4 and `specs/003-fog-of-war/bench-ir-a.txt`.

**2. Determinism (FR-027)**: the same seed gives the same crypt (a test compares two builds).

**3. No view**: `grep` over `bench/` for `view` imports and the replay test of the Constitution Check.

## Project Structure

### Documentation (this feature)

```text
specs/003-fog-of-war/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── comando-ir-a.md
│   ├── comando-mapa.md
│   ├── vista-sala-niebla.md
│   └── bitacora-comentarios.md
└── tasks.md
```

### Source Code (repository root)

```text
model/
├── sala_logica.py       # Sala.conocimiento, Salida.memoria and their constants
├── partida_logica.py    # conocidas, _subir/_explorar/_explorar_vecinas, _memorizar_puertas,
│                        #   puerta_recordada, retrocesos; hooks in mover and retroceder
├── ruta_conocida.py     # NEW: backwards search over the known map
└── viaje_logica.py      # NEW: trip and stop reasons
service/juego_service.py # ir_a, mapa_vista, estado_vista with fog
dto/
├── salida_vista (in estado_vista_dto.py)  # nombre_destino may be None
├── mapa_vista_dto.py    # NEW
└── viaje_dto.py         # NEW
controller/controlador.py # commands "ir a" and "mapa"
adapters/
├── bitacora_partida.py  # comentar
└── lector_bitacora.py   # skip comment lines
view/vista_consola.py    # sin explorar, mostrar_mapa, viaje messages
view/vista_silenciosa.py # no-op mostrar_mapa
structures/monticulo.py  # comparisons written inline (speed only; same behavior)
bench/bench_ir_a.py      # NEW
tests/
├── test_niebla_estados.py     test_niebla_puertas.py   test_niebla_antorcha.py
├── test_niebla_retroceso.py   test_ir_a_ruta.py        test_ir_a_viaje.py
├── test_ir_a_bitacora.py      test_vista_niebla.py     test_bench_ir_a.py
└── oracle for routes (in tests/mapas_*)
```

**Structure Decision**: Same five layers as parts one and two. Knowledge is stored on the crypt
objects the model already owns, written through the existing undo history. Two new model files hold
the route search and the trip; everything else is a small change to existing files.

## Points for the spec

Found while planning; the plan did not decide them (Constitution VIII). All five were settled in
`/speckit-clarify` on 2026-11-12 and are listed here for traceability.

1. **Order of stop reasons.** Resolved (clarification 2026-11-12): the first that applies in the order of FR-022.
2. **Stop by a scroll.** Resolved (clarification 2026-11-12): its own reason, `RETROCESO`. Corrected on 2026-11-17: it is last in the order of the reasons met by a step, but a rewind since the previous step is detected before the next step and takes precedence (FR-022).
3. **Refused move.** Resolved (clarification 2026-11-17): the trip stops with `SIN_RUTA` (FR-028).
4. **How the destination is named.** Resolved (clarification 2026-11-12): by id only, as shown in the known map.
5. **Verdict of FR-026.** Resolved (clarification 2026-11-12): 99th percentile of the route computation ≤ 5 ms, maximum printed; the whole step is reported for information only.

## Complexity Tracking

No constitution violation to justify.
