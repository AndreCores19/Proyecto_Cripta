---

description: "Task list for Hunter Enemy"
---

# Tasks: Hunter Enemy

**Input**: Design documents from `specs/002-hunter-enemy/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (monticulo, hunter-decision, catalog-hunter, room-view-hunter), quickstart.md

**Tests**: Required. Constitution IX says every acceptance scenario needs an automated test that cites its FR, and every task cites at least one FR. All tests use fake data built in the test (hand-built rooms, fake JSON, `tests/estado_fijo.py` doubles) and **no network**.

**Owner**: Emily owns this feature end to end and implements it with the agent. Tasks carry no per-task owner tag.

## Format: `[ID] [P?] [Story] Description — FR`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: user story from spec.md (US1–US7); phases without a story are shared groundwork
- Every test function's docstring MUST cite its FR and scenario (plus the Constitution principle where relevant), e.g. `"""FR-004 · US1-4"""`.
- Within a phase, write the tests first and run them: they must fail for the right reason before the implementation task, and pass after it.

## Path Conventions

Single-project layered layout at the repo root: `dto/`, `data/`, `model/`, `service/`, `controller/`, `view/`, `adapters/`, `structures/`, `bench/`, `tests/`.

## Test files

| File | Covers |
|---|---|
| `tests/test_monticulo.py` (new) | generic min-heap: order, ties, empty, `vaciar` |
| `tests/mapas_cazador.py` (new helper, not a test module) | fake crypt builders and the independent oracle (see "Common fixtures") |
| `tests/test_puertas.py` (existing) | `Salida.origen`, `Sala.entradas`, door epoch counter |
| `tests/estado_sin_cazadores.py`, `tests/capturar_estado_sin_cazadores.py` (new helpers, not test modules) | final state of seeded games without hunters, captured before any change |
| `tests/test_cazador_decision.py` (new) | `Busqueda`; US1, US2, hunter not activated (US5-4) |
| `tests/test_cazador_equivalencia.py` (new) | US3; modes agree with the oracle; cache rules; determinism |
| `tests/test_cazador_conocimiento.py` (new) | US4 |
| `tests/test_catalogo_cazador.py` (new) | `Enemigo.rango`, catalog reading, US5 |
| `tests/test_vista_cazador.py` (new) | US6 |
| `tests/test_bench_cazador.py` (new) | US7 |
| `tests/test_replay_cazador.py` (new) | record + replay a game with a hunter (FR-014, FR-021) |

## Common fixtures

**Model fixture** (all model tests): build `Sala`/`Salida` by hand and link them with `enlazar` (as `tests/test_puertas.py` and `tests/test_costos_salida.py` do). Create the player with `Jugador(vida_max=10**6, ataque=10, defensa=10**6, velocidad=100, inventario_max=10, sala=…)` and a hunter with `Enemigo(id_enemigo, tipo, nombre, vida, vida_max, ataque, defensa, velocidad, "cazador", sala, rango=…)`. Create the game with `Partida(jugador, semilla=1)`.

**Isolated hunter setup** (decision tests): before calling the method under test:
1. Put the player in the room named by the scenario, and the hunter in a different room.
2. Add the hunter with `partida.activar_enemigo(h)` and remove its activation turn with `partida.agenda.cancelar(h.evento)`.
3. Set `partida.reloj = T` and call `partida._actuar_enemigo(h)`.

Afterwards the hunter's only pending action is the one that call scheduled, so `h.evento.tiempo` and `h.sala` can be asserted.

**`tests/mapas_cazador.py`** (created in T013; imports only from `model/`, no test module):
- `cadena(costos)`: rooms 1..n+1 in a line, exit `E`/`O` between neighbours with the given costs; returns `(salas, salidas)`.
- `grilla(filas, columnas, costo)`: rows × columns rooms, ids row by row from 1, exits `N`/`S`/`E`/`O`, all with `costo`.
- `cripta_aleatoria(semilla, num_salas)`: `random.Random(semilla)` builds a connected crypt with costs from the values (1, 10, 50, 100, 250, 500, 1000), some one-way exits and some closed doors; returns the rooms.
- `distancias_referencia(salas, sala_jugador)`: the oracle. Plain lists, repeated relaxation until nothing changes: `dist[r] = min over open exits s of r: s.costo + dist[s.destino]`, with `dist[sala_jugador] = 0` and the rest infinite. No heap, no stamps, no limit, no `busq_*` fields.
- `decision_referencia(salas, sala_jugador, cazador)`: `None` if `dist[cazador.sala]` is infinite or greater than `cazador.rango`; otherwise the open exit `s` of `cazador.sala` with `s.costo + dist[s.destino] == d` and the lowest `(s.destino.id, s.direccion)`.

---

## Phase 1: Baseline before any code change

**Purpose**: save the "before" numbers and state. Nothing in this phase edits code. Every later task depends on it.

- [ ] T001 Check that `specs/002-hunter-enemy/spec.md` is committed (commit `3ad9823`) and that `git status` shows no change under `model/`, `structures/`, `data/`, `service/`, `dto/`, `view/`, `controller/`, `bench/` or `main.py`. Commit the plan artifacts (plan, research, data-model, contracts, quickstart, this file) in their own commit before any code, per Constitution VII — all FRs
- [ ] T002 Run `python -m pytest` on the unchanged code and note the result (expected: 115 passed). It is the "all green before" reference for Phase 3 and Phase 11 — FR-013, FR-014
- [ ] T003 [P] Run `python -m bench.bench_ciclo` three times on the unchanged code and save all three outputs, separated by a line `--- corrida N ---`, to `specs/002-hunter-enemy/bench-antes-ciclo.txt`. Do not edit the output — FR-017
- [ ] T004 [P] Run `python -m bench.bench_agenda` three times on the unchanged code and save all three outputs, separated by `--- corrida N ---`, to `specs/002-hunter-enemy/bench-antes-agenda.txt`. Do not edit the output — FR-017, FR-019
- [ ] T005 Capture the state of seeded games without hunters before any change — FR-013, FR-014 (SC-006):
  - Create `tests/estado_sin_cazadores.py` (helper, not a test module). `resumen(semilla)` builds `bench.bench_ciclo.armar_partida_costos(30, 50, semilla)`, turns the odd-numbered enemies into `"rastreador"` (`enemigo.comportamiento = "rastreador"`), plays 500 actions (every 5th is `esperar_jugador()`, the others `mover()` along the chain, turning around when there is no exit, like `_jugar` in `tests/test_costos_salida.py`) and returns one text: `reloj`, `acciones_jugador`, the player's room id and life, and one line `id sala vida` per enemy.
  - Create `tests/capturar_estado_sin_cazadores.py` (like `tests/capturar_salida_parte1.py`): writes the summaries for seeds 1, 2 and 3 to `specs/002-hunter-enemy/estado-sin-cazadores-antes.txt`. Run it now, on the unchanged code.

**Checkpoint**: the three baseline files exist and nothing else changed. Review before starting Phase 2.

---

## Phase 2: Generic min-heap

**Purpose**: the hand-written heap of [contracts/monticulo.md](./contracts/monticulo.md). It depends on nothing else and is reused by spec 003.

- [ ] T006 [P] Write `tests/test_monticulo.py`. Docstrings cite FR and the Constitution principle I/II — FR-003, FR-007, FR-014, FR-018:
  - extraction order equals a sorted list for 1000 seeded random integer priorities (`random.Random(5)`);
  - equal priorities come out in insertion order (insert 20 values with 3 distinct priorities and check the order);
  - tuple priorities `(2, 1)`, `(1, 9)`, `(1, 3)` come out as `(1, 3)`, `(1, 9)`, `(2, 1)`;
  - `extraer()` and `proximo()` on an empty heap return `None`; `len()` follows inserts and extracts;
  - `proximo()` does not remove;
  - `vaciar()` empties the heap and a second use gives the same order as a new heap (the insertion counter restarts);
  - a caller that needs a tie-break puts it in the priority: `(2, 7)`, `(2, 3)` come out as `(2, 3)`, `(2, 7)` whatever the insertion order;
  - the module imports neither `heapq`, `bisect` nor `collections` (read the source file text).
- [ ] T007 Implement `structures/monticulo.py`: class `MonticuloMinimo` with `insertar(prioridad, valor)`, `extraer()`, `proximo()`, `vaciar()`, `__len__`. Array-based binary heap; nodes hold `(prioridad, secuencia, valor)`; order by `prioridad` using only `<`, equal priorities by `secuencia`. No `heapq`, `bisect` or `collections`. Depends on T006 — FR-007, FR-014, FR-018
- [ ] T008 Run `python -m pytest tests/test_monticulo.py -v`; all green. Check with `grep -nE "heapq|bisect|collections|networkx|\bdict\(|\bset\(|\bfrozenset\(|\{\}|\{[^}]*:[^}]*\}" structures/monticulo.py` (review each hit by hand: f-strings and JSON parsing are not indexes) — FR-018

**Checkpoint**: Phase 2 can be reviewed alone: one new file and one new test file.

---

## Phase 3: Model groundwork for hunters

**Purpose**: the small model fields the search and the decision need ([data-model.md](./data-model.md)). No hunter behavior yet.

- [ ] T009 [P] Add tests to `tests/test_puertas.py` — FR-008, FR-011:
  - `agregar_salida` sets `salida.origen` to the room and appends the exit to `salida.destino.entradas` (a two-way connection gives each room one incoming exit; a one-way exit gives the destination room an incoming exit and the origin room none);
  - a new `Sala` has `busq_marca == -1` and `busq_dist == 0`;
  - assigning `salida.cerrada` (True or False) adds 1 to `Salida.epoca_puertas`; reading it does not;
  - `Partida.abrir_puerta` bumps the counter, and `Partida.retroceder()` right after (the rewind writes `cerrada` back through the history) bumps it again.
- [ ] T010 [P] Add tests to `tests/test_catalogo_cazador.py` (new file): `Enemigo(..., "cazador", sala, rango=300).rango == 300`; the default `rango` is 0; `es_cazador()` is True for `"cazador"` and False for `"errante"`, `"rastreador"` and `"guardián"` — FR-001
- [ ] T011 In `model/sala_logica.py`: `Salida.origen` (set by `Sala.agregar_salida`), `Sala.entradas` (list, filled by `agregar_salida` with `salida.destino.entradas.append(salida)`), `Sala.busq_marca = -1`, `Sala.busq_dist = 0`, and `Salida.cerrada` as a property over `_cerrada` whose setter adds 1 to the class attribute `Salida.epoca_puertas` (starts at 0). In `model/enemigo_logica.py`: `Enemigo(..., suelta=None, rango=0)` and `es_cazador()` (`comportamiento == "cazador"`). Depends on T009, T010 — FR-001, FR-008, FR-011
- [ ] T012 Run the whole suite (`python -m pytest`): the 115 tests of T002 plus the new ones are green. A failure in an old test means the `cerrada` property or `agregar_salida` change broke part-one behavior; fix it before going on. Also run `tests/estado_sin_cazadores.resumen(semilla)` for seeds 1, 2 and 3 and compare each with the block saved in `specs/002-hunter-enemy/estado-sin-cazadores-antes.txt` (T037 automates the same check later): they must be identical now, because Phase 3 touches `Salida` and `Sala` — FR-013, FR-014

**Checkpoint**: Phase 3 can be reviewed alone; no behavior changes in the game.

---

## Phase 4: User Story 1 — The hunter chases the player when within range (Priority: P1)

**Goal**: a hunter attacks, waits or moves one step along the cheapest route according to FR-002 to FR-006.

**Independent Test**: build the small crypts below, run one hunter turn and check attack, wait or move.

- [ ] T013 [P] [US1] Write the helper `tests/mapas_cazador.py` as described in "Common fixtures" (`cadena`, `grilla`, `cripta_aleatoria`, `distancias_referencia`, `decision_referencia`). Create `tests/test_cazador_equivalencia.py` with a first self-check section: the oracle gives `dist` 0, 100 and 250 for a chain with costs 100 and 150 and the player at the end — FR-003, FR-011
- [ ] T014 [P] [US1] Write `tests/test_cazador_decision.py`, part `Busqueda` (needs T011; fails until T020):
  - rooms farther than the limit are not reached: in a chain with costs 100, 100, 100 and the player at one end, `calcular(sala_jugador, 200)` gives `busq_marca == estampa` for the first three rooms and leaves the fourth room at `-1`;
  - a room exactly at the limit (distance 200 with limit 200) is reached, one at 201 is not;
  - closed exits are not crossed;
  - a one-way exit `A→B` (no exit back) gives `distancia(A) == cost` when the player is in `B`, and `distancia(B)` is `None` when the player is in `A`;
  - two successive searches give different stamps, and `Busqueda.ultima_estampa` equals the latest one even when two `Busqueda` objects alternate;
  - a search never writes `busq_*` on a room outside the reached region — FR-018, FR-003, FR-009
- [ ] T015 [P] [US1] In `tests/test_cazador_decision.py` add US1-1: hunter and player in the same room (`cadena([100])`, both in room 1): `_actuar_enemigo` attacks (a bitácora line contains `ataca`, the player lost life, the hunter's room is unchanged). Docstring `FR-002 · US1-1` — FR-002
- [ ] T016 [P] [US1] In `tests/test_cazador_decision.py` add US1-2, US1-3 and US1-4 on `cadena([100, 150])` (rooms A=1, B=2, C=3), player in C, hunter in A, clock T=1000, speed 100: with `rango` 300 the hunter ends in B (`d` = 250); with `rango` 250 it also ends in B (`d == rango` moves); with `rango` 200 it stays in A and its next action is at T + 100. Docstrings `FR-003, FR-005 · US1-2`, `FR-004, FR-005 · US1-3`, `FR-004 · US1-4` — FR-003, FR-004, FR-005
- [ ] T017 [P] [US1] In `tests/test_cazador_decision.py` add US1-5: hunter in A, player in C, the exit `A→B` is closed (`cerrada=True` with `llave`), no other route: the hunter waits (stays in A, next action T + 100) and the door is still closed afterwards; with the door open it moves. Docstring `FR-004, FR-009 · US1-5` — FR-004, FR-009
- [ ] T018 [P] [US1] In `tests/test_cazador_decision.py` add US1-6: hunter in A, player in C, direct exit `A→C` cost 500, route `A→B` cost 100 and `B→C` cost 100, `rango` 300: the hunter moves to B (`d` = 200, not the 500 exit). Docstring `FR-003, FR-005 · US1-6` — FR-003, FR-005
- [ ] T019 [P] [US1] In `tests/test_cazador_decision.py` add US1-7: hunter with speed 50 in A, exit `A→B` with `costo` 120, player in B's neighbour so the route is that exit, `rango` ≥ 120, clock T=700: after the turn the hunter is in B at once, its next action is at T + 240, and a bitácora line says it moves (it went through `_programar_movimiento`: wrap that method and check it was called once with that exit). Add a second case for the speed-change edge case (spec 001 FR-009, Appendix B): hunter speed 50, exit `costo` 500, move at T=0 so the next action is at 1000; set `partida.reloj = 400` and call `partida.efectos.aplicar_velocidad(hunter, +50, 10**6)` (speed becomes 100): the pending action is now at `400 + max(1, (1000 - 400) * 50 // 100)` = 700. Docstring `FR-006, FR-009 · US1-7` — FR-006
- [ ] T020 [US1] Create `model/ruta_cazador.py` with `Busqueda` as in plan §The search: class counter `ultima_estampa` and `nueva_estampa()` shared by all instances, `calcular(origen, limite)` (backwards over `Sala.entradas`, stop when the popped distance exceeds `limite`, never insert `nd > limite`, stale entries skipped, uses `MonticuloMinimo`), `distancia(sala, estampa)` (`busq_dist` if `busq_marca == estampa` else `None`) and a `busquedas` counter. Depends on T007, T011, T014 — FR-003, FR-009, FR-018
- [ ] T021 [US1] In the same file add `DecisorCazador(modo="individual")` with `decidir(partida, cazador, limite_forzado=None)` (`limite_forzado` is for tests only): limit = `limite_forzado` if given, else `cazador.rango`; search; `d = distancia(cazador.sala)`; `None` when unreached or `d > rango`; otherwise the open exit `s` of `cazador.sala` with `s.costo + distancia(s.destino) == d` and the lowest `(s.destino.id, s.direccion)`. Raise `RuntimeError` if the limit used is smaller than `cazador.rango`. In `model/partida_logica.py` add `self.decisor_cazador = DecisorCazador("individual")` in `__init__`, `_decidir_cazador(enemigo)`, and the branch `elif enemigo.comportamiento == "cazador": salida = self._decidir_cazador(enemigo)` next to the `errante` and `rastreador` branches. Movement and waiting stay in the existing code (`_programar_movimiento`, wait branch). Depends on T015–T020 — FR-002, FR-003, FR-004, FR-005, FR-006, FR-009
- [ ] T022 [US1] Run `python -m pytest tests/test_cazador_decision.py tests/test_puertas.py tests/test_monticulo.py -v` and then the whole suite; all green. check with `grep -nE "heapq|bisect|collections|networkx|\bdict\(|\bset\(|\bfrozenset\(|\{\}|\{[^}]*:[^}]*\}" model/ruta_cazador.py` (review each hit by hand: f-strings and JSON parsing are not indexes) that it has no hit, and that it imports only `structures/monticulo` — FR-018

**Checkpoint**: Phase 4 is an MVP: a hunter chases within its `rango`. Review it alone.

---

## Phase 5: User Story 2 — Ties between routes are broken by room id (Priority: P1)

**Goal**: the same room, state and `rango` always give the same exit.

**Independent Test**: crypts with equal-cost alternatives.

- [ ] T023 [P] [US2] In `tests/test_cazador_decision.py` add US2-1: hunter in room `u` (id 5) with open exits to B (id 7, `cost(u,B)` = 100, `dist(B,player)` = 200) and D (id 3, `cost(u,D)` = 200, `dist(D,player)` = 100); `rango` 400: `d` = 300 for both and the hunter moves to D. Build it by hand with the ids given. Docstring `FR-007 · US2-1` — FR-007
- [ ] T024 [P] [US2] In `tests/test_cazador_decision.py` add US2-2: neighbour of id 1 with `cost + dist` = 400 and neighbour of id 7 with 300 (= `d`): the hunter moves to the room of id 7. Docstring `FR-007 · US2-2` — FR-007
- [ ] T025 [P] [US2] In `tests/test_cazador_decision.py` add US2-3: `grilla(3, 3, 100)`, hunter in room 1 (top-left), player in room 9 (bottom-right), `rango` 1000: the hunter moves to room 2 (the lowest id among neighbours 2 and 4, both on routes of cost `d` = 400). Repeat on `grilla(4, 4, 100)` (`d` = 600) and on the same grid with one cost changed to 50 so a single neighbour is on a cheapest route. Docstring `FR-007 · US2-3` — FR-007
- [ ] T026 [P] [US2] In `tests/test_cazador_decision.py` add the assumption case of the spec: two exits `N` and `E` of the hunter's room lead to the same neighbour with the same cost: the hunter takes the one with the lowest direction name (`E` before `N`), whatever the order in `Sala.salidas`; run it with both orders. Docstring `FR-007, FR-014 · Assumptions` — FR-007, FR-014
- [ ] T027 [US2] Run the new tests. If one fails, fix the choice in `DecisorCazador.decidir` (`model/ruta_cazador.py`); no other file changes. Then run the whole suite — FR-007

**Checkpoint**: Phase 5 only adds tests and, at most, a fix in one function.

---

## Phase 6: User Story 3 — The hunter always decides from the current state (Priority: P1)

**Goal**: every mode decides exactly like a fresh computation, whatever changed since the previous turn.

**Independent Test**: change the state between two turns and compare with the oracle.

- [ ] T028 [P] [US3] Add to `tests/test_cazador_equivalencia.py` (created in T013), part scenarios. Each test runs the same steps for the three modes (`pytest.mark.parametrize("modo", …)`, building the decider with `DecisorCazador(modo)` and assigning `partida.decisor_cazador`) and compares the exit with `decision_referencia`. Docstrings cite FR and scenario — FR-011, FR-012:
  - US3-1 (`FR-011, FR-012`): hunter in A, rooms A–B–C and an alternative route A–D–C. Turn 1 moves it along A→B; then door `B–C` closes (`partida._poner_cerrada(salida, True)`) and the hunter is back in A: turn 2 takes the alternative route if its cost ≤ `rango`; with no alternative it waits;
  - US3-2 (`FR-011, FR-012`): the hunter waited because every route went through a closed door; the door opens (`_poner_cerrada(…, False)`), the player is within `rango`: it moves along the route using that door;
  - US3-3 (`FR-011, FR-012`): after one move toward room C, the player moves to room D (`partida.mover`); the next decision uses D;
  - US3-4 (`FR-011`): a wanderer dies between two hunter turns (`partida.atacar` on a wanderer with 1 life); the decision equals that of a new identical hunter in the same state;
  - US3-5 (`FR-011, FR-012`): the player opens with a key a door with `cierre_automatico` 100 that the hunter's route uses; after the clock passes the closing event the next decision treats the door as closed.
- [ ] T029 [P] [US3] In `tests/test_cazador_equivalencia.py` add the seeded random comparison (`FR-011`, SC-002): for seeds 1–20, `cripta_aleatoria(seed, 40)`, 6 hunters with random `rango` among the values (0, 100, 300, 1000) and a player; 200 steps, each step doing one of: `_poner_cerrada` on a random door, the player moves (`mover` on a random open exit), a random enemy is removed, `partida.retroceder()` when the history has a frame; after each step, for every hunter and every mode, the decision equals `decision_referencia`. Two more checks in the same test: (a) **doors untouched by hunters** (SC-003, FR-009): snapshot `[s.cerrada for every exit of every room]` before and after each hunter turn (`partida._actuar_enemigo(h)`) and require them equal; (b) **order independence** (Constitution II, FR-007): for each seed, rebuild the same crypt a second time with `Sala.salidas` and `Sala.entradas` of every room reordered by a seeded shuffle (`random.Random(seed + 1000).shuffle`), run the same steps, and require every decision to name the same destination room and direction as in the unshuffled run — FR-011, FR-012, FR-009, FR-007
- [ ] T030 [P] [US3] In `tests/test_cazador_equivalencia.py` add the cache rules of mode `compartido` — FR-011, FR-018:
  - a second hunter with a **larger** `rango` than the one that filled the cache asks next: the cache is recomputed (`busqueda.busquedas` grows by 1) and the decision equals the oracle;
  - a hunter with a **smaller or equal** `rango` asks after another with a larger one: no new search;
  - `decidir` raises `RuntimeError` when the cache is forced to a smaller limit than the asking hunter's `rango` (call `decisor.decidir(partida, cazador, limite_forzado=cazador.rango - 1)` with a hunter whose `rango` is at least 1);
  - an unrelated search is run between two hunter turns (`Busqueda().calcular(otra_sala, 500)` using another `Busqueda` object): the next decision equals the oracle and costs one new search (condition 4 of the cache check);
  - a rewind (`retroceder()`) between two turns invalidates the cache;
  - with no change between two turns, `compartido` runs 0 new searches while `individual` and `compartido_sin_reuso` run 1 each.
- [ ] T031 [P] [US3] In `tests/test_cazador_equivalencia.py` add determinism (`FR-014`, SC-005): the same seeded crypt, hunters and action sequence of 300 actions run twice with each mode give the same final state (clock, rooms, life of the player and of every enemy); the three modes give the same final state as one another — FR-014
- [ ] T032 [US3] In `model/ruta_cazador.py` add the modes `"compartido_sin_reuso"` and `"compartido"` to `DecisorCazador` as in plan §The decider: limit = `max(cazador.rango, largest rango among living active hunters in partida.enemigos)`; mode `compartido` keeps `sala_jugador`, `epoca`, `limite`, `estampa` and reuses the search only while the four conditions of data-model.md hold, otherwise recomputes (never extends). Unknown mode names raise `ValueError`. Depends on T028–T031 — FR-011, FR-012, FR-018
- [ ] T033 [US3] Run `python -m pytest tests/test_cazador_equivalencia.py -v` and the whole suite; all green. Run the random comparison with seeds 1–200 once by hand (change the range temporarily) and keep the range at 20 — FR-011

**Checkpoint**: Phase 6 can be reviewed alone: one new module section and one test file. It carries the "observable equivalence" guarantee.

---

## Phase 7: User Story 4 — The hunter knows the whole map (Priority: P1)

**Goal**: no decision depends on fog of war or on downloaded content.

**Independent Test**: the same game with rooms empty or fully populated, and a service run with a fake factory.

- [ ] T034 [P] [US4] Write `tests/test_cazador_conocimiento.py` — FR-008, FR-010:
  - US4-1 (`FR-008`): the hunter's route crosses rooms with `rastro is None` (never visited by the player); the hunter moves along it. Docstring `FR-008 · US4-1`;
  - US4-2 (`FR-010`): the same crypt twice, once with every room having objects, traps and inactive enemies (content "downloaded") and once with empty rooms (`objetos`, `trampas`, `inactivos` all empty): the decision is the same in both, for each mode. Docstring `FR-010 · US4-2`;
  - US4-3 (`FR-010, FR-014`): the same seeded game (crypt, seed and 200 actions) run twice, once with content in every room and once with none: the sequence of bitácora lines that mention the hunters and the final state are identical. Docstring `FR-010, FR-014 · US4-3`;
  - US4-4 (`FR-008`): build the rooms through `RepositorioCripta.construir_salas` from fake `SalaDTO`/`SalidaDTO` objects with `costo` (as `tests/test_costos_datos.py` does), no network; a hunter on those rooms takes the route that uses those costs. Docstring `FR-008 · US4-4`;
  - Constitution V (`FR-010`): with `JuegoService` and the `FabricaFalsa` of `tests/estado_fijo.py` on a crypt with a hunter far from the player, the hunter's moves never add its destination room to `fabrica.pobladas`; only the player's moves do.
- [ ] T035 [US4] Run the tests. If one fails, find the read of room content or `rastro` in `model/ruta_cazador.py` or in the `cazador` branch of `Partida` and remove it. Then run the whole suite — FR-010

**Checkpoint**: Phase 7 is tests plus, at most, a removal.

---

## Phase 8: User Story 5 — Hunters come from the catalog; other enemies do not change (Priority: P2)

**Goal**: a catalog entry defines a hunter; nothing changes for wanderers and trackers; a hunter not yet activated does nothing.

**Independent Test**: fake catalog JSON, no network.

- [ ] T036 [P] [US5] In `tests/test_catalogo_cazador.py` add — FR-001, FR-015:
  - US5-1: `ficha_desde_json({... "comportamiento": "cazador", "rango": 400 ...})` gives a `FichaEnemigoDTO` with `rango == 400`; `FabricaModelo.crear_enemigo(None, instancia, ficha, sala)` (the method uses nothing from `self`, so `None` stands in for it; `instancia` is `types.SimpleNamespace(instancia="h1", tipo="ent_lobo", vida=None)`) gives an `Enemigo` that is a hunter with `rango` 400. Docstring `FR-001 · US5-1`;
  - US5-5: an entry with `"comportamiento": "cazador"` and no `rango` gives `rango == 0`; the resulting enemy with the player one exit away waits (stays, next action at T + 100), and attacks when it shares the player's room. Docstring `FR-001, FR-002, FR-004 · US5-5`;
  - an entry with `rango` and behavior `"errante"` keeps `rango` on the enemy but moves with the wanderer rule (FR-013);
  - nothing about a particular crypt or entry is hardcoded: the factory takes `rango` only from the entry (`FR-015`).
- [ ] T037 [P] [US5] In `tests/test_catalogo_cazador.py` add US5-2 (`FR-013, FR-014`, SC-006): `tests/estado_sin_cazadores.resumen(semilla)` for seeds 1, 2, 3 on the current code equals the text saved in `specs/002-hunter-enemy/estado-sin-cazadores-antes.txt` (T005). Docstring `FR-013 · US5-2` — FR-013, FR-014
- [ ] T038 [P] [US5] In `tests/test_catalogo_cazador.py` add US5-3 (`FR-013`): one room graph with a hunter, a wanderer and a tracker; in one turn each: the wanderer's exit is the one `_decidir_errante` returns for the seeded `partida.azar`, the tracker's the one `_decidir_rastreador` returns, and the hunter's the one `decision_referencia` returns. Docstring `FR-013 · US5-3` — FR-013
- [ ] T039 [P] [US5] In `tests/test_cazador_decision.py` add US5-4 (`FR-022`): a hunter placed in `sala.inactivos` of a room away from the player, `rango` 1000 and the player within range: after 10 player actions it has not moved or attacked and has no pending event; the player then enters its room (`partida.mover`) and the hunter is activated; from its next turn on it decides as in US1. Docstring `FR-022 · US5-4` — FR-022
- [ ] T040 [US5] In `dto/ficha_dto.py` add `rango` to `FichaEnemigoDTO` (`__init__(…, regeneracion=0, rango=None)`: `self.rango = rango if rango is not None else 0`) and `rango=datos.get('rango')` in `desde_json`; no range or type check. In `data/fabrica_modelo.py` pass `rango=ficha.rango` in `crear_enemigo` (use `getattr(ficha, "rango", 0)` as `regeneracion` does). Depends on T036 — FR-001, FR-015
- [ ] T041 [US5] Run `python -m pytest tests/test_catalogo_cazador.py tests/test_cazador_decision.py -v` and the whole suite; all green. If US5-2 differs from the saved file, the feature changed part-one behavior: find and fix the cause — do not regenerate the file — FR-013

**Checkpoint**: Phase 8 can be reviewed alone: two small production files plus tests.

---

## Phase 9: User Story 6 — The player can tell hunters apart (Priority: P2)

**Goal**: the room view marks hunters; rooms without hunters print as before.

**Independent Test**: `estado_vista()` and `VistaConsola.mostrar_estado` on a fixed state.

- [ ] T042 [P] [US6] Write `tests/test_vista_cazador.py` — FR-016:
  - US6-1: a room with a hunter and a wanderer, built with `armar_estado_fijo()` from `tests/estado_fijo.py` plus two `Enemigo` objects added to `partida.enemigos` in the player's room: `servicio.estado_vista().enemigos` has `cazador == True` for the hunter and `False` for the wanderer; `VistaConsola().mostrar_estado(estado)` prints `  Lobo (cazador) [id] (Vida: v/vm)` for the hunter and the part-one line for the wanderer (capture with `capsys`). Docstring `FR-016 · US6-1`;
  - US6-2: with only a wanderer and a tracker in the room, the printed text equals `cargar_golden("estado.txt")`-style output of the same state without any `(cazador)`; the existing `tests/test_vista_costos.py` golden tests stay unchanged and green. Docstring `FR-016, FR-013 · US6-2`;
  - `EnemigoVistaDTO("Rata", "r1", 5, 10, [])` still works (default `cazador=False`);
  - `enemigos_en_sala()` also fills the field; the view never receives an `Enemigo` (the `EstadoVistaDTO` has no model reference).
- [ ] T043 [US6] In `dto/estado_vista_dto.py` add `cazador=False` to `EnemigoVistaDTO`. In `service/juego_service.py` pass `e.es_cazador()` in `estado_vista` and `enemigos_en_sala`. In `view/vista_consola.py` print `(cazador)` right after the name for a hunter (see [contracts/room-view-hunter.md](./contracts/room-view-hunter.md)); other enemies print exactly as before. `view/vista_silenciosa.py` is unchanged. Depends on T042 — FR-016
- [ ] T044 [US6] Run `python -m pytest tests/test_vista_cazador.py tests/test_vista_costos.py tests/test_frontera_servicio.py -v` and the whole suite; all green (the part-one golden files did not change) — FR-016, FR-013

**Checkpoint**: Phase 9 can be reviewed alone: three small production files plus one test file.

---

## Phase 10: User Story 7 — Hunters do not slow the game down (Priority: P2)

**Goal**: benchmarks that prove FR-017 to FR-021, and the choice of the default mode.

**Independent Test**: run the benchmarks; read the tables.

- [ ] T045 [P] [US7] Write `tests/test_bench_cazador.py` with tiny sizes passed as arguments (3 rooms to 30, 3 to 6 hunters, 20 actions) so that it runs in seconds — FR-017 to FR-021:
  - US7-1 (`FR-017`): `bench_ciclo.ejecutar()` (with the scenarios list monkeypatched to small `cazadores` and `cazadores_rango_total` scenarios, tuples `(nombre, salas, enemigos, cazadores)`) prints a line for each of the two hunters scenarios (`cazadores` and `cazadores_rango_total`) that has the average, the p99 and the worst cycle, and the verdict word; a scenario with p99 exactly 20.0 ms is `cumple` (the verdict uses `<=`);
  - US7-2 (`FR-018`): `bench_cazador.escalado(salas_chicas, salas_grandes, rango, semilla)` returns the two decision times and their ratio; both crypts have an identical region within `rango` (assert it by comparing the rooms reached by `Busqueda.calcular` in both);
  - US7-3 (`FR-019`): `bench_cazador.ejecutar(pequeno=True)` prints the four comparisons (one hunter vs many; small vs large `rango`; per hunter vs shared; reuse vs recompute) and, for the last two, a row for doors changing often and a row for doors almost never changing;
  - US7-4 (`FR-019, FR-011`): the function that runs one seeded action list in the three modes returns the same list of hunter decisions for all three, and the benchmark raises if they differ (force a difference with a fake mode in the test and check it raises);
  - US7-5 (`FR-020`): `bench_cazador.armar_cripta(semilla, salas, cazadores)` called twice with the same seed gives the same rooms, exits, costs, closed doors and hunters (compare id, direction, destination, cost, `cerrada`, `rango` lists); a different seed gives a different crypt;
  - US7-6 (`FR-021`): in a subprocess (`subprocess.run([sys.executable, "-I", "-c", …])`) import `bench.bench_ciclo` and `bench.bench_cazador`, run the small benchmark and print `any(name.startswith("view") for name in sys.modules)`; it is `False`. Also `grep -rn "Vista" bench/` finds nothing.
- [ ] T046 [US7] In `bench/bench_ciclo.py` add `armar_partida_cazadores(num_salas, num_enemigos, num_cazadores, semilla)`: same room chain and cost set as `armar_partida_costos`, `num_enemigos - num_cazadores` wanderers and `num_cazadores` hunters with `rango` drawn from the values (100, 300, 1000) by `random.Random(semilla)`; extend each `ESCENARIOS` entry to `(nombre, salas, enemigos, cazadores)` with `cazadores` = 0 for `normal`, `grande` and `extremo`, and make `ejecutar` call `armar_partida_cazadores` when `cazadores > 0` and `armar_partida` otherwise; add the scenarios `("cazadores", 100, 300, 30)` and `("cazadores_rango_total", 100, 300, 30)` (same crypt, every hunter's `rango` = 1000000, so decisions can reach the whole crypt); change the verdict for the **whole file** from `p99 < LIMITE_MS` to `p99 <= LIMITE_MS` (one convention for every scenario, as the spec says "at most 20 ms"): the single `veredicto` line in `ejecutar` and the closing text `Limite: … (veredicto sobre el percentil 99)`, which now says `p99 <= 20 ms`. Do not make this edit before T003 has saved the baseline. Depends on T045 — FR-017, FR-020
- [ ] T047 [US7] Create `bench/bench_cazador.py` with `ejecutar()`, `armar_cripta(semilla, salas, cazadores)` and `escalado(...)` as in plan §Measurements items 2 and 3: the four FR-019 comparisons (one hunter vs many with 1, 10, 30, 100 hunters; small vs large `rango` 200 vs 5000 on 100 and 1000 rooms; per hunter vs shared vs shared without reuse and reuse vs recompute, each with doors changing every player action and every 500); doors change through `Partida._poner_cerrada` with a seeded RNG; each cell prints microseconds per player action (average of 3000) and the number of searches; before timing, all modes run the same action list and the program raises if any hunter decision differs. Imports nothing from `view/`. Depends on T032, T046 — FR-018, FR-019, FR-020, FR-021
- [ ] T048 [US7] In `main.py` add `bench_cazador` to the `--bench` import and to the loop of modules. Check with `grep -rn "Vista" bench/` that nothing from `view/` is used — FR-021
- [ ] T049 [US7] Extend `bench/bench_agenda.py` for section 5.6 — FR-017, FR-019: add `contar_operaciones_cazadores(acciones, num_enemigos, num_cazadores)` on `armar_partida_cazadores` (programar/extraer/cancelar/reprogramar per player action and the maximum number of pending events), run with 300, 1000 and 3000 enemies with 30 hunters, and with 10% hunters; print it next to the wanderers-only run. The three part-one candidates (`AgendaHeap`, `AgendaListaSinOrdenar`, `AgendaListaOrdenada`) are re-run with the variable-increment model in the same output. Depends on T046
- [ ] T050 [US7] Run `python -m pytest tests/test_bench_cazador.py -v`; all green — FR-017 to FR-021
- [ ] T051 [US7] Run `python -m bench.bench_ciclo` and save to `specs/002-hunter-enemy/bench-despues-ciclo.txt`. Run it two more times (three runs, as in T003). Check: the `cazadores` and `cazadores_rango_total` scenarios have p99 <= 20 ms and the maximum is printed (SC-007); the `normal`, `grande` and `extremo` scenarios keep p99 <= 20 ms (part-one criterion). Compare their average with the best of the three runs in `bench-antes-ciclo.txt`: more than 10% slower is an **investigation trigger, not an acceptance gate**; write the cause (likely the `Salida.cerrada` property or the `agregar_salida` change) in this task's note and decide whether to act — FR-017
- [ ] T052 [US7] Run `python -m bench.bench_cazador`; save the output to `specs/002-hunter-enemy/bench-cazador.txt` — FR-018, FR-019
- [ ] T053 [US7] Run `python -m bench.bench_agenda` and save it to `specs/002-hunter-enemy/bench-agenda-cazadores.txt` (three runs) and `bench-despues-agenda.txt` — FR-017, FR-019
- [ ] T054 [US7] Fill the §Measurements table of `specs/002-hunter-enemy/plan.md` with the numbers from T051–T053 and apply the written decision rules: (a) default hunter mode (`compartido` if it is the fastest or within 10% of the fastest in every row of the comparisons and the p99 and scaling criteria pass; otherwise the fastest mode that passes; if none passes, stop and reopen the plan in a separate commit); (b) the agenda decision of section 5.6 (keep the binary heap if it is the fastest or within 10% at every size ≥ 300; otherwise reopen it in a separate commit). Depends on T051–T053 — FR-017, FR-018, FR-019
- [ ] T055 [US7] Set the chosen mode as the default in `Partida.__init__` (`DecisorCazador(<mode>)`), keeping the other two modes in the code. Re-run `python -m pytest` — FR-011, FR-019

**Checkpoint**: Phase 10 can be reviewed alone: benchmark code, saved outputs and the filled table.

---

## Phase 11: Polish & cross-cutting

- [ ] T056 [P] Write `tests/test_replay_cazador.py` (FR-014, FR-021, Constitution III): record a game on a crypt with a hunter (rooms built by hand, `FabricaFalsa` from `tests/estado_fijo.py`, `Controlador.ejecutar` with `VistaSilenciosa` and a `BitacoraPartida(tmp_path)` as in `tests/test_replay_costos.py`), then replay the log with `Controlador(servicio, None, None, None)` on rebuilt rooms and the seed from `LectorBitacora`; `resumen_final()` and `estado_vista()` are equal. Also check that no class defined in `view/` is instantiated during the replay (monkeypatch the constructors as `tests/test_salida_replay.py` does) — FR-014, FR-021
- [ ] T057 Constitution gate, limited to what this feature adds (`structures/monticulo.py`, `model/ruta_cazador.py`, the changes in `model/sala_logica.py`, `model/enemigo_logica.py`, `model/partida_logica.py`, `dto/`, `data/fabrica_modelo.py`, `service/juego_service.py`, `view/vista_consola.py`, `bench/`) — FR-014, FR-018, FR-021:
  - none uses `dict`, `set`, `heapq`, `bisect`, `collections`, `networkx` or another graph library (`grep -nE "heapq|bisect|collections|networkx|\bdict\(|\bset\(|\bfrozenset\(|\{\}|\{[^}]*:[^}]*\}" <files>` (review each hit by hand: f-strings and JSON parsing are not indexes)); the auxiliary structures are `MonticuloMinimo`, lists and integer fields;
  - `model/` and `structures/` import nothing from `view/`, `controller/` or the view DTO modules;
  - `grep -rn "Vista" bench/` finds nothing, and `--replay` creates no `view/` class (T056);
  - `structures/agenda.py` is unchanged (`git diff --stat structures/agenda.py` is empty);
  - the hunter moves only through `_programar_movimiento` (`grep -n "_programar_movimiento" model/partida_logica.py`).
- [ ] T058 Run the whole suite, `python -m pytest`; all green. Compare the count with T002 (115) plus the new tests — FR-013, FR-014
- [ ] T059 Manual check from `quickstart.md` — FR-016, FR-004, FR-014: run `python main.py` on a crypt that has a hunter and `python main.py --replay <log>` on its log, and report exactly what could be checked. If the service has no crypt with a hunter yet, report that only the automated tests cover it
- [ ] T060 Add a note to this file under T059 saying what was checked and what was not, and update `specs/002-hunter-enemy/checklists/requirements.md` only if a spec correction was needed (a spec correction goes in its own commit before the code that depends on it) — all FRs

---

## Dependencies & Execution Order

```text
Phase 1 (T001–T005)  baseline: nothing else may start before T003–T005 are saved
→ Phase 2  heap          T006 → T007 → T008
→ Phase 3  groundwork    T009, T010 → T011 → T012
→ Phase 4  US1 (MVP)     T013–T019 → T020 → T021 → T022
→ Phase 5  US2           T023–T026 → T027
→ Phase 6  US3           T028–T031 → T032 → T033
→ Phase 7  US4           T034 → T035
→ Phase 8  US5           T036–T039 → T040 → T041
→ Phase 9  US6           T042 → T043 → T044
→ Phase 10 US7           T045 → T046 → T047 → T048; T049 (after T046)
                         T050 → T051, T052, T053 → T054 → T055
→ Phase 11 polish        T056, T057 → T058 → T059 → T060
```

- Phase 2 depends only on Phase 1. Phase 3 depends on Phase 1. Phase 4 needs Phases 2 and 3.
- Phases 5, 6 and 7 add tests to the decision of Phase 4; Phase 6 also edits `model/ruta_cazador.py` (modes), so it comes before Phase 10.
- Phase 8 (T040) edits `dto/ficha_dto.py` and `data/fabrica_modelo.py`, independent of Phases 5–7; it can run in parallel with them if two sessions work in different files.
- Phase 9 edits `dto/estado_vista_dto.py`, `service/juego_service.py`, `view/vista_consola.py`; independent of Phases 5–8 once Phase 3 is done (needs `Enemigo.es_cazador`).
- Phase 10 needs Phase 6 (all three modes) and Phase 8 (catalog data is not used by the benchmark, but the hunters scenario builds `Enemigo` directly).
- Edits to the same file are sequential: `model/ruta_cazador.py` (T020 → T021 → T032), `model/partida_logica.py` (T021 → T055), `tests/test_cazador_decision.py` (T014 → T015 → … → T039), `tests/test_cazador_equivalencia.py` (T013 → T028 → T029 → T030 → T031), `tests/test_catalogo_cazador.py` (T010 → T036 → T037 → T038).
- `[P]` marks tasks that touch different files with no unfinished dependency; with one implementer they can be done in any order inside their phase.

### Parallel examples

```text
Phase 1:  T003 ∥ T004 (different outputs) → T005
Phase 3:  T009 ∥ T010 (different test files)
Phase 4:  T013 ∥ T014 ∥ T015 ∥ T016 ∥ T017 ∥ T018 ∥ T019  (write the tests; same file, so one session
          at a time, or split between sessions and merge)
Phase 8 ∥ Phase 9 after Phase 4 (different production files)
```

## Implementation Strategy

1. **Phase 1 first.** The "before" benchmark outputs and the seeded state file are taken on the unchanged code.
2. **Heap** (Phase 2), reviewed on its own.
3. **Groundwork and MVP** (Phases 3–4): the hunter chases within its `rango` with the simplest mode (`individual`).
4. **Correctness** (Phases 5–7): tie-break, state changes and knowledge tests; the shared modes in Phase 6.
5. **Catalog and view** (Phases 8–9), then **benchmarks and the default mode** (Phase 10), then polish (Phase 11).
6. Commit per phase; a spec correction always goes in its own commit before the code that follows it (Constitution VII). Review each phase's checkpoint before starting the next.
7. **Scenario coverage** (Constitution IX): US1-1…7 → T015–T019; US2-1…3 → T023–T025; US3-1…5 → T028; US4-1…4 → T034; US5-1…5 → T036, T037, T038, T039; US6-1…2 → T042; US7-1…6 → T045.
8. **Assignment Appendix B** (Constitution IX), terrain and hunter cases → scenarios and tests (full table in [quickstart.md](./quickstart.md)): no open route → US1-5 (T017); route cost above `rango` → US1-4 (T016); fewer rooms but higher cost vs more rooms and lower cost → US1-6 (T018); two neighbours tie → US2-1 (T023); a door on the route closes between turns → US3-1 (T028); high-speed actor through an exit of cost 1 → spec 001 US1-5; speed change while crossing a costly exit → spec 001 US3-1…3 and, for the hunter, T019.
