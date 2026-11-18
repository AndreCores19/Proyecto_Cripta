# Implementation Plan: Crypt Solvability Verification

**Branch**: `004-crypt-solvability` | **Date**: 2026-11-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-crypt-solvability/spec.md`

## Summary

Before a game starts, the program decides whether the crypt can be won and explains why if not.
The decision is **one pass over the skeleton** that grows the region the player can reach and the
set of keys the player holds at the same time: reaching a room makes the keys located there
*obtainable* (they go into a hand-written min-heap ordered by key id); after the region has grown
as far as it can with the keys already taken, the lowest-id obtainable key is taken, the closed exits
that were waiting for it are released, and the region grows again. Every room is entered once, every
exit is looked at once from its origin, every key goes in and out of the heap once, so the cost is
`O((V + E) log V + K log K)` (the `log V` is finding a room's position in the sorted room vector), never one
full pass per key; it is still near-linear and the benchmark shows it with operation counters. The order in which the keys leave the heap is
the order of keys (FR-009, FR-011) and does not depend on how the service lists the keys and the exits of each room (FR-010); the rooms are taken sorted by id, as in part one.

What the pass leaves behind answers the report of a non-solvable crypt (FR-012): the keys never taken
(a), the closed exits that were left waiting, which are exactly the blocked frontier (b), where each
of those keys is (c), and, with one linear sweep over only the rooms the pass did not reach, the guard
of each unobtainable key and the cycles among them (d).

Key locations come from a new service query (`/criptas/{id}/llaves`), counted in the request budget,
saved on disk with the crypt version it was obtained for and reused while the version is the same
(FR-004, FR-005). In `--offline` mode the recorded package gets a `llaves.json` per crypt (FR-006).
`--verificar <crypt>` runs the same service with no view; `--forzar` lets a non-solvable crypt start.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `requests` (unchanged); no new dependencies

**Storage**: One new small file per crypt, `cache/llaves/<id_cripta>.json`, holding the crypt version
and the key list. It is replaced when the version differs (Constitution V: invalidated by the version
check, never deleted by hand). The offline package gains `offline/<id_cripta>/llaves.json`.

**Testing**: pytest (`tests/`), one test per acceptance scenario, each citing its FR. An independent
oracle (full pass per key, plain lists) checks every verdict, order and report on seeded random crypts
and on shuffled listings. All tests use fake clients and fake data built in the test; **no network**.

**Target Platform**: Desktop console (Windows/Linux), headless `--verificar` and `--bench`

**Project Type**: CLI game, five-layer architecture (data → logic → service → controller → view)

**Performance Goals**: FR-018: verification of the largest published crypt (cripta-06: 300 rooms, 4 keys,
6 skeleton pages) in at most 200 ms, locally, without network or rendering. FR-019: cost approximately
linear in rooms, exits and keys, shown with synthetic crypts of many chained keys against the naive
alternative (one full pass per key).

**Constraints**: Constitution I (no `dict`/`set`/`heapq`/`bisect`/`collections`, no graph library),
II (fixed tie-breaks), III (no view in `--verificar` or `--bench`), IV (nothing crypt-specific in code),
V (the key query counts in the budget; version check only), VI (benchmarks deterministic by seed),
VIII (this plan adds no rule; see "Points for the spec").

**Scale/Scope**: Published crypts today: 20, 40, 50, 24 and 300 rooms with 2 to 4 keys each, budgets
from 23 to 63 requests (cripta-06: 63). The benchmark also uses synthetic crypts of 300 to 100 000
rooms and 4 to 2 000 chained keys to show the trend.

## Constitution Check

*GATE: checked before Phase 0 and re-checked after Phase 1 — PASS.*

### Structures Gate

| Item | Status | Notes |
|---|---|---|
| No `dict`/`set` as index or cache in an evaluated structure | PASS | Per-room state is lists indexed by the room's position in the existing binary-search vector; keys are found with that same vector (ids sorted as text); per-room key lists are lists; the cache file is read once into a list of DTOs. |
| No `heapq`, `bisect`, `collections` | PASS | Reuses `structures/monticulo.py` (obtainable keys by id), `structures/cola.py` (rooms to visit) and `structures/ordenamientos.py` (report order). |
| No graph or pathfinding library | PASS | The pass is written by us in `model/solvabilidad_logica.py`. |
| Hand-written structures cover solvability | PASS | Heap, queue, binary-search vector, lists and integer arrays. |

### Architecture Gate

| Item | Status | Notes |
|---|---|---|
| `model/` and `structures/` import nothing from `view/` or `controller/` | PASS | The new model file imports only `structures/` and `model/sala_logica.py`. |
| `--verificar` and `--bench` create no view class | PASS | `--verificar` runs a function of `aplicacion.py` that builds only the data layer and the service and prints with plain functions (like `--replay`); `bench/bench_solvabilidad.py` builds rooms directly. A test makes every class in `view/` raise on construction and runs `--verificar`. |
| DTOs at every layer boundary | PASS | `LlaveUbicacionDTO` (data → service) and `ReporteVerificacionDTO` (service → view/adapters). The view never receives a `Sala`. |

### Process Gate

| Item | Status | Notes |
|---|---|---|
| `spec.md` committed before implementation | PENDING | Commit the spec and its clarifications before the first task (Constitution VII). |
| Every task cites its FR | PENDING | Enforced when `tasks.md` is generated. |
| Every scenario has a test citing its FR | PENDING | Mapping in [quickstart.md](./quickstart.md). |

### Principles

| Principle | Status | Notes |
|---|---|---|
| II. Determinism | PASS | The order of keys leaves a heap ordered by key id; reports are sorted with fixed keys; flood order is fixed (see R5). Nothing depends on the order of rooms, exits or keys in the service answers. A test shuffles every listing. |
| IV. No hardcoded data | PASS | No room id, key id or crypt id appears in code; key ids come from the skeleton and the key query. |
| V. Network budget | PASS | One request per crypt version (the key query); `--verificar` makes datos + skeleton pages + (at most) the key query, no content and no catalog. Cripta-06 needs 8 of its 63. |
| VI. Evidence-backed performance | PASS (pending data) | The 200 ms claim and the linear growth come only from `bench_solvabilidad` (§Measurements). |
| VIII. What goes where | PASS | Structures and algorithms stay here; rules stay in the spec. Gaps found while planning are listed in "Points for the spec" instead of being decided. |

## Design

### Where each requirement lands

| FR | Layer | Change |
|---|---|---|
| FR-001 | model | The pass reads the rooms as built from the skeleton (`Sala.salidas`, `Salida.cerrada`, `Salida.llave`) and the key list. Nothing of the player's knowledge (`Sala.conocimiento`) is read. |
| FR-002, FR-003 | data + adapters | `ClienteHttp.llaves(id)` calls `GET /criptas/{id}/llaves` through the same `_get` as every other request. The answer gives, per key, `id`, `sala` and, when an enemy carries it, `enemigo`; the room already is the enemy's initial room, so the pass needs nothing else (R1). |
| FR-004 | data + adapters | The call goes through `_get`, which counts the request and refuses past the budget. `--offline` counts nothing, as for every offline call. |
| FR-005 | data | `RepositorioLlaves.cargar` reads `cache/llaves/<id>.json`; if its stored version equals the crypt version it returns that, otherwise it queries and overwrites the file (R2). |
| FR-006 | adapters | `ClienteOffline.llaves(id)` reads `<id>/llaves.json`; `grabar_offline.py` records it for every crypt and, only when the crypt listing succeeded, was not empty and every crypt was recorded without error, removes the crypt folders the service does not list (R3). |
| FR-007, FR-008 | model | The pass of §The pass implements the assumptions; solvable is decided by the last step (exit key taken and an exit door of that key leading to the exit room). |
| FR-009, FR-010, FR-011 | model | Order = order in which keys leave the heap; heap key = key id as text (R4). |
| FR-012 | model | (a)–(c) fall out of the pass; (d) is the guard sweep (R5). |
| FR-013 | model | One pass, plus one sweep over the rooms the pass did not reach. Never a pass per key (R5). |
| FR-014, FR-015, FR-016 | `aplicacion.py` + view | `Aplicacion.jugar` verifies first, shows verdict and order (or the report), and returns without starting the game when not solvable and not `--forzar`. |
| FR-017 | `main.py` + adapters | `--verificar <crypt>` calls `verificar_cripta` (no view, no catalog) and prints with `adapters/salida_verificacion.py`. |
| FR-022 | `aplicacion.py` | A communication error from the key query (or an exhausted budget) is caught where `jugar` and `verificar_cripta` call the service: the error is shown, there is no verdict, `jugar` ends unless `forzar` is true (then the game starts without a verdict), `verificar_cripta` ends with status 1. |
| FR-018, FR-019, FR-020, FR-021 | bench | New `bench/bench_solvabilidad.py` (§Measurements). |

### The pass (`model/solvabilidad_logica.py`, class `Verificador`)

Inputs: the rooms (the binary-search vector of `RepositorioCripta`), the initial room id, the exit room
id, the exit key id and the key list. State, all plain lists indexed by room position or key position:
`alcanzada[pos]` (bool), `llaves_en[pos]` (keys located there), and per key `obtenida`, `pendientes`
(the closed exits waiting for it) and `visita`. Keys are kept in a vector sorted by id (the existing
binary-search vector, which only needs `<` and `==`) so a door's key id is found in `O(log K)`.

1. Mark the initial room reached and enqueue it.
2. **Grow** while the queue is not empty: take a room; for every key located there, insert it in the
   heap with its id as priority; for every exit whose destination is not reached: if the exit is open,
   or its key is already taken, reach and enqueue the destination; otherwise append the exit to the
   `pendientes` of its key (a closed exit whose key id is not in the key list, or with no key, goes to a
   separate list of *exits nobody can open*; a key id named by such an exit, or the exit key, that the key list
   does not give gets a never-obtainable entry with no room, so that the report can list it with location
   unknown, FR-012).
3. If the heap is empty, stop. Otherwise take the **lowest-id key**, mark it taken, append its id to the
   order, release its `pendientes` (reach and enqueue each destination not yet reached) and go to 2.
4. **Decide**: solvable iff the exit key was taken and some exit that requires it leads to the exit room
   from a reached room (FR-008).

Why "the lowest id obtainable at that moment" is FR-011: a key is in the heap exactly while it is
obtainable and not yet taken, and the region has been grown as far as the keys taken allow before the next
one is taken, so "at the same moment" means "in the heap together". Every key leaves after the keys that
open the doors on its way, which is FR-009.

Cost: each room is enqueued once; each exit is examined from its origin once and, if it waited, released
once; each destination room is found in the sorted room vector (`O(log V)`, the cost of a binary search) and each
closed exit costs one `O(log K)` search of its key; each key is inserted and extracted once (`O(K log K)`).
Total `O((V + E) log V + K log K)`: still near-linear (the `log V` of a binary search, no pass per key). The
benchmark shows the near-linear growth with operation counters (rooms entered and exits examined stay at most
`V` and `E` however many keys there are) and with the time ratios.

### What the pass leaves, and the report (FR-012)

After step 3 stops:

- **(a)** the keys that were never taken, sorted by id.
- **(b)** the exits still waiting in the `pendientes` of those keys. An exit is in a `pendientes` list only
  if its origin was reached and its destination was not, so these are exactly the closed doors adjacent to
  the reached region. Sorted by `(room id of the origin, direction)` with `ordenar`.
- **(c)** the location of each key of (a), already in the key records.
- **(d)** *Guard sweep*, one linear sweep over the rooms not reached: take the keys of the frontier doors in
  increasing id order; for each, flood from the destinations of its doors (doors in increasing
  `(origin id, direction)` order) over exits of rooms not reached **ignoring locks**, labelling every room not
  yet labelled with that key and with the door the flood came through. A room already labelled is not entered
  again: whatever lies behind it is reachable from the lower key as well, so every room ends with the *lowest*
  frontier key that reaches it. The **guard** of an unobtainable key is the label of its room. Following guards
  gives a graph in which every key has at most one outgoing edge, so a walk from each key in increasing id
  order, marking keys with the starting key id, finds every cycle once (each key is in at most one). A cycle is
  reported as the list of its keys starting at the lowest id, each with its room, the guard key and the
  frontier door of that link. A key with no label (its room cannot be reached even ignoring locks) has no
  guard and is in no cycle. The doors of the exits nobody can open (no key, or a key the list does not give)
  start no flood, so the rooms behind them have no guard either. When several frontier keys reach the same
  region the lowest key id is the reported guard: that is what FR-012 (d) says. Cost `O(V_U + E_U + K)`
  where `U` is the part of the crypt the pass left.

All of it is read from the one pass and one sweep; there is no pass per key (FR-013). The exit-key-behind-its-own-door
case of the spec (scenario US3-1) is the cycle of length one.

### Data and layers

- `data/repositorio_llaves.py` — `RepositorioLlaves(fuente, almacen)`: `cargar(id_cripta, version)` →
  list of `LlaveUbicacionDTO`. Uses `adapters/almacen_llaves.py` (`leer(id)` → `(version, llaves)` or
  `None`, `guardar(id, version, llaves)`).
- `service/verificacion_service.py` — `VerificacionService(repo_cripta, repo_llaves)`: `verificar()` builds
  the model input from `repo_cripta.salas` and the DTOs, runs the `Verificador`, and returns a
  `ReporteVerificacionDTO`.
- `adapters/salida_verificacion.py` — `lineas_reporte(reporte)` (a list of lines) and
  `imprimir_reporte_verificacion(reporte)`; no import of `model/` or `view/`. `VistaConsola.mostrar_verificacion`
  prints the same lines, so the game and `--verificar` show the same text (contract
  [reporte-verificacion.md](./contracts/reporte-verificacion.md)).
- `aplicacion.py` — `Aplicacion.jugar(ruta_carga, forzar)` verifies before asking for the name and before any
  session, **with `self.repo_cripta` and `self.cliente`**: the skeleton that `Aplicacion.__init__` already
  downloaded is reused (no second download) and the key query goes through the same client, so it shares the
  request counter and the budget (FR-004). `verificar_cripta(url, id_cripta, cliente)` builds only the crypt
  repository (one skeleton download), the key repository and the service (no catalog, no view).
- `main.py` — options `--verificar CRIPTA` and `--forzar`; `--bench` runs `bench_solvabilidad`.

### Complexity (engine)

- Verification: `O((V + E) log V + K log K)` time, `O(V + E + K)` space.
- Report: the guard sweep adds `O(V_U + E_U)`; sorting the frontier and the lists adds `O(F log F + K log K)`.
- Cache: one file read per run (`O(K)`), one request per crypt version.

## Measurements (Constitution VI, FR-018 to FR-021)

Everything is deterministic by seed (`random.Random(seed)`), local, without network or rendering, and
imports nothing from `view/`.

**1. Largest published crypt (FR-018, SC-005)** — new `bench/bench_solvabilidad.py`. Synthetic crypt shaped
like cripta-06 (300 rooms, 4 keys: three chained doors and an exit key, seeded), built directly as rooms.
It measures `Verificador.verificar` alone in microseconds over repeated runs and prints average, 99th
percentile and maximum. Verdict: **maximum of the runs ≤ 200 ms** (FR-018 says "at most 200 ms", with no
percentile). It is also run on an unsolvable variant, so the report cost (the guard sweep) is inside the
measurement.

**2. Linear growth against the naive alternative (FR-019, FR-021, SC-006)** — synthetic crypts of
chained keys: key `i` is in the region that key `i-1` opens, so obtaining a key opens a new region.
Sizes: 100, 1 000, 10 000 and 100 000 rooms with one key per 50 rooms (2, 20, 200 and 2 000 keys). The
verification is measured at every size; the naive alternative (the same crypt, one full reachability pass from
scratch after every key taken; same order of keys, checked equal) only up to **10 000 rooms and 200 keys**: at
100 000 rooms and 2 000 keys it would need about 2×10⁸ room visits, many minutes in Python. The whole benchmark
must finish in about a minute. It prints both
times (the naive one where it is measured) and the ratios between consecutive sizes. Evidence of near-linear
growth: when the size grows by a factor `f`, the verification time grows by about `f` (a little more, from the
`log V`) and the naive time by about `f²`, and the operation counters stay within `V` and `E`.

**3. Determinism (FR-020)**: the same seed gives the same crypt (a test compares two builds).

**4. No view**: `grep` over `bench/` for `view` imports and the test that makes every `view/` class raise.

## Project Structure

### Documentation (this feature)

```text
specs/004-crypt-solvability/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── consulta-llaves.md
│   ├── cache-llaves.md
│   ├── paquete-offline-llaves.md
│   ├── reporte-verificacion.md
│   └── comandos-verificar-forzar.md
└── tasks.md
```

### Source Code (repository root)

```text
model/
└── solvabilidad_logica.py   # NEW: Verificador, ResultadoVerificacion, LlaveLogica
service/
└── verificacion_service.py  # NEW
dto/
├── llave_dto.py             # NEW: LlaveUbicacionDTO
└── reporte_verificacion_dto.py  # NEW
data/
└── repositorio_llaves.py    # NEW
adapters/
├── cliente_http.py          # llaves(id)
├── cliente_offline.py       # llaves(id)
├── almacen_llaves.py        # NEW
└── salida_verificacion.py   # NEW
aplicacion.py                # jugar(..., forzar), verificar_cripta
main.py                      # --verificar, --forzar, bench_solvabilidad
grabar_offline.py            # records llaves.json
view/vista_consola.py        # mostrar_verificacion
view/vista_silenciosa.py     # no-op mostrar_verificacion
bench/bench_solvabilidad.py  # NEW
tests/
├── mapas_solvabilidad.py        # builders and independent oracle (not a test module)
├── test_solvabilidad_orden.py   test_solvabilidad_informe.py
├── test_solvabilidad_llaves.py  test_solvabilidad_comandos.py
└── test_bench_solvabilidad.py
```

**Structure Decision**: Same five layers as parts one to three. The verification is a pure model function
over the rooms the data layer already builds; the key list is a new, small data-layer concern with its own
file store; everything else is a small change to existing files.

## Points for the spec

Found while planning; the plan did not decide them (Constitution VIII). All ten points were settled in
`/speckit-clarify` on 2026-11-17 (two rounds); none is provisional any more.

1. **A closed exit whose key is not in the key list, or that names no key.** Resolved (clarification
   2026-11-17): it can never be opened; it is reported in the blocked frontier with the key it names (or none),
   and the missing key as unobtainable with location unknown (FR-012).
2. **The exit key is not in the key list.** Resolved (same clarification): not solvable; the exit key is
   reported as unobtainable with location unknown (FR-012).
3. **Several cycles.** Resolved (clarification 2026-11-17): every cycle is reported, each starting at its
   lowest key id, sorted by that id (FR-012). Where several frontier keys reach the same locked room, the guard
   is the lowest key id (R5), a fixed tie-break (Constitution II); FR-012 (d) was reworded on 2026-11-17 to say
   exactly this.
4. **Which keys the order lists.** Resolved (clarification 2026-11-17): every key the player can obtain
   (FR-009).
5. **"The same pass."** Resolved (clarification 2026-11-17): the pass plus one linear sweep over only the
   rooms it did not reach, never a pass per key (FR-013).
6. **Games that are not started from the menu or the command line.** Resolved (clarification 2026-11-17,
   second round): `--replay` and loading a saved game do not verify again (FR-014).
7. **The key query fails or the budget is spent.** Resolved (clarification 2026-11-17): the usual
   communication error, no verdict, the game does not start unless `--forzar` is given (FR-022).
8. **The offline package.** Resolved (clarification 2026-11-17, second round): the package holds only the
   crypts the service serves, each with its recorded `llaves.json`; `cripta-01`, which the service does not
   serve, is removed (FR-006). Consequence for the work: `grabar_offline.py` rewrites the package from the
   service, and the manual-test scripts in `pruebas_manuales/` that name `cripta-01` need another crypt id.
9. **A key id listed twice by the key query.** Resolved (second round): only the entry with the lowest room id
   counts (FR-002).
10. **Exit status of `--verificar`.** Resolved (second round): 0 when solvable, 1 when not solvable or on a
    communication error (FR-017).

## Complexity Tracking

No constitution violation to justify.
