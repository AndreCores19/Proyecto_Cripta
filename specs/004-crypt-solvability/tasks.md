---

description: "Task list for Crypt Solvability Verification"
---

# Tasks: Crypt Solvability Verification

**Input**: Design documents from `specs/004-crypt-solvability/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (consulta-llaves, cache-llaves, paquete-offline-llaves, reporte-verificacion, comandos-verificar-forzar), quickstart.md

**Tests**: Required. Constitution IX says every acceptance scenario needs an automated test that cites its FR, and every task cites at least one FR. All tests use fake data built in the test (hand-built rooms, fake clients) and **no network**.

## Format: `[ID] [P?] [Story] Description — FR`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: user story from spec.md (US1–US8); phases without a story are shared groundwork
- Every test function's docstring MUST cite its FR and scenario, e.g. `"""FR-010, FR-011 · US2-2"""`.
- Within a phase, write the tests first and run them: they must fail for the right reason before the implementation task, and pass after it.
- Phases follow dependency order, not story number: the pass itself (US2 order, US4 enemy keys, US3 report), then the key query and its storage (US7, needed by the flow), then the start flow (US1), then `--forzar` (US5), `--verificar` (US6) and the benchmark (US8).

## Path Conventions

Single-project layered layout at the repo root: `dto/`, `data/`, `model/`, `service/`, `controller/`, `view/`, `adapters/`, `structures/`, `bench/`, `tests/`. `aplicacion.py` and `main.py` are at the root.

## Test files

| File | Covers |
|---|---|
| `tests/mapas_solvabilidad.py` (new helper, not a test module) | crypt builders, key lists, listing shuffles, independent oracle (a full pass per key) |
| `tests/test_solvabilidad_orden.py` (new) | oracle self-checks, US2-1..3 |
| `tests/test_solvabilidad_informe.py` (new) | US3-1..4, US4-1, US4-2 |
| `tests/test_solvabilidad_llaves.py` (new) | US7: key query, saved file, offline package, recording |
| `tests/test_solvabilidad_comandos.py` (new) | US1, US5, US6: service, report text, start flow, `--forzar`, `--verificar` |
| `tests/test_bench_solvabilidad.py` (new) | US8 |

## Common fixtures

**Rooms**: `Sala` and `Salida` built by hand (`model/sala_logica.py`). A door is two `Salida` faces joined with `enlazar`, both closed (`cerrada=True`) and with the same `llave`. The verification takes the rooms as a binary-search vector (`VectorBusqueda` in `structures/vector_busqueda.py`, ids in increasing order, as `RepositorioCripta.construir_salas` builds it): `armar_vector(salas)` in `tests/mapas_solvabilidad.py` does it.

**Keys**: `LlaveLogica(id, id_sala, id_enemigo)` for the model; `LlaveUbicacionDTO(id_llave, id_sala, id_enemigo)` for the data layer. A key lying in a room has `id_enemigo = None`.

**Fake client**: a class with the methods the data layer calls (`datos_cripta`, `pagina_esqueleto`, `llaves`, …), counting its requests and raising `ErrorCliente` past its budget, like `ClienteHttp`. No test imports `requests` for real.

**`tests/mapas_solvabilidad.py`** (created in T004; imports only from `model/`, `dto/`, `structures/`):
- `armar_vector(salas)` → binary-search vector of rooms; `cripta(n, puertas)` → `n` rooms (ids 1..n) joined by the given `(a, b, costo, llave)` pairs (`llave=None` is an open door).
- `cadena_de_llaves(k)` → crypt where key `i` lies in the region that key `i-1` opens, with the exit behind key `k`.
- `cripta_aleatoria_con_llaves(semilla, n_salas, n_llaves)` → seeded crypt with random closed doors and key locations (rooms and enemy-carried keys).
- `barajar(salas, llaves, semilla)` → the same crypt with the exits of every room and the key list in another order.
- `resolver_referencia(salas, id_inicial, id_salida, id_llave_salida, llaves)` → the **oracle**: plain lists and a full reachability pass from scratch after every key taken, always taking the lowest-id key obtainable; returns `resoluble`, `orden` (key ids), `inalcanzables` (ids), `frontera` (`(id_origen, direccion, id_destino, id_llave)` sorted), and `ciclos` with the same rules as plan §What the pass leaves (guard = lowest frontier key id that reaches the room ignoring locks, found with one flood per frontier key). No heap, no vector, no counters.

## Phase 1: Baseline before any code change

**Purpose**: fix the reference. Nothing in this phase edits code.

- [X] T001 Check that `specs/004-crypt-solvability/spec.md` is committed (commit `326fc76`) and that `git status` shows no change under `model/`, `structures/`, `data/`, `service/`, `dto/`, `view/`, `controller/`, `adapters/`, `bench/`, `aplicacion.py`, `main.py` or `grabar_offline.py` (Constitution VII) — all FRs
- [X] T002 Run `python -m pytest` on the unchanged code and note the result (count and time). It is the "all green before" reference for Phase 11 — all FRs

**Checkpoint**: baseline noted and nothing else changed.

---

## Phase 2: Foundational — DTOs and shared test helper

**Purpose**: the data shapes and the oracle every story uses. Blocks every story.

- [X] T003 [P] Create `dto/llave_dto.py` with `LlaveUbicacionDTO(id_llave, id_sala, id_enemigo)` and `desde_json(datos)` reading `datos["id"]`, `datos["sala"]` and `datos.get("enemigo")` (`enemigo` is absent for a key lying in a room, so `id_enemigo` is `None`); and `dto/reporte_verificacion_dto.py` with `UbicacionLlaveDTO(id_llave, id_sala, id_enemigo)` (`id_sala` is `None` if the key is not in the key list), `PuertaFronteraDTO(id_sala, id_destino, direccion, id_llave)` (`id_llave` is `None` if the exit names no key), `EslabonCicloDTO(id_llave, id_sala, id_llave_guardia, puerta)` (`puerta` is a `PuertaFronteraDTO`) and `ReporteVerificacionDTO(id_cripta, resoluble, orden, llaves_inalcanzables, puertas_frontera, ciclos, solicitudes)`. When the crypt is solvable, `llaves_inalcanzables`, `puertas_frontera` and `ciclos` are empty lists. Plain values and lists only; no import of `model/` — FR-002, FR-003, FR-012
- [X] T004 Write `tests/mapas_solvabilidad.py` as described in "Common fixtures" (`armar_vector`, `cripta`, `cadena_de_llaves`, `cripta_aleatoria_con_llaves`, `barajar`, `resolver_referencia`) — FR-008, FR-009, FR-010, FR-011, FR-012
- [X] T005 Add a first self-check in `tests/test_solvabilidad_orden.py`: the oracle gives `orden == ["k1", "k2"]` for a three-room chain where door 1 opens with `k1` (lying in room 1) and door 2 with `k2` (lying in room 2), exit behind door 2; and `resoluble == False` with `inalcanzables == ["k"]` and one frontier door when the exit key lies behind the only door that opens with it. Docstrings `FR-008, FR-012` — FR-008, FR-009, FR-012

**Checkpoint**: DTOs exist, the oracle is written and checks itself.

---

## Phase 3: User Story 2 — A solvable crypt gives a valid and repeatable order of keys (Priority: P1)

**Goal**: the pass: reach rooms, take keys lowest id first, decide solvable. This phase builds the core of `Verificador`.

**Independent Test**: build a crypt of chained keys, verify it, check the order against every dependency and against the oracle; verify it again with exits and keys listed in another order.

- [X] T006 [P] [US2] In `tests/test_solvabilidad_orden.py` add: US2-1 (a solvable crypt with chained keys: every key appears after all the keys needed to reach it, and the order equals the oracle's), US2-2 (a crypt with several keys obtainable at the same moment: the lowest id comes first, and two runs give the same order), US2-3 (`barajar` the exits of every room and the key list: same order), the assumptions of FR-007 (a closed door with the key already taken is crossed; a door that has `cierre_automatico` and a room with a trap are crossed as if open; a key is never consumed: two doors that open with the same key both open), a key lying in a room that is only reachable through an exit with no door, the exit key obtainable but no exit of the exit room requires it (not solvable, FR-008), the same key id listed twice with different rooms (only the entry with the lowest room id counts, FR-002), and a randomized check: 200 seeded crypts from `cripta_aleatoria_con_llaves`, `Verificador` equals `resolver_referencia` in `resoluble` and `orden`. Docstrings `FR-009, FR-010, FR-011 · US2-1`, etc. — FR-002, FR-007, FR-008, FR-009, FR-010, FR-011
- [X] T007 [US2] Create `model/solvabilidad_logica.py` with `LlaveLogica(id, id_sala, id_enemigo)` (plus `obtenida`, `pendientes` (list of `Salida`) and `visita`, as in data-model.md), `ResultadoVerificacion` and `Verificador.verificar(salas, id_inicial, id_salida, id_llave_salida, llaves)` implementing plan §The pass: sort the key list by `(id, id_sala)` with `ordenar` (`structures/ordenamientos.py`) and drop later entries with the same id (FR-002); put the keys in a `VectorBusqueda` by id; lists indexed by room position (`salas.posicion(id)`) for `alcanzada` and `llaves_en`; a `Cola` of rooms to visit; a `MonticuloMinimo` of obtainable keys with the key id as priority; grow, take the lowest-id key, release its `pendientes`, repeat; then decide solvable (exit key taken and some exit that requires it leads to the exit room from a reached room). A closed exit whose key id is not in the key list, or that names no key, goes to a separate list `sin_abrir` and is never crossed; for each key id named by such an exit, and for the exit key, that the key list does not give, create a never-obtainable `LlaveLogica` with `id_sala` `None` (it never enters the heap), so that the report can list it as unobtainable with location unknown (FR-012). The cost is `O((V + E) log V + K log K)`: finding a room's position in the sorted room vector is a binary search, `O(log V)`; it is still near-linear and `visitas_salas` and `examenes_salidas` show it. Count `visitas_salas` and `examenes_salidas` in plain integer attributes (used in T011). Imports only `structures/` and `model/sala_logica.py`; no `dict`, `set`, `heapq`, `bisect`, `collections`; never reads `Sala.conocimiento` or `Salida.memoria`. Depends on T004, T006 — FR-001, FR-002, FR-007, FR-008, FR-009, FR-010, FR-011, FR-013, FR-019
- [X] T008 [US2] Run `python -m pytest tests/test_solvabilidad_orden.py -v` and the whole suite; all green. Check `model/solvabilidad_logica.py` with `grep -nE "heapq|bisect|collections|networkx|\bdict\(|\bset\(|\bfrozenset\(|\{\}|\{[^}]*:[^}]*\}"` (review each hit by hand: f-strings are not indexes) and that it imports nothing from `view/`, `controller/`, `service/` or `dto/` — FR-009, FR-019

**Checkpoint**: the verdict and the order work. Review before Phase 4.

---

## Phase 4: User Story 4 — Keys carried by enemies are placed where the enemy starts (Priority: P1)

**Goal**: a key dropped by an enemy is obtainable in the room where that enemy starts, wherever the enemy wanders.

**Independent Test**: a crypt where the key is in what a wandering enemy drops.

- [ ] T009 [P] [US4] In `tests/test_solvabilidad_informe.py` add: US4-1 (a key with `id_enemigo` set and `id_sala` the enemy's initial room: the verification places it in that room, so the key is obtainable as soon as that room is reached and the order and verdict equal the oracle's), `LlaveUbicacionDTO.desde_json({"id": ..., "sala": ..., "enemigo": ...})` keeps the enemy id and `desde_json` without `enemigo` gives `id_enemigo` `None`. The key's location is never moved by the enemy's behavior (no enemy is simulated). Docstrings `FR-003 · US4-1` — FR-002, FR-003
- [ ] T010 [US4] Run `python -m pytest tests/test_solvabilidad_informe.py -v`. If a test fails, the cause is the verification using `id_enemigo` for something other than the report: fix it in `model/solvabilidad_logica.py` — FR-003. Then run the whole suite

**Checkpoint**: enemy keys are placed. US4-2 is added in Phase 5, where the report exists.

---

## Phase 5: User Story 3 — A non-solvable crypt is explained exactly (Priority: P1)

**Goal**: what the pass leaves, and the guard sweep: unobtainable keys, frontier doors, locations, cycles.

**Independent Test**: a non-solvable crypt with a known frontier and a known cycle; two runs give the same report.

- [ ] T011 [P] [US3] In `tests/test_solvabilidad_informe.py` add: US3-1 (the exit key behind the only door that it opens: not solvable, one cycle of length one, scenario 1 of the brief), US3-2 (the report lists exactly the unobtainable keys sorted by id, the closed exits from reached rooms to rooms not reached sorted by `(id of origin, direction)` each with its key, and the location of each key), US3-3 (three keys that guard each other in a ring: the concrete cycle, starting at its lowest key id, the same in two runs and after `barajar`), several independent cycles (all reported, each starting at its lowest key id, sorted by that id, FR-012), a room reached by the flood of two frontier keys (the guard is the lowest key id), a key whose room is not connected at all (it has no guard and is in no cycle), a closed door that names a key missing from the key list or names no key (it is in the frontier with `id_llave` `None` or the missing key, and the missing key is unobtainable with `id_sala` `None`), the exit key missing from the key list, US4-2 (a key carried by an enemy whose initial room is not reachable: not obtainable and reported with its room and its enemy), US3-4 (count `visitas_salas` and `examenes_salidas` on `cadena_de_llaves(k)` for k = 10, 100 and 1000: both stay at most the number of rooms and of exits, and do not grow with k beyond them, so there is no pass per key), and a randomized check: 200 seeded crypts, every list of the report equals `resolver_referencia`'s. Docstrings `FR-012, FR-013 · US3-2`, etc. — FR-003, FR-010, FR-012, FR-013
- [ ] T012 [US3] In `model/solvabilidad_logica.py` extend `Verificador` to fill `ResultadoVerificacion` as in plan §What the pass leaves: `inalcanzables` (keys never taken, sorted by id), `frontera` (the exits still in the `pendientes` of those keys plus those in `sin_abrir`, sorted by `(id of origin, direction)` with `ordenar`) and `ciclos`, from one linear sweep over the rooms the pass did not reach: take the keys of the frontier doors in increasing id order, flood from the destinations of their doors (doors in increasing `(origin id, direction)` order) over the exits of rooms not reached ignoring locks, labelling each room not yet labelled with that key and that door (a labelled room is never entered again); the doors of the exits in `sin_abrir` (no key, or a key the list does not give) start no flood, so the rooms behind them have no guard; the guard of an unobtainable key is the label of its room (when several frontier keys reach the same region the lowest key id is the reported guard, FR-012 d); follow guards from each key in increasing id order marking keys with the starting key id to find every cycle once; a cycle is the list of its keys starting at the lowest id, each with its room, its guard key and the frontier door. No pass per key. Depends on T007, T011 — FR-003, FR-010, FR-012, FR-013
- [ ] T013 [US3] Run `python -m pytest tests/test_solvabilidad_orden.py tests/test_solvabilidad_informe.py -v` and the whole suite; all green. Repeat the `grep` of T008 on `model/solvabilidad_logica.py` — FR-012, FR-013

**Checkpoint**: the model decides and explains. Review before the data and flow phases.

---

## Phase 6: User Story 7 — Key locations come from the service within the budget (Priority: P2)

**Goal**: the key query, its counting, the saved file by version, and the offline package.

**Independent Test**: a fake client and a temporary folder: the request count, a new version, a saved answer, and `--offline` reading `llaves.json`.

- [ ] T014 [P] [US7] Write `tests/test_solvabilidad_llaves.py`: US7-1 (`ClienteHttp.llaves(id)` with `requests.get` replaced by a fake counts one request, asks `GET /criptas/{id}/llaves` with the client id header, returns the JSON, and raises `ErrorCliente` past the budget, FR-004), US7-2 (`RepositorioLlaves.cargar(id, version)` with another version than the saved file: the fake client is asked again and the file now holds the new version, and the old file is not deleted by the code before the answer arrives), US7-3 (same version: the saved list is used and the fake client makes no request), a damaged or incomplete file is treated as missing, the file holds `{"version": ..., "llaves": [...]}` with `enemigo` absent for a key lying in a room, `ClienteOffline.llaves(id)` reads `<id>/llaves.json` and counts no request and raises `ErrorOffline` if the file is missing, `grabar_offline.grabar()` with a fake `ClienteHttp` writes `llaves.json` for each crypt the fake lists and removes from the package folder any crypt folder that the fake does not list, **only** when the listing succeeded, was not empty and every crypt was recorded without error; with an empty listing nothing is removed, and with a recording that fails halfway (the fake raises on the second crypt) nothing is removed either (FR-006). Docstrings `FR-004, FR-005 · US7-1`, etc. — FR-002, FR-004, FR-005, FR-006
- [ ] T015 [US7] Add `llaves(self, id_cripta)` to `adapters/cliente_http.py` (`return self._get(f"/criptas/{id_cripta}/llaves", operacion=f"obtener llaves de {id_cripta}")`) and to `adapters/cliente_offline.py` (`return self._leer(id_cripta, "llaves.json")`). Depends on T014 — FR-002, FR-004, FR-006
- [ ] T016 [US7] Create `adapters/almacen_llaves.py` (`AlmacenLlaves(carpeta)`: `leer(id_cripta)` → `(version, llaves)` or `None`, a damaged or incomplete file is `None`; `guardar(id_cripta, version, llaves)`; file `<carpeta>/<id_cripta>.json`, as in [cache-llaves.md](./contracts/cache-llaves.md); the id is validated like `AlmacenFichas._ruta`) and `data/repositorio_llaves.py` (`RepositorioLlaves(fuente, almacen)`: `cargar(id_cripta, version)` returns a list of `LlaveUbicacionDTO`: the saved list if the stored version equals `version`, otherwise one query, then `guardar`). Neither imports `model/` or `view/`. Depends on T003, T014, T015 — FR-002, FR-004, FR-005
- [ ] T017 [US7] In `grabar_offline.py` record `llaves.json` for each crypt (`guardar(f"{CARPETA}/{id_cripta}/llaves.json", cliente.llaves(id_cripta))`, on that crypt's own client) and, after recording, remove from `CARPETA` every crypt folder that the service did not list (FR-006: the package holds only crypts the service serves). **Delete only if** the crypt listing succeeded and was not empty and every listed crypt was recorded without error: an empty listing, an exception while listing, or an exception while recording any crypt leaves the package as it is. The removal touches only direct subfolders of `CARPETA` whose name is not in the served list. Depends on T014, T015 — FR-006
- [ ] T018 [US7] Run `python -m pytest tests/test_solvabilidad_llaves.py -v` and the whole suite; all green — FR-004, FR-005, FR-006

**Checkpoint**: key locations can be loaded, counted, saved and read offline. Review before Phase 7.

---

## Phase 7: User Story 1 — The player is told before playing whether the crypt can be won (Priority: P1)

**Goal**: the service, the report text and the start flow: solvable starts, non-solvable stops and shows the report.

**Independent Test**: a solvable and a non-solvable fake crypt; start a game on each; check that the first starts and the second does not and shows the report.

- [ ] T019 [P] [US1] Write `tests/test_solvabilidad_comandos.py` (part start flow): `VerificacionService(repo_cripta, repo_llaves).verificar()` returns a `ReporteVerificacionDTO` (the service converts `LlaveUbicacionDTO` into `LlaveLogica`, runs the verification and fills the DTO; `solicitudes` is the requests the verification made), `lineas_reporte(reporte)` gives exactly the texts of [reporte-verificacion.md](./contracts/reporte-verificacion.md) for a solvable and a non-solvable report (sections only when they have entries, `(sin ubicación)` and `no tiene llave` as in the contract), `Aplicacion._verificar_antes_de_jugar(vista, forzar)` on a fake application: US1-1 (solvable: returns `True`, the verdict and the order of keys were shown), US1-2 (non-solvable without `forzar`: returns `False`, the report was shown, scenario 4 of the brief), US1-3 (the verdict does not change with the player's knowledge: verify before and after a game has explored rooms), FR-022 (the key query raises `ErrorCliente`: the error is shown, no verdict, returns `False`; with `forzar` it returns `True` without a verdict), the skeleton is downloaded once and shared (a fake client counts `pagina_esqueleto` calls: after `Aplicacion`'s own load and the verification before the game the count equals the number of skeleton pages, not twice that; and the key query goes through the same fake client, so its request counts in the same counter and the same budget, FR-004), `--replay` (`Aplicacion.reproducir`) and a `cargar` session (`Aplicacion._sesion` with a saved path) never call the verification (FR-014). Docstrings `FR-014, FR-015 · US1-2`, etc. — FR-001, FR-002, FR-008, FR-009, FR-012, FR-014, FR-015, FR-022
- [ ] T020 [US1] Create `service/verificacion_service.py` (`VerificacionService(repo_cripta, repo_llaves)`): `verificar()` works on the crypt repository it is given (the game path gives it `self.repo_cripta`, whose skeleton `Aplicacion.__init__` already downloaded: it never downloads the skeleton again) and reads `repo_cripta.datos` (initial room, exit room, exit key, version), asks `repo_llaves.cargar(id, version)`, converts the DTOs into `LlaveLogica`, runs `Verificador.verificar(repo_cripta.salas, ...)` and builds the `ReporteVerificacionDTO` (key lists sorted as the model returns them; `solicitudes` from the source's request counter before and after). Depends on T003, T012, T016, T019 — FR-001, FR-002, FR-009, FR-012, FR-014
- [ ] T021 [US1] Create `adapters/salida_verificacion.py` (`lineas_reporte(reporte)` → list of lines as in [reporte-verificacion.md](./contracts/reporte-verificacion.md); `imprimir_reporte_verificacion(reporte)` prints them; no import of `model/` or `view/`), add `VistaConsola.mostrar_verificacion(reporte)` (prints the same lines) in `view/vista_consola.py` and a no-op `VistaSilenciosa.mostrar_verificacion` in `view/vista_silenciosa.py`. Depends on T019 — FR-012, FR-014
- [ ] T022 [US1] In `aplicacion.py` add `Aplicacion._verificar_antes_de_jugar(vista, forzar)` → `True` if the game may start: it builds the `VerificacionService` **with `self.repo_cripta` and `self.cliente`** (the verification reuses the skeleton the game already downloaded, and the key query uses the same client as the game, so it shares the request counter and the budget, FR-004), runs it, shows the verdict and the order of keys, or the report, with `vista.mostrar_verificacion`; if not solvable and not `forzar` it returns `False`; a communication error (`ErrorCliente`, `ErrorOffline`) is shown with `vista.mostrar_mensaje`, gives no verdict and returns `forzar` (FR-022). Change `Aplicacion.jugar(self, ruta_carga=None, forzar=False)` to call it first, before `pedir_nombre`, and return without a game when it gives `False`. `_sesion` and `reproducir` do not call it (FR-014). Depends on T020, T021 — FR-014, FR-015, FR-016, FR-022
- [ ] T023 [US1] Run `python -m pytest tests/test_solvabilidad_comandos.py -v` and the whole suite; all green. Tests that build an `Aplicacion` or call `jugar` and now reach the verification: give their fake application a solvable verification or a fake `VerificacionService` the same way (list them in the commit message) — FR-014, FR-015

**Checkpoint**: the player is told before a game starts. Review before Phase 8.

---

## Phase 8: User Story 5 — The player can start anyway with `--forzar` (Priority: P2)

**Goal**: `--forzar` starts the game of a non-solvable crypt.

**Independent Test**: a non-solvable crypt with `--forzar`: the game starts.

- [ ] T024 [P] [US5] In `tests/test_solvabilidad_comandos.py` add: US5-1 (`_verificar_antes_de_jugar(vista, forzar=True)` on a non-solvable crypt: the report is shown and it returns `True`), `main()` accepts `--forzar` and passes it to `Aplicacion.jugar(ruta_carga, forzar=True)` (replace `main.Aplicacion` and `main.sys.argv` in the test; read `main.py` first), and without the option the call has `forzar=False`. Docstrings `FR-016 · US5-1` — FR-015, FR-016
- [ ] T025 [US5] In `main.py` add `parser.add_argument("--forzar", action="store_true", help="juega aunque la cripta no se pueda ganar")` and pass `forzar=args.forzar` in the call `Aplicacion(...).jugar(...)` for the two branches that play (named crypt and menu). `--replay` and `--bench` ignore it. Depends on T022, T024 — FR-016
- [ ] T026 [US5] Run `python -m pytest tests/test_solvabilidad_comandos.py -v` and the whole suite; all green — FR-016

**Checkpoint**: `--forzar` works.

---

## Phase 9: User Story 6 — The crypt can be verified without playing (Priority: P2)

**Goal**: `--verificar <crypt>` runs only the verification and prints the report, with no view.

**Independent Test**: run `--verificar` on a solvable and on a non-solvable fake crypt: the report is printed, no game, no view class.

- [ ] T027 [P] [US6] In `tests/test_solvabilidad_comandos.py` add: US6-1 (`verificar_cripta(url, id_cripta, cliente)` with a fake client prints the report with `imprimir_reporte_verificacion`, builds no catalog and no game: the fake client records that it was never asked for `contenido_salas`, `catalogo` or the catalog version, and the requests are datos, skeleton pages and at most one key query) and returns status 0 for a solvable crypt and 1 for a non-solvable one and 1 when a communication error ends the run (FR-017), US6-2 (every class defined in `view/` raises when constructed: the run still works and prints, as `tests/test_salida_replay.py` does), `main()` with `--verificar CRIPTA` calls `verificar_cripta` and exits with its status (replace `main.sys.exit` and `main.verificar_cripta`), and works with `--offline`. Docstrings `FR-017 · US6-1`, `FR-017 · US6-2` — FR-017, FR-022
- [ ] T028 [US6] In `aplicacion.py` add `verificar_cripta(url, id_cripta, cliente)`: it builds `RepositorioCripta` with the given `cliente` (loads data and skeleton once, `construir_salas`; the key query goes through the same `cliente`, so it shares the request counter and the budget, FR-004), `AlmacenLlaves("cache/llaves")`, `RepositorioLlaves` and the `VerificacionService`, runs it, prints with `adapters.salida_verificacion.imprimir_reporte_verificacion` and one line with the requests made and the budget, and returns 0 if solvable and 1 otherwise; a communication error is printed with the usual message and returns 1. It imports nothing from `view/` and builds no catalog. `Aplicacion._verificar_antes_de_jugar` uses the same `AlmacenLlaves` folder. Depends on T022, T027 — FR-017, FR-022
- [ ] T029 [US6] In `main.py` add `parser.add_argument("--verificar", metavar="CRIPTA", help="verifica si la cripta se puede ganar y termina")` and, before the branches that play, `sys.exit(verificar_cripta(URL, args.verificar, cliente))` with the client chosen by `--offline` as today. Depends on T028 — FR-017
- [ ] T030 [US6] Run `python -m pytest tests/test_solvabilidad_comandos.py -v` and the whole suite; all green — FR-017

**Checkpoint**: `--verificar` works with no view.

---

## Phase 10: User Story 8 — Verification is fast and grows linearly (Priority: P2)

**Goal**: at most 200 ms with a crypt of the size of the largest published one; linear growth shown against the naive alternative.

**Independent Test**: run `bench_solvabilidad` and read the verdict and the growth.

- [ ] T031 [P] [US8] Write `tests/test_bench_solvabilidad.py` (small configuration, like `tests/test_bench_ir_a.py`): US8-3 (the same seed builds the same crypt twice: compare `(id, direction, destination id, key)` of every exit and the key list), the report has average, 99th percentile and maximum of the verification, and the verdict line with the maximum against 200 ms (a maximum of exactly 200.0 ms is "cumple", 200.001 is "NO cumple", as in `tests/test_bench_ir_a.py`), the naive alternative gives the same order of keys as the verification on every measured crypt, `bench/bench_solvabilidad.py` contains no import of `view`, and running it leaves no `view` module loaded (`subprocess` with `-I`, as `tests/test_bench_ir_a.py`). Docstrings `FR-018 · US8-1`, `FR-019, FR-021 · US8-2`, `FR-020 · US8-3` — FR-018, FR-019, FR-020, FR-021
- [ ] T032 [US8] Create `bench/bench_solvabilidad.py`: a seeded builder of a crypt with the shape of cripta-06 (300 rooms, 4 keys: three chained doors and the exit key) and of chained-key crypts (key `i` in the region that key `i-1` opens; rooms 100, 1 000, 10 000 and 100 000 with one key per 50 rooms; the naive alternative only up to 10 000 rooms and 200 keys, since at 100 000 rooms and 2 000 keys it needs about 2×10⁸ room visits; the whole benchmark must finish in about a minute), built directly as rooms with `random.Random(semilla)` (reuse nothing from `view/`); `ejecutar(pequeno=False)` measures `Verificador.verificar` alone (microseconds, repeated runs), prints average, 99th percentile and maximum, the verdict `maximum <= 200 ms` for the 300-room crypt (also for a non-solvable variant, so the guard sweep is inside the measurement), and for each chained-key size the verification time, the naive alternative (one full reachability pass from scratch per key taken, same lowest-id rule, in this file) and the ratio between consecutive sizes; the naive and the verification must give the same order of keys. Register it in the `--bench` list of `main.py` next to `bench_ir_a`. Imports nothing from `view/`. Depends on T012, T031 — FR-018, FR-019, FR-020, FR-021
- [ ] T033 [US8] Run `python -m bench.bench_solvabilidad`, `python -m pytest tests/test_bench_solvabilidad.py -v`, and record the output in `specs/004-crypt-solvability/bench-solvabilidad.txt` (three runs separated by a line `--- corrida N ---`). The verdict with 300 rooms must be `<= 200 ms`, and when the size grows by a factor `f` the verification time must grow by about `f` (write the observed ratios down, and the time of the whole benchmark: about a minute). If a limit is not met, look for savings in the verification before anything else — FR-018 (SC-005), FR-019 (SC-006)

**Checkpoint**: performance evidence saved.

---

## Phase 11: Polish & cross-cutting

- [ ] T034 Constitution gate, limited to what this feature adds (`model/solvabilidad_logica.py`, `dto/llave_dto.py`, `dto/reporte_verificacion_dto.py`, `data/repositorio_llaves.py`, `adapters/almacen_llaves.py`, `adapters/salida_verificacion.py`, `service/verificacion_service.py`, `aplicacion.py`, `view/vista_consola.py`, `bench/bench_solvabilidad.py`) — FR-001, FR-013, FR-019, FR-020:
  - none uses `dict`, `set`, `heapq`, `bisect`, `collections`, `networkx` or another graph library in the evaluated part (`grep -nE "heapq|bisect|collections|networkx|\bdict\(|\bset\(|\bfrozenset\(|\{\}|\{[^}]*:[^}]*\}" <files>`, reviewing each hit by hand: f-strings and JSON reading are not indexes);
  - `model/` and `structures/` import nothing from `view/` or `controller/`;
  - `grep -rn "Vista" bench/` finds nothing, and the `--verificar` path builds no `view/` class (T027);
  - `grep -nE "itm_|cripta-|e-cripta" <the new source files>` finds nothing: no crypt, key or enemy id in code (Constitution IV);
  - `structures/monticulo.py`, `structures/cola.py`, `structures/vector_busqueda.py` and `structures/ordenamientos.py` are unchanged (`git diff --stat` empty);
  - the verification reads neither `Sala.conocimiento` nor `Salida.memoria` (`grep -n "conocimiento\|memoria" model/solvabilidad_logica.py` is empty).
- [ ] T035 [P] Update `README.md`: add `--verificar CRIPTA` and `--forzar` to the options table, a short paragraph on the verification (what it decides, the report, exit status, that the key query counts in the budget and is saved in `cache/llaves/`), `bench_solvabilidad` among the benchmarks, the new `tests/` files in section 4, the new folder in section 6 (`cache/llaves/`) and `llaves.json` in the offline package — FR-006, FR-014, FR-017
- [ ] T036 [P] Write the justification of the single pass in `docs/DECISIONES.md` (it exists since spec 003), under the heading `5.5 Verificación de resolubilidad: una pasada y no una por llave`: why the region and the keys grow together with a min-heap by key id instead of one reachability pass per key (research R4), why the report comes from what the pass leaves plus one sweep over the rooms it did not reach (R5), and the measured numbers from `bench-solvabilidad.txt`; link to `docs/Documento_de_Decisiones.pdf` and to `research.md` — FR-009, FR-013, FR-019
- [ ] T037 Record, in a note under this task, the mapping of the four cases that are the whole solvability section of assignment Appendix B to the scenario of `spec.md` and the test that covers each: (1) the exit key is behind the single door that it itself opens: not solvable and the report points out the cycle → US3-1, `tests/test_solvabilidad_informe.py` (T011); (2) a key is in the `suelta` field of a wandering enemy: the verification places it in the enemy's initial room → US4-1, `tests/test_solvabilidad_informe.py` (T009); (3) several valid orders: two executions give the same order → US2-2, `tests/test_solvabilidad_orden.py` (T006); (4) a non-solvable crypt without `--forzar`: the game does not start and the report is shown → US1-2, `tests/test_solvabilidad_comandos.py` (T019). Use the real test function names. If a case has no scenario or no test, stop and correct the spec in its own commit before the code that depends on it (Constitution IX) — all FRs
- [ ] T038 Run the whole suite, `python -m pytest`; all green. Compare the count with T002 plus the new tests — all FRs
- [ ] T039 Re-record the offline package so that it holds `llaves.json` and only the crypts the service serves: run `python grabar_offline.py` (**needs the network and removes `offline/cripta-01`**, which the service does not serve: ask the user before running it; each crypt uses its own client, so the budget of the game is not spent) — FR-006
- [ ] T040 Manual check from `quickstart.md` — FR-006, FR-014, FR-015, FR-016, FR-017: run `python main.py --offline --verificar cripta-03`, `python main.py --offline cripta-03` (verdict and order shown, game starts), and a non-solvable crypt with and without `--forzar` (if no recorded crypt is non-solvable, say so and report that only the automated tests cover it); check the exit status of `--verificar` and that `cache/llaves/` holds the saved file; report exactly what could be checked
- [ ] T041 Add a note under T040 saying what was checked and what was not, and update `specs/004-crypt-solvability/checklists/requirements.md` only if a spec correction was needed (a spec correction goes in its own commit before the code that depends on it) — all FRs

---

## Dependencies & Execution Order

```text
Phase 1 (T001–T002)  baseline: nothing else may start before it
→ Phase 2  foundations   T003 ∥ T004 → T005
→ Phase 3  US2           T006 → T007 → T008
→ Phase 4  US4           T009 → T010
→ Phase 5  US3           T011 → T012 → T013
→ Phase 6  US7           T014 → T015 → T016, T017 → T018
→ Phase 7  US1           T019 → T020, T021 → T022 → T023
→ Phase 8  US5           T024 → T025 → T026
→ Phase 9  US6           T027 → T028 → T029 → T030
→ Phase 10 US8           T031 → T032 → T033
→ Phase 11 polish        T034, T035, T036 → T037 → T038 → T039 → T040 → T041
```

- Phases 3 to 5 each add code to `model/solvabilidad_logica.py`, so they are sequential. Phase 6 (data) needs only the DTOs and could run beside Phases 3 to 5 in a second session; it is placed after them because the flow needs both.
- Phase 7 needs Phase 5 (the report) and Phase 6 (the key list). Phases 8 and 9 edit `aplicacion.py` and `main.py` after it, so they are sequential.
- Phase 10 needs Phase 5 (`Verificador` with the report).
- Edits to the same file are sequential: `model/solvabilidad_logica.py` (T007 → T012), `aplicacion.py` (T022 → T028), `main.py` (T025 → T029 → T032), `tests/test_solvabilidad_orden.py` (T005 → T006), `tests/test_solvabilidad_informe.py` (T009 → T011), `tests/test_solvabilidad_comandos.py` (T019 → T024 → T027), `grabar_offline.py` (T017).
- `[P]` marks tasks that touch different files with no unfinished dependency; with one implementer they can be done in any order inside their phase.

### Parallel examples

```text
Phase 2:  T003 ∥ T004 (DTOs vs test helper)
Phase 3–5: T006 ∥ T009 ∥ T011 (write the tests first, in different files)
Phase 6:  T016 ∥ T017 (store and repository vs recording)
Phase 7:  T020 ∥ T021 (service vs report text)
Phase 11: T034 ∥ T035 ∥ T036
```

## Implementation Strategy

1. **Phase 1 first.** The baseline test count is taken on the unchanged code.
2. **The pass** (Phases 3 to 5): order and verdict, then enemy keys, then the report, reviewed one phase at a time. MVP of the verification: Phase 3 alone decides and orders; Phase 5 explains.
3. **Key query and flow** (Phases 6 and 7): data first, then the start flow. MVP of the feature: Phases 3 to 7 (a player is never sent into an impossible game without knowing it).
4. **`--forzar`, `--verificar` and the benchmark** (Phases 8 to 10), then polish (Phase 11).
5. Commit per phase; a spec correction always goes in its own commit before the code that follows it (Constitution VII). Review each phase's checkpoint before starting the next.
6. **Scenario coverage** (Constitution IX): US1-1, US1-2, US1-3 → T019; US2-1..3 → T006; US3-1..3 → T011; US3-4 → T011; US4-1 → T009; US4-2 → T011; US5-1 → T024; US6-1 → T027; US6-2 → T027; US7-1..3 → T014; US7-4 (FR-022) → T019; US8-1 → T032 and T033; US8-2 → T032 and T033; US8-3 → T031; offline reading and recording (FR-006) → T014; Appendix B → T037.
7. **Mandatory scenarios of the brief** (spec Input): 1 → US3-1 (T011); 2 → US4-1 (T009); 3 → US2-2 (T006); 4 → US1-2 (T019).
