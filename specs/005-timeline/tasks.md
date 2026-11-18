---

description: "Task list for Timeline (consult the game at any past instant)"
---

# Tasks: Timeline (consult the game at any past instant)

**Input**: Design documents from `specs/005-timeline/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R12), data-model.md, contracts/ (comando-historia, cli-replay-hasta-checkpoint, dto-historia, formato-guardado-v2, reporte-bench-linea-tiempo), quickstart.md, bench-antes.txt (the "before" baseline, already saved)

**Tests**: Required. Constitution IX: every acceptance scenario has an automated test that cites its FR, and every task cites at least one FR. All tests use fake data built in the test (hand-built rooms, fake clients, fake catalog) and **no network**; a fake client that raises on any call is used wherever the plan says "never touches the network".

## Format: `[ID] [P?] [Story] Description — FR`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: user story from spec.md (US1–US8); phases without a story are shared groundwork
- Every test function's docstring MUST cite its FR and scenario, e.g. `"""FR-001, FR-004 · US1-1"""`.
- Within a phase, write the tests first and run them: they must fail for the right reason before the implementation tasks, and pass after them.
- Phases follow the order the group asked for and can be reviewed on their own; each ends with a checkpoint that says what is true when it is merged. Story numbers do not follow phase order.

## Path Conventions

Single-project layered layout at the repo root: `dto/`, `data/`, `model/`, `service/`, `controller/`, `view/`, `adapters/`, `structures/`, `bench/`, `tests/`. `aplicacion.py` and `main.py` are at the root. Identifiers are in Spanish as in the code base.

## Test files

| File | Covers |
|---|---|
| `tests/linea_tiempo_apoyo.py` (helper, not a test module) | seeded game builder, fake client/catalog, live-summary capture, the oracle runner |
| `tests/test_linea_tiempo_estructura.py` (new) | `LineaTiempo`: search, trim, grid, forbidden imports |
| `tests/test_registro_estado.py` (new) | state record round trip, scratch graph, stop bound |
| `tests/test_linea_tiempo_registro.py` (new) | recording of actions and checkpoints (US6) |
| `tests/test_linea_tiempo_consulta.py` (new) | US1, US2 at service level, instant and action rules |
| `tests/test_linea_tiempo_retroceso.py` (new) | US3, ledger of skipped effects |
| `tests/test_linea_tiempo_comando.py` (new) | `historia` command, DTOs, texts, log/undo untouched |
| `tests/test_linea_tiempo_oraculo.py` (new) | the oracle, run in three modes: plain, after scrolls, after save and load |
| `tests/test_linea_tiempo_replay.py` (new) | US4 |
| `tests/test_linea_tiempo_guardado.py` (new) | US5 |
| `tests/test_linea_tiempo_opciones.py` (new) | `--checkpoint-cada` (US6-6/7/8) |
| `tests/test_bench_linea_tiempo.py` (new) | US6-3, US7, US8 |
| `tests/fixtures/guardado_v1.sav` (new binary fixture) | a save written by the part-one code |

## Common fixtures (`tests/linea_tiempo_apoyo.py`, created in T004)

- `armar_mundo(semilla, salas, enemigos, cazadores, con_objetos, con_pergaminos)` → hand-built rooms (`Sala`, `Salida`, `enlazar`), a `Jugador`, a `Partida` and a fake factory that fills rooms from in-test contents and a fake ficha table; no repository, no client. Also returns the *world builder* (a function that rebuilds the skeleton) the timeline needs.
- `FakeCliente`: counts calls and raises `AssertionError` on any call (proves "no network"); `FakeCatalogo` with an LRU of 2 fichas, so evictions happen in short games.
- `jugar_semilla(servicio, semilla, n)` → a deterministic list of commands (moves among open exits, waits, attacks when an enemy is present, pick-ups/drops, uses, door opens, optional scroll reads) executed through `Controlador.ejecutar` with a silent view; returns the commands.
- `resumen_plano(partida_o_dto)` → comparable plain tuple of exactly the FR-004 fields (clock, room, life and stats, equipment, inventory in order **without** the cursor, active effects, enemies in the room with life, known map). Built twice: once from a live `JuegoService` and once from a `ResumenHistoriaDTO`.
- `capturar_vivo(servicio)` → `(numero_de_accion_proxima, reloj, resumen_plano)`; the oracle calls it **before every player action** and once at the end.
- `PartidaInstrumentada(Partida)`: a test subclass used by a **second live game** (same world, same seed, same commands) that appends a snapshot of `resumen_plano` with its time (a) once at construction, (b) after every executed non-player event (it wraps `_actuar_enemigo`, `_cerrar_puerta` and `efectos.ejecutar`), and (c) after each player action completes (it wraps `_accion_jugador`). It never uses `Reproductor`, `LineaTiempo` or any timeline code, so the oracle is independent of the code under test.
- `oraculo(servicio, vivos, instantaneas, consultar)` → for every entry of `vivos` (captured **before** every player action) checks `consultar("#", k)` equals the captured summary; for every instant t from 0 to the clock checks `consultar("t", t)` against the oracle's expected summary: if t is the clock of a decision, the `vivos` entry of that decision (decision wins); otherwise the last entry of `instantaneas` with time ≤ t. Reports the first difference with k, t and both summaries.
- After a scroll the helper truncates `vivos` to the surviving actions (entries for numbers above n are dropped, and the entry for decision n+1 is replaced by the live summary taken right after the scroll) and truncates `instantaneas` to the entries taken before that decision. Numbers of reverted actions are then rejected by the query, not compared.

## Phase 1: Baseline

**Purpose**: fix the reference. Nothing in this phase edits code.

- [X] T001 Check that `specs/005-timeline/spec.md` is committed (Constitution VII; commit `0b0663a`) and that `git status` shows no change under `model/`, `structures/`, `data/`, `service/`, `dto/`, `view/`, `controller/`, `adapters/`, `bench/`, `aplicacion.py`, `main.py` — all FRs
- [X] T002 Run `python -m pytest` on the unchanged code and note the count and time as the "all green before" reference for Phase 12 — all FRs
- [X] T003 Check that `specs/005-timeline/bench-antes.txt` exists and contains the `bench_historial` and `bench_guardado` reports of the unchanged code; **do not regenerate it** — FR-026, FR-027

**Checkpoint**: baseline noted, nothing else changed.

## Phase 2: Foundations — structure, state record, scratch world (blocks every story)

**Purpose**: the pieces every later phase uses. No story is complete here.

- [X] T004 Create the test helper `tests/linea_tiempo_apoyo.py` with the fixtures listed above (`armar_mundo`, `FakeCliente`, `FakeCatalogo`, `jugar_semilla`, `resumen_plano`, `capturar_vivo`, `oraculo`); it imports only from `model/`, `dto/`, `structures/`, `data/`, `service/`, `controller/` — FR-009, FR-025
- [X] T005 [P] Write `tests/test_linea_tiempo_estructura.py` (fails first): `ultimo_menor_o_igual` equals a plain linear scan on seeded vectors (including t below the first clock, equal to a clock, above the last); its comparison counter grows ~log2 n (counter at n=1 000 and n=100 000 differ by a small constant, not by 100×); clocks must be strictly increasing (appending a clock ≤ the last raises `ValueError`); `recortar(n)` removes only from the end and leaves the first n records untouched; `len(puntos) ≤ ⌊A/K⌋ + 1`; `K` must be a positive integer (0, negative, non-int raise `ValueError`) — FR-019, FR-022, FR-011
- [X] T006 Implement `structures/linea_tiempo.py` (`LineaTiempo`): parallel vectors `relojes`, `tipos`, `argumentos` (index = `numero − 1`); `k` "checkpoint spacing, positive int"; `puntos` where `puntos[i]` is the state with `i·K` actions taken, found by `punto_para(boundary)` = slot `boundary // K` in O(1); `ultimo_menor_o_igual(t)` iterative binary search with a `comparaciones` counter; `recortar(n)` with `del` on each vector from the end; `omitidos` as an empty chronological list for Phase 5. No `dict`, `set`, `heapq`, `bisect`, `collections`, `copy` — FR-019, FR-021, FR-022, FR-028
- [X] T007 [P] Write `tests/test_registro_estado.py` part 1 (fails first): `capturar(partida)` then `restaurar(registro, mundo)` into a **fresh** graph gives a `Partida` whose `resumen_plano` equals the original's, and after the same 200 seeded actions (with hunters, poison, speed potion, traps, a door with automatic closing, an enemy death with loot) both stay equal at every step; the random generator state is restored exactly (`array('I')` of 625 words + the `gauss_next` marker); the record shares no mutable object with the live game (mutate the live game afterwards, the record does not change) — FR-023, FR-009, FR-004
- [X] T008 Implement `model/registro_estado.py` per data-model "RegistroEstado": partida fields (`reloj`, `num_sec`, `azar`, `acciones_jugador`, `enemigos_derrotados`, `terminada`, `victoria`, `abrio_puerta_salida`, `retrocesos`, `modo_decisor`, `siguiente_instancia`), player, active enemies, effects, touched rooms (`conocimiento`, `rastro`, floor objects, `inactivos`, traps with `armada` and `evento`) and touched exits (`cerrada`, `memoria`), where **touched** means: a room with `conocimiento` > 0, or `rastro` not none, or non-empty `objetos`, `inactivos` or `trampas`; an exit whose `cerrada` differs from the skeleton's value or whose `memoria` is not 0; everything else is the skeleton, `conocidas` order, agenda events with `(kind, key)` references; entity lookup while restoring with sorted vectors and `VectorBusqueda` (no `dict`); no `copy` module. Add `Partida.desde_registro(registro, salas)` that builds a `Partida` **without** the constructor's side effects (no event scheduled, no room entered) — FR-023, FR-021, FR-028
- [X] T009 [P] Write `tests/test_registro_estado.py` part 2 (fails first): the pure skeleton builder returns a new room vector and writes nothing to the repository (`repo.salas` identical object and contents before and after); building it twice gives two graphs that share no `Sala` or `Salida`; `avanzar_hasta_jugador(limite=t)` stops before extracting an event with `tiempo > t`, runs every event with `tiempo ≤ t` whatever its sequence number, and with `limite=None` behaves exactly as today (the existing suite stays green) — FR-001, FR-006, FR-009
- [X] T010 Extract a pure skeleton builder `construir_grafo(dtos)` in `data/repositorio_cripta.py` (returns the sorted room vector; `construir_salas` calls it and then stores the result, behavior unchanged) and add the optional `limite` parameter to `Partida.avanzar_hasta_jugador` in `model/partida_logica.py` (look at `agenda.proximo()` before extracting; `None` keeps current behavior) — FR-001, FR-006

**Checkpoint**: `LineaTiempo`, the state record, the pure builder and the stop bound exist and are tested; nothing in the running game uses them yet; existing tests are still green.

## Phase 3: Recording of actions and checkpoints during play (US6)

**Goal**: while the game runs, every surviving action gets a record and every K actions a checkpoint is taken; nothing changes for the player.

**Independent Test**: play seeded games and inspect the timeline: numbers, clocks, resolved targets, checkpoint count and spacing.

### Tests (write first)

- [X] T011 [US6] Write `tests/test_linea_tiempo_registro.py` (fails first). Cases, each citing its FR: (a) after N successful actions the vectors hold N records numbered from 1 with `reloj` equal to the clock at the decision (before the action), `tipo` in `mover, esperar, atacar, recoger, soltar, equipar, usar, abrir`, and the resolved `argumento` (direction, enemy id or object instance id; none for `esperar`) — including `usar` and `soltar` with the inventory cursor moved by `sig`/`ant` and `atacar` with no id in a room with one enemy — FR-003, FR-006; (b) failed commands (wall, closed door, no key, full inventory), `mapa`, `inv`, `sig`, `ant`, unknown commands and `ir a` with an unexplored target add **no** record; `ir a` adds one `mover` per step — FR-006, FR-003; (c) checkpoint 0 exists before any action and a new one is taken exactly when the number of actions taken is a multiple of K; `len(puntos) ≤ ⌊A/K⌋ + 1` for K = 1, 3, 7 and K larger than the game — FR-019, US6-1; (d) every checkpoint contains the random generator state (restoring it and drawing gives the same numbers the live game then drew) — FR-023, US6-5; (e) memory: two seeded games of the same world, one twice as long, with K fixed: the measured memory of the timeline (`tracemalloc`, timeline alone) grows by a factor between 1.5 and 2.5, not by a factor close to the ratio of actions × touched state — FR-021, US6-3; (f) a game that ends (death) stops recording and keeps `reloj_final` — FR-002
- [X] T012 [P] [US6] In the same file add the scenario test for US6-2/US6-4 at structure level: for every boundary of a 3 000-action synthetic game, `punto_para` returns the slot `boundary // K` and the number of actions between that checkpoint and the boundary is ≤ K − 1; the checkpoint lookup does not iterate the vectors (zero comparisons for the slot; the clock search itself is tested in T005) — FR-020, FR-022

### Implementation

- [X] T013 [US6] Create `model/linea_tiempo_logica.py` with `LineaTiempoPartida`: `iniciar(partida, constructor_mundo, k)` (takes checkpoint 0), `registrar_accion(partida, tipo, argumento, reloj_antes)` (appends the record with `numero` = actions taken after the action; takes a checkpoint when that number is a multiple of K), `reloj_final`, read access for queries. Define the constant `K_POR_DEFECTO = 50  # PROVISIONAL: replaced by T068 with the value measured by the benchmark (plan.md, "Default K")` so that starting a game without `--checkpoint-cada` works from this phase on; tests and the benchmark still pass K explicitly — FR-019, FR-021, FR-023
- [X] T014 [US6] Edit `service/juego_service.py`: after each **successful** action (`mover`, `esperar`, `atacar`, `recoger_objeto`, `soltar_objeto`, `equipar_objeto`, `usar_objeto`, `abrir_puerta`) call `registrar_accion` with the resolved target and the clock read **before** the call. The target is resolved from state before calling the model: the direction; the enemy id the service already chose (`atacar`); the object instance id (`recoger_objeto`); for `usar_objeto`, `soltar_objeto` and `equipar_objeto`, the `id_instancia` of the object under the inventory cursor (`inv.actual`) read before the call. **Success rule**: the call is recorded as an action only when `acciones_jugador` went up by exactly one **and** `partida.retrocesos` did not change; a call after which `retrocesos` changed read a scroll (see T034) and is never recorded as an action. `ir_a` records through `mover` unchanged; the service receives the `LineaTiempoPartida` in its constructor (default `None` keeps every existing test untouched) — FR-003, FR-006, FR-002
- [X] T015 [US6] Edit `aplicacion.py` (`_sesion` and `reproducir`) to create the `LineaTiempoPartida` for the new `Partida` with the world builder from the repository's pure builder and the K in use, and pass it to `JuegoService`; the K comes from a parameter (wired to the command line in Phase 9) — FR-019, FR-017

**Checkpoint**: a played, replayed or loaded game builds its timeline; no query exists yet; part-one behavior is unchanged (existing tests green).

## Phase 4: The `historia` query by action number and by instant (US1, US2)

**Goal**: a read-only reconstruction of the state at any instant or before any action, at model/service level (the command and DTOs come in Phase 6).

**Independent Test**: the oracle test in plain mode (no scrolls) and the scenario tests below.

### Tests (write first)

- [X] T016 [US1] Write `tests/test_linea_tiempo_consulta.py` (fails first), one test per scenario, each citing its FR: US1-1 `t` in 0..T gives the state after executing every event with time ≤ t (compare with the live state captured when the clock first reached ≥ t and with an independent replay by the oracle) — FR-001, FR-002, FR-004; US1-2 `#k` gives the state just before action k — FR-003, FR-004; US1-3 `t` > clock is rejected with reason `despues_del_reloj` and nothing changes — FR-005; **US1-4 "several events at the same instant"**: build a world where two enemies act at the same instant t and the player has **no** decision at t; the state at t includes both — FR-001; **US1-5 and US1-9, decision wins**: an instant at which the player has a decision gives the state just before it, and events of that instant that come later in agenda order `(tiempo, num_sec)` are **not** shown (plan, "Decisions on the points for the spec" 1) — FR-001, FR-009; US1-6 every summary has the FR-004 fields and the known map shows nothing unknown at that instant (a room first seen at clock 500 is absent from `t=499`) — FR-004; US1-7 `t=0` is the initial state — FR-002, FR-004; US1-8 malformed, negative, `#0`, `#x`, missing argument are rejected with `argumento_invalido` — FR-005
- [X] T017 [P] [US1] In the same file: edge cases — `t` equal to the clock is accepted and equals the live state; `#k` with k = actions taken + 1 rejected with `accion_inexistente`; a game with no actions: only `t=0`; a finished game (death) accepts every instant up to the end; K = 1 and K larger than the game give identical answers (only the counters differ); an instant exactly on a checkpoint and one K actions after it equal a reconstruction from checkpoint 0 — FR-002, FR-003, FR-005, FR-019, FR-020
- [X] T018 [P] [US2] Add service-level tests: after any mix of accepted and rejected queries the live clock, the full live `resumen_plano`, `acciones_jugador`, the agenda (events and sequence numbers), the random generator state and the undo allowance (the scroll reverts the same actions in the same order) are identical to those of the same seeded game without queries (US2-1, US2-3, US2-4); two games with the same world, seed and commands, one with queries in the middle, end identical (US2-5) — FR-006, FR-008, FR-009
- [X] T019 [P] [US2] Add the "never touches the network" test (the `FakeCliente` raises on any call, the `FakeCatalogo` has 2 fichas so evictions happen): run 100 queries on a 1 000-action game that entered 30 rooms; no call, the request counter does not move, and a ficha evicted long ago is still found — FR-006, FR-009 (research R8)
- [X] T020 Write `tests/test_linea_tiempo_oraculo.py` **mode 1, plain**: for K = 1, 3, 7 and K larger than the game, on a seeded 400-action game with hunters, poison, speed potion, traps, doors with automatic closing and a death: capture the live summary before every player action with `capturar_vivo`, run the same seed and commands in the second live game with `PartidaInstrumentada` to get the per-event snapshots, then check with `oraculo` that `#k` gives exactly the captured summaries and that `t` gives, at every t from 0 to the end, the summary the oracle expects (the decision's capture when t is a decision clock, otherwise the last snapshot with time ≤ t) — SC-002, FR-001, FR-002, FR-003, FR-004

### Implementation

- [X] T021 [P] [US2] Create `data/fabrica_reproduccion.py` and the frozen ficha store: `FichasCongeladas` is a `VectorBusqueda` keyed by ficha id; add the observer in `FabricaModelo._ficha` (`data/fabrica_modelo.py`) that stores every ficha the live factory resolves; `FabricaReproduccion.poblar_sala(sala)` fills a scratch room from `repo_cripta.contenidos` and the store only, with the instance counter from the record, and raises `ErrorReproduccion` if a ficha or content is missing — it never calls `repo_catalogo.resolver` or the client — FR-006, FR-023
- [X] T022 [US1] Create `model/reproduccion_logica.py` (`Reproductor`): builds the scratch world with the pure builder, loads the checkpoint with `Partida.desde_registro`, re-plays the stored actions with the real `Partida` methods (a move first populates the room through `FabricaReproduccion`, as `JuegoService.mover` does, **when the world has one**; worlds built by hand, such as the benchmark's, have none and the step is skipped; before `usar`, `soltar` or `equipar` it places the inventory cursor on the object whose `id_instancia` is the stored argument, and `atacar` and `recoger` address their target by that id), applies the stop rule of research R7: `k = ultimo_menor_o_igual(t)` over the decision clocks; if `c_k == t` stop before action k (decision wins); if `c_k < t` play action k then `avanzar_hasta_jugador(limite=t)`; for `#k` valid only for 1 ≤ k ≤ n; at most K actions are applied (count them and raise if exceeded) — FR-001, FR-003, FR-006, FR-009, FR-020
- [X] T023 [US1] Create `service/historia_service.py` with `reproducir_en_instante(t)` and `reproducir_en_accion(k)`: validate arguments (reasons `argumento_invalido`, `despues_del_reloj`, `accion_inexistente`), call the `Reproductor`, return the scratch `Partida`, the reported clock (`t`, or `c_k` for `#k`) and the reason; never touches the live `Partida`, its `Historial`, its agenda or its random generator — FR-005, FR-006, FR-008, FR-004
- [X] T024 [US1] Expose the two methods on `JuegoService` (`historia_por_instante`, `historia_por_accion`) delegating to `HistoriaService`; run T016–T020 until green — FR-001, FR-003, FR-005

**Checkpoint**: at model/service level every instant and every `#k` of seeded games equals what the live game showed; queries leave no trace; no network; no scroll cases yet.

## Phase 5: Scroll trim and the ledger of skipped effects (US3)

**Goal**: after a scroll the timeline describes the game as it ended up, with no extra checkpoint and with the effects the undo skips applied when a re-simulation passes the rewind point.

**Independent Test**: the scroll scenario tests, the ledger tests (one per row 1–6 of research R6) and the oracle in mode 2.

### Tests (write first)

- [X] T025 [US3] Write `tests/test_linea_tiempo_retroceso.py` (fails first), scenario tests citing FR: US3-1 after a scroll no query shows any effect of the reverted action (compare every instant with the oracle's plain replay of the surviving actions) — FR-010; US3-2 `t` > clock after the scroll is rejected — FR-005, FR-010; US3-3 new actions after the scroll are shown, not the reverted ones — FR-010; US3-4 `#k` with k beyond the surviving actions is rejected, and numbering continues from the last survivor — FR-003, FR-010; US3-6 the scroll still reverts at most 5 actions: each read reverts one action (`Historial.deshacer` pops one frame), so six consecutive reads revert five and the sixth is refused with "no hay acciones que retroceder" and trims nothing; the timeline answers instants far older than 5 actions — FR-012; **a scroll read with `usar`** (the cursor on the scroll, command `usar` instead of `retroceder`) trims the timeline exactly like `retroceder`, is not recorded as an action, and the following queries equal the live state — FR-010, FR-012; edge cases: a scroll with fewer than 5 actions taken trims only what was reverted; consecutive scrolls trim in turn — FR-010, FR-011
- [X] T026 [P] [US3] In the same file, US3-5: the work of a scroll does not depend on the length of the game — count the operations of `recortar` plus ledger retagging (a counter in `LineaTiempo`) for a scroll at action 1 000 and at action 5 000 of the same world: equal ±r — FR-011
- [X] T027 [P] [US3] In the same file, the **ledger tests**, one per row of the table in research R6, each building the case by hand and comparing the answer of a query after the rewind point with the live state: (1) the consumed scroll is absent after the rewind point and present before it; (2) a scroll picked up by a reverted action is in the inventory after the rewind (the undo leaves it) and the floor no longer has it; (3) a scroll dropped by a reverted action is on the floor and not in the inventory; (4) the instance counter: loot of a reverted kill advances it, and the next object created after the scroll has the same id in the live game and in a query that re-plays that creation; (5) a room populated by a reverted move keeps its population, and entering it again after the scroll gives the same objects, enemies and ids in the live game and in a query; (6) a scroll created by that population has the same id. Plus: a checkpoint of boundary n kept by the trim (n multiple of K) is **not refreshed** and a query that starts from it applies the entries tagged n on top of it; entries tagged below the checkpoint's boundary are not applied; `len(puntos) ≤ ⌊A/K⌋ + 1` after every scroll (**no checkpoint off the K grid**, FR-019) — FR-010, FR-019, FR-020, FR-023
- [X] T028 [P] [US3] In the same file: ledger rules from data-model "EfectoOmitido": entries are chronological; a window entry (`reaplicar` false) older than the history capacity (5) is dropped after each recorded action; after a scroll the kept entries have `etiqueta` = n and `reaplicar` true; a second scroll to n2 < n retags the earlier-kept entries first, then the new window, preserving order; the ledger size after 5 000 actions with no scroll is ≤ the entries of the last 5 actions — FR-010, FR-011, FR-021
- [X] T029 Extend `tests/test_linea_tiempo_oraculo.py` **mode 2, after scrolls**: seeded games for K = 1, 3, 7, large, with 5 scroll reads at seeded moments (one right after a first entry into a room, one reverting a pick-up of a scroll, two consecutive), (one of the reads done with `usar` on the scroll), capturing the live summary before every player action and, after every scroll, truncating the captures as the helper in `Common fixtures` says; run the second live game with `PartidaInstrumentada` for the same commands (it performs the same scroll reads); then `oraculo` must pass for every surviving `#k` and every `t` ≤ clock, including instants between decisions around the rewind point, and `#k` for a reverted number must be rejected — SC-002, SC-004, FR-010

### Implementation

- [X] T030 [US3] Create `model/efectos_omitidos.py`: `EfectoOmitido(etiqueta, reaplicar, tipo, datos)` with `tipo` in `poblar, suelo_quitar, suelo_poner, inv_agregar, inv_quitar, contador` and the data per type from data-model (room id + starting instance counter; room id + instance id; room id + object record; object record; instance id; value); `aplicar(entrada, mundo)` that applies one entry to a scratch world (`poblar` sets the factory counter to `contador_inicial` then populates; `contador` sets the counter) — FR-010, FR-023
- [X] T031 [US3] Edit `model/partida_logica.py`: add `diario_omitidos` (a list, `None` when no timeline is active) appended at the exempt points of research R6 rows 1–3 only: `_quitar_del_suelo` and `_poner_en_suelo` (scroll branch), `recoger` (scroll added to the inventory), `soltar` (scroll removed), `usar_pergamino` (consumption); each entry tagged with `acciones_jugador` of the action in progress. No change to `Inventario` — FR-010
- [X] T032 [US3] Edit `data/fabrica_modelo.py` and `service/juego_service.py`: `poblar_sala` returns the instance counter it started from or `None` if the room was already populated; `JuegoService.mover` calls `LineaTiempoPartida.anotar_poblacion(id_sala, contador_inicial)` when a room was populated, tagged with `acciones_jugador + 1` — FR-010, FR-023
- [X] T033 [US3] Extend `structures/linea_tiempo.py` and `model/linea_tiempo_logica.py`: `LineaTiempoPartida.tras_retroceso(partida)` — n = `acciones_jugador`; `recortar(n)` deletes records and checkpoints above n from the end; retags every ledger entry of the reverted window and every kept entry with tag > n to tag n with `reaplicar` true (earlier-kept first); appends `contador(value)` with the live instance counter; **takes no checkpoint**; `registrar_accion` drops non-`reaplicar` entries older than `historial.capacidad` — FR-010, FR-011, FR-012, FR-019
- [X] T034 [US3] Edit `service/juego_service.py`: read `partida.retrocesos` before and after **every** service call that can read a scroll — `retroceder` and `usar_objeto` (because `Partida.usar` hands a scroll under the cursor to `usar_pergamino`); if it changed, call `tras_retroceso` (and do not record the call as an action, T014). A refused scroll ("no hay acciones que retroceder", `retrocesos` unchanged) changes nothing — FR-010, FR-012
- [X] T035 [US3] Edit `model/reproduccion_logica.py`: apply the ledger entries tagged b, in order, when the scratch world is **at the decision point with b actions taken** — right after loading a checkpoint of boundary b, or after replaying action b and running the events up to the player's turn; an instant t with `c_b ≤ t < c_{b+1}` stops before that point and does not apply them; never apply entries tagged below the checkpoint's boundary; add to T027/T029 a case with an instant between action b and the turn after a scroll to b (it must show the pre-scroll state, as the second live game's snapshots do); run T025–T029 until green — FR-010, FR-020, FR-023

**Checkpoint**: after any number of scrolls every query equals the live state and never shows a reverted action; no checkpoint is ever off the K grid; scroll cost does not depend on game length.

## Phase 6: The `historia` command and its DTO (US1, US2)

**Goal**: the player types `historia <t>` / `historia #k`; everything crosses layers as DTOs; the command leaves no trace in the log or the saved commands.

**Independent Test**: the command tests below and the oracle through the DTO.

### Tests (write first)

- [X] T037 [P] [US1] Write `tests/test_linea_tiempo_comando.py` part 1 (fails first): `historia <t>` and `historia #<k>` return a `RespuestaHistoriaDTO` whose `ResumenHistoriaDTO` fields are exactly `reloj, id_sala, nombre_sala, jugador, inventario, enemigos, mapa` (data-model); `reloj` is the requested instant for `t` and the decision clock for `#k`; `jugador`, `inventario`, `enemigos`, `mapa` reuse `JugadorVistaDTO`, `ObjetoInventarioDTO`, `EnemigoVistaDTO`, `MapaVistaDTO`; no import from `model/` in `dto/resumen_historia_dto.py` — FR-004, FR-029
- [X] T038 [P] [US1] Same file part 2: command parsing — `historia`, `historia abc`, `historia -3`, `historia #0`, `historia #x`, `historia 1.5`, `historia 3 4` are rejected with the accepted forms and change nothing; `historia t` with t > clock and `#k` beyond the surviving actions are rejected with their reasons; accepted queries print through `mostrar_historia` — FR-005, US1-8
- [X] T039 [P] [US2] Same file part 3: **log and saved commands**: run a seeded game through `Controlador` with a `BitacoraPartida` on a temporary folder, interleave accepted and rejected `historia` commands, and check that `partida.log` is byte-for-byte the log of the same game without them, that `controlador.comandos` has no `historia`, and that a `guardar` right after a query writes the same commands as without it (US2-2, US2-4) — FR-007, FR-017
- [X] T040 [P] [US2] Same file part 4: the scroll allowance — after queries the scroll still reverts the same actions in the same order (US2-3), and the live state, clock and agenda are untouched after rejected queries (US2-4) — FR-006, FR-008
- [X] T041 [P] [US1] Same file part 5: **FR-014 text identity** — the lines printed by `VistaConsola.mostrar_historia` and by `salida_replay.imprimir_historia` for the same `RespuestaHistoriaDTO` are identical, because both call `adapters/formato_historia.py`; the formatted text has the clock, room, life and stats, active effects, inventory (equipped marked), enemies with `vida/vida_max` and the known map in the layout of the `mapa` command — FR-004, FR-014
- [X] T042 Extend `tests/test_linea_tiempo_oraculo.py` **mode 1 and mode 2 through the command**: the same captured summaries are compared with what `Controlador.ejecutar("historia #k")` and `("historia t")` deliver (as DTO and as printed text via a recording view), for K = 1, 3, 7 and large, without and with scrolls — SC-002, SC-004, FR-004, FR-005

### Implementation

- [X] T043 [US1] Create `dto/resumen_historia_dto.py` with `ResumenHistoriaDTO(reloj, id_sala, nombre_sala, jugador, inventario, enemigos, mapa)` and `RespuestaHistoriaDTO(aceptada, motivo, resumen, termino_antes=False, reloj_final=None)` where `motivo` is one of `None`, `despues_del_reloj`, `accion_inexistente`, `argumento_invalido`; plain classes, no import from `model/` — FR-029, FR-004
- [X] T044 [US1] Extend `service/historia_service.py` and `service/juego_service.py`: build the `ResumenHistoriaDTO` from the scratch `Partida` with read-only code shared with `mapa_vista`/`estado_vista` (factor the common reading so the scratch partida and the live one use the same functions; the map is the scratch world's own `conocimiento`/`memoria`); `historia_por_instante` and `historia_por_accion` now return `RespuestaHistoriaDTO` — FR-004, FR-029
- [X] T045 [P] [US1] Create `adapters/formato_historia.py`: a pure function `lineas_historia(dto) -> list[str]` (no printing, no imports from `model/` or `view/`) — FR-004, FR-014
- [X] T046 [US1] Edit `controller/controlador.py`: add `historia` to the commands excluded **before** the "append to `comandos` and write to the log" step (today the exclusion list is `salir`, `guardar`, `cargar`, `ir`), parse `historia <t>` / `historia #<k>` (non-negative whole number; `#` followed by a positive whole number), call the service, show the summary through the view or the rejection through `_mostrar_mensaje` — FR-005, FR-006, FR-007
- [X] T047 [US1] Edit `view/vista_consola.py` (`mostrar_historia(dto)` printing `lineas_historia`) and `view/vista_silenciosa.py` (no-op) — FR-004, FR-014; run T037–T042 until green

**Checkpoint**: `historia` works in a game; accepted and rejected queries leave the log, saved commands, undo allowance and live state untouched; the oracle passes through the command.

## Phase 7: `--replay ... --hasta` without the view (US4)

**Goal**: headless summary at an instant, identical to the in-game one.

**Independent Test**: replay a recorded game with an inner and an outer instant.

### Tests (write first)

- [X] T048 [P] [US4] Write `tests/test_linea_tiempo_replay.py` (fails first): US4-1 the lines printed for `--hasta t` inside the game equal the lines `historia t` produces in the live game with the same crypt, seed and commands (record a seeded game's log with `BitacoraPartida`, replay it with a fake offline client) — FR-013, FR-014; US4-2 `t` greater than the final clock prints the final state, then a line saying the game ended earlier with the final clock — FR-015; US4-3 `Aplicacion.reproducir` with `--hasta` creates no view: every class in `view/` is patched to raise on construction and the run still succeeds — FR-016; US4-4 malformed or negative `--hasta` reports an error, exit status 1, and prints **no** state; `--hasta` without `--replay` is an argparse error; a log the game did not write correctly reports the error as in earlier specs and prints no state — FR-013; US4-5 a log with scroll readings gives the summary of the game as it ended up (equal to the live `historia`) — FR-010, FR-014
- [X] T049 [P] [US4] Same file: the replay stops executing commands as soon as the clock is ≥ t or the commands end, then answers from the timeline; the number of executed commands is smaller than the log's when t is early; the request counter is the one of a plain `--replay` of the same prefix (the query adds none) — FR-013, FR-006

### Implementation

- [X] T050 [US4] Edit `adapters/salida_replay.py`: `imprimir_historia(respuesta)` using `adapters/formato_historia.py`, and `imprimir_termino_antes(reloj_final)` for FR-015; no import from `model/` or `view/` — FR-013, FR-015, FR-016
- [X] T051 [US4] Edit `aplicacion.py` `reproducir(lector, hasta=None)`: with `hasta`, run the commands through `Controlador` with `vista=None`, stop once the clock ≥ `hasta` or the commands end, answer `hasta` from the timeline, print through `salida_replay`; if `hasta` > final clock print the final state and the "ended earlier" notice — FR-013, FR-014, FR-015, FR-016
- [X] T052 [US4] Edit `main.py`: `--hasta T` (integer ≥ 0, only with `--replay`; otherwise error and no state) passed to `reproducir`; update the help text; run T048–T049 until green — FR-013, FR-016

**Checkpoint**: `--replay LOG --hasta T` prints the same summary as the game, with no view, and the "ended earlier" notice past the end.

## Phase 8: Save format v2 — K in the header, part-one incompatibility (US5)

**Goal**: the file stores the commands and the K in use (the timeline is rebuilt by re-executing the commands, decision of 2026-11-18); a v1 file is refused with the existing mechanism.

**Independent Test**: round trip, v1 fixture, damaged files, and the oracle after save and load.

### Tests and fixture (write first)

- [X] T053 [US5] Create the fixture `tests/fixtures/guardado_v1.sav` by running the **part-one** writer: check out `adapters/guardado_binario.py` of commit `0b0663a` into a temporary folder outside the repo, run its `guardar` on a small seeded game, copy only the resulting bytes into the fixture; also create `tests/fixtures/guardado_v1_corto.sav` (a valid v1 file cut to 20 bytes: shorter than the v2 header but with magic and version intact). Document how they were made in a comment at the top of `tests/test_linea_tiempo_guardado.py` — FR-018
- [X] T054 [P] [US5] Write `tests/test_linea_tiempo_guardado.py` (fails first): US5-1 save a game with a long timeline (K = 7), load it, and every `historia` answer equals the one before the save (`oraculo` over a saved-and-loaded game: capture before every action, load, compare) — FR-017; US5-2 save after a scroll, load, the timeline still excludes the reverted actions and the ledger effects hold (consumed scroll, populated room) — FR-010, FR-017; US5-3 the v1 fixture is refused with "Formato de guardado incompatible: el archivo es v1 y este programa usa v2" and `validar_guardado` returns the message — FR-018; US5-3 the short v1 fixture (20 bytes) gives the **same incompatibility message**, not "truncado" — FR-018; US5-4 after a refused load nothing is loaded partially, the current game is unchanged (state, clock, commands list), and the file's bytes and modification time are unchanged — FR-018; US5-5 an empty file, a truncated v2 file, random bytes and a v2 file with `k = 0` are reported as unreadable (`ErrorGuardado`) and never loaded — FR-018; the file records no query and no notice: a save right after a query is byte-identical to one without it — FR-007, FR-017
- [X] T055 [P] [US5] Same file: the saved K wins — a game saved with K = 7 and loaded with K = 20 requested keeps K = 7, the checkpoints of the rebuilt timeline are at multiples of 7, and a notice text is produced only when the option was typed and differs (no notice when it was not typed) — FR-017, FR-019
- [X] T056 Extend `tests/test_linea_tiempo_oraculo.py` **mode 3, after save and load**: play a seeded game with scrolls, save in the middle, load into a new `Aplicacion`/service (commands re-executed with recording on), keep playing, and check `oraculo` over the whole game (before-save captures and after-load captures) — SC-002, SC-005, FR-017

### Implementation

- [X] T057 [US5] Edit `adapters/guardado_binario.py`: `VERSION_FORMATO = 2`; `leer_cabecera` first reads the 6-byte prefix `"<4sH"` (magic, version) and checks magic then version, **then** reads the rest of the header per version (v2: the v1 fixed fields plus `k` u32); a v1 file always yields the existing "Formato de guardado incompatible" message, also when it is shorter than the v2 header; fewer than 6 bytes or a later short read is "El archivo está truncado"; `k` must be a positive integer or the file is unreadable; `CabeceraGuardado` and `guardar` carry `k`; nothing else in the layout changes — FR-018, FR-017
- [X] T058 [US5] Edit `aplicacion.py` (`guardar_partida`, `_sesion`): save the K in use; on load take the saved K for the new timeline and return the notice text if an explicit option differs; load keeps re-executing the commands with recording on (no suspension, no timeline in the file); `validar_guardado` keeps running before any state changes — FR-017, FR-018
- [X] T059 [US5] Run T053–T056 until green; run the existing save/load tests (`tests/test_ir_a_guardado.py`, `tests/test_semilla.py`) and fix only what the header change breaks — FR-018, FR-017

**Checkpoint**: v2 files round trip with the same answers; v1, empty, truncated and random files are refused without touching the game or the file.

## Phase 9: `--checkpoint-cada` (US6)

**Goal**: K is set from the command line, validated, and the saved K wins on load.

### Tests (write first)

- [X] T060 [P] [US6] Write `tests/test_linea_tiempo_opciones.py` (fails first): US6-6 `--checkpoint-cada` with no value, `0`, `-5`, `abc`, `2.5` exits with status 2 and an error message, runs nothing and makes no request (the fake client raises on any call) — FR-019; US6-7 with no option the game starts and uses `K_POR_DEFECTO` (provisional 50 until T068; the test reads the constant instead of repeating the number, so T068 needs no test change) — FR-019, FR-026; US6-8 loading a game saved with K1 under `--checkpoint-cada K2` keeps K1 and shows the notice "`--checkpoint-cada` ignored: this game was saved with K=<K1>" — FR-017, FR-019; the option is also accepted with `--replay` and ignored by `--verificar` — FR-019

### Implementation

- [X] T061 [US6] Edit `main.py`: `--checkpoint-cada K` (type validated as a positive integer; any other value is refused through `parser.error`, exit status 2, before anything runs), default `None` meaning "not typed" so the load notice appears only when it was typed; pass K and "typed" to `Aplicacion`; when not typed, K is `K_POR_DEFECTO` (provisional, T013) — FR-019, FR-017
- [X] T062 [US6] Edit `aplicacion.py` so `jugar`, `reproducir` and the load path use the K from the option, the default or the saved file, and print the notice through the view (`mostrar_mensaje`) at the start of the loaded session; run T060 until green — FR-017, FR-019

**Checkpoint**: the option is validated, the saved K wins with a notice, and a game started without the option uses the provisional default K = 50.

## Phase 10: Benchmark — K = 10, 50, 200 and no checkpoints; the default K (US7, US8, US6)

**Goal**: measurements that justify the default K by the rule in `plan.md` ("Default K"); synthetic games deterministic by seed; no network, no view.

**Independent Test**: `python -m bench.bench_linea_tiempo` and `tests/test_bench_linea_tiempo.py`.

### Tests (write first)

- [X] T063 [P] [US8] Write `tests/test_bench_linea_tiempo.py` (fails first, small sizes: 300 actions): US7-3 / US8-5 the synthetic game generated twice with the same seed gives the same command list and the same final state, and different seeds differ — FR-025; US8-1 / US8-2 / US8-4 the report text has a row for each of K = 10, 50, 200, a `none` row (only checkpoint 0, re-simulating from the start), the columns of `contracts/reporte-bench-linea-tiempo.md`, and a "Default K" line that names the row it comes from — FR-026; US6-3 linearity row: the same seed at A and 2A actions at fixed K gives a memory ratio between 1.5 and 2.5 — FR-021, FR-026; SC-008 in every K row "max actions re-played ≤ K" and in the `none` row equal to the whole game — FR-020; US7-2 the benchmark makes no request (fake client raises) and creates no view (every class in `view/` patched to raise) — FR-016, FR-024; the p99 uses `ordenados[int(n·0.99)]` over queries chosen by seed spread over the whole game including the oldest and the most recent instants — FR-024; the default-K rule function is unit-tested on made-up tables (largest K with p99 ≤ 25 ms, memory of every K reported next to it; none qualifies → "the group decides") — FR-026
- [X] T064 [P] [US8] Same file: the forward-vs-backward section reports cost per re-simulated action, cost per inverted action, closures per action in `Historial` and the extrapolated bytes at A actions, with numbers taken from a run, not constants — FR-026, FR-027 (research R1)

### Implementation

- [X] T065 [US7] Create `bench/juego_sintetico.py`: given world, seed and length, return the same command sequence every time (moves among open exits chosen with a seeded generator, waits, attacks when an enemy is present, pick-ups and drops when objects exist, a few scroll reads including one right after entering a new room); worlds `referencia` (cripta-06 skeleton from the offline pack + 30 hunters, as `bench_ciclo.armar_partida_referencia`), `grande` (100 rooms, 100 enemies), `extremo` (100 rooms, 300 enemies, information only); ≥ 5 000 player actions each — FR-025, FR-024
- [X] T066 [US7] Create `bench/bench_linea_tiempo.py` with `ejecutar()`: for each world and each K in (10, 50, 200) plus the no-checkpoint alternative report checkpoints, memory of checkpoints, memory of actions + ledger (`tracemalloc` on the timeline alone, game excluded), graph-build time share, maximum actions re-played, p99 / mean / worst of the query set; the linearity row; scroll reads, ledger entries kept and checkpoints off the K grid (must be 0); the forward-vs-backward section; the "Default K" line chosen by the plan's rule (largest K in the set with p99 ≤ 25 ms on `referencia`, memory of every K printed next to it; if none qualifies, print the table and "the group decides") — FR-024, FR-025, FR-026, FR-021
- [X] T067 [US7] Register `bench_linea_tiempo` in `main.py --bench` (after `bench_historial`), with no network and no view; make T063–T064 green — FR-016, FR-026
- [X] T068 [US7] **Measure and decide**: run `python -m bench.bench_linea_tiempo` on the reference world with ≥ 5 000 actions; apply the plan's rule; replace the provisional `K_POR_DEFECTO = 50` in `model/linea_tiempo_logica.py` with the chosen value and remove the PROVISIONAL marker from the code; copy the table, the machine, Python version, date and the chosen row into `specs/005-timeline/plan.md` ("Default K": replace "provisional, pending measurement") and into `docs/DECISIONES.md` (new section for the timeline); save the full output as `specs/005-timeline/bench-despues-linea.txt`. If p99 > 50 ms at the chosen K on `referencia`, stop and report to the group instead of choosing — FR-019, FR-024, FR-026
  - Done 2026-11-18: K = 10 (p99 16.54 ms, the largest K with p99 ≤ 25 ms; K = 5 added to the set); table in `plan.md` and `docs/DECISIONES.md` §5.5.1. The output was saved as `specs/005-timeline/bench-linea-tiempo.txt` (name chosen by the group instead of `bench-despues-linea.txt`). Reaching it needed the R5 fallback: one scratch graph per service, reset between queries (`data/grafo_reutilizable.py`, `tests/test_grafo_reutilizable.py`).
- [X] T069 [US7] Test US7-1 in `tests/test_bench_linea_tiempo.py` (marked slow): at the chosen default K, 5 000 actions on `referencia`, p99 of the query set ≤ 50 ms, maximum printed; run it once at full size — FR-024, SC-006
  - Run 2026-11-18 at full size: K=10, p99 14.54 ms, worst 36.33 ms, mean 5.11 ms — passed.

**Checkpoint**: the benchmark runs headless and deterministic; the default K is a number derived from a table that is in `plan.md` and `docs/DECISIONES.md`.

## Phase 11: Part-one undo-history benchmark under the new load — §5.6 (US8)

**Goal**: repeat the part-one measurements with the timeline active, next to the part-one values.

### Tests (write first)

- [X] T070 [P] [US8] Add to `tests/test_bench_linea_tiempo.py`: `bench_historial` prints, for each scenario (`pequeño`, `larga`, `normal`, `grande`, `extremo`), the part-one figures (computed live without the timeline) next to the figures with the timeline active — action, undo, closures kept (max 5 frames) — plus a "capture checkpoint (µs)" column that replaces "copiar todo"; the part-one columns of the same run stay within a factor of 3 of `bench-antes.txt` (machine noise, not a regression test of the old numbers) — FR-027
  - Changed 2026-11-18 by the group: the factor-of-3 timing assertion was removed because it failed under load; the test keeps the structural checks, and the comparison with `bench-antes.txt` lives in the report (`bench-despues.txt`, `docs/DECISIONES.md` §5.6.2).

### Implementation

- [X] T071 [US8] Edit `bench/bench_historial.py`: run each scenario twice (`LineaTiempoPartida` absent / active, same seed, same actions); the benchmark drives `Partida` directly, so in the active run it creates the `LineaTiempoPartida` after the world is set up (`iniciar`) and calls `registrar_accion` after each `esperar_jugador` and `tras_retroceso` after each `retroceder`, exactly as `JuegoService` does, print the side-by-side table of `contracts/reporte-bench-linea-tiempo.md` ("Part one under the new load"); keep the original columns and their meaning — FR-027
- [X] T072 [US8] Run `python -m bench.bench_historial` and `python -m bench.bench_guardado` (the latter unchanged, only to show the 4-byte header change moves nothing, as agreed on 2026-11-18; no timeline section exists to compare); save both outputs as `specs/005-timeline/bench-despues.txt`; add the §5.6 table to `docs/DECISIONES.md` next to the part-one values, with the forward-vs-backward numbers of T066 — FR-027, FR-026
  - Done 2026-11-18 with K = 10: `bench_historial` run three times in a row (the run-to-run spread is as large as the timeline's added cost, so the table gives ranges), `bench_guardado` once (sizes identical to the baseline).

**Checkpoint**: §5.6 is repeated with the timeline active and shown next to the "before" values.

## Phase 12: Polish and cross-cutting

- [ ] T073 [P] Add `tests/test_linea_tiempo_estructura.py::test_modulos_sin_prohibidos`: scan `structures/linea_tiempo.py`, `model/registro_estado.py`, `model/reproduccion_logica.py`, `model/linea_tiempo_logica.py`, `model/efectos_omitidos.py`, `data/fabrica_reproduccion.py`, `service/historia_service.py` for imports of `heapq`, `bisect`, `collections`, `copy`, and for `dict(`, `{}` used as an index, `set(`; and check that no file under `model/` or `structures/` imports from `view/` or `controller/` — FR-028, FR-029, SC-001
- [ ] T074 [P] Add a layer test: with every class in `view/` patched to raise on construction, run `--replay ... --hasta` and `--bench` end to end (small sizes) — FR-016
- [ ] T075 [P] Add a determinism test: the same crypt, seed and commands run twice give identical timelines (vectors, checkpoints' records, ledger) and identical answers to a fixed query list, with and without interleaved queries — FR-009, SC-011
- [ ] T076 Run the quickstart (`specs/005-timeline/quickstart.md`) sections 1–8 against the real offline pack and fix what it shows; record the result at the end of `quickstart.md` — all FRs
- [ ] T077 Run `python -m pytest` and compare with the T002 reference: every old test still passes and the new ones pass; run `/speckit-analyze` (constitution Structures, Architecture and Process gates, every task cites an FR, every acceptance scenario has a test citing its FR) and fix findings — FR-028, FR-029, SC-001
- [ ] T078 Traceability check: build the table "acceptance scenario → test function" for US1-1…US8-5 and "FR-001…FR-029 → task" and add it to the end of this file; any scenario or FR without a test or task blocks the merge — SC-001

**Checkpoint**: all gates pass, results and the default K are recorded, and the table of traceability is complete.

## Dependencies and order

```text
Phase 1 Baseline
  └─ Phase 2 Foundations (structure, record, builder, stop bound)
       └─ Phase 3 Recording (US6)
            └─ Phase 4 Query (US1, US2)
                 └─ Phase 5 Scroll + ledger (US3)
                      └─ Phase 6 Command + DTO (US1, US2)
                           ├─ Phase 7 Replay --hasta (US4)
                           └─ Phase 8 Save v2 (US5)
                                └─ Phase 9 --checkpoint-cada (US6)
                                     └─ Phase 10 Benchmark + default K (US7, US8)
                                          └─ Phase 11 §5.6 rerun (US8)
                                               └─ Phase 12 Polish
```

Phases 7 and 8 both need Phase 6 and are independent of each other; if two people work in parallel they can take one each. Phase 9 needs Phase 8 because the saved K is what the option is compared with.

### Within-phase order

- Tests first, seeing them fail; then structures/model; then service; then controller/view/adapters; then wiring in `aplicacion.py` and `main.py`.
- T006 before T013; T008 before T022; T010 before T022; T021 before T022; T022 before T023; T030–T035 in order (T033 needs T030–T032; T035 needs T033); T043 before T044; T057 before T058.

### Parallel opportunities

- Phase 2: T005 ‖ T007 ‖ T009 (different test files); T006, T008, T010 after their tests.
- Phase 4: T017 ‖ T018 ‖ T019 (same area, different tests, no shared edit); T021 ‖ T016.
- Phase 5: T026 ‖ T027 ‖ T028.
- Phase 6: T037–T041 ‖ each other; T045 ‖ T043.
- Phase 7 ‖ Phase 8 after Phase 6.
- Phase 10: T063 ‖ T064; Phase 12: T073 ‖ T074 ‖ T075.

## Implementation strategy

- **MVP (first review)**: Phases 1–6 — recording, query by action and instant, scroll correctness, the command and its DTO. That is US1, US2, US3 and the core of US6, and it is what the oracle test protects.
- **Second increment**: Phase 7 (replay) and Phase 8 (save v2) — US4 and US5; they are independent.
- **Third increment**: Phases 9–11 — the option, the measurements, the default K and §5.6 — US6-6/7/8, US7, US8.
- **Stop conditions**: if the oracle (T020, T029, T042, T056) fails, no later phase starts; if T068 finds p99 > 50 ms on the reference world at every K, report to the group before choosing.
- Commit order (Constitution VII): `spec.md` is already committed; commit this `tasks.md` and the plan documents before the first code task; each phase is committed on its own.
