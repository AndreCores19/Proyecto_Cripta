---

description: "Task list for Fog of War and Automatic Travel"
---

# Tasks: Fog of War and Automatic Travel

**Input**: Design documents from `specs/003-fog-of-war/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (comando-ir-a, comando-mapa, vista-sala-niebla, bitacora-comentarios), quickstart.md

**Tests**: Required. Constitution IX says every acceptance scenario needs an automated test that cites its FR, and every task cites at least one FR. All tests use fake data built in the test (hand-built rooms, `FabricaFalsa` from `tests/estado_fijo.py`) and **no network**.

## Format: `[ID] [P?] [Story] Description — FR`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: user story from spec.md (US1–US9); phases without a story are shared groundwork
- Every test function's docstring MUST cite its FR and scenario, e.g. `"""FR-004 · US1-2"""`.
- Within a phase, write the tests first and run them: they must fail for the right reason before the implementation task, and pass after it.
- Phases follow priority and dependency order, not story number: the P1 stories US1 to US4, then US6 to US8 (they need US1 to US3), then the P2 stories US5 and US9.

## Path Conventions

Single-project layered layout at the repo root: `dto/`, `data/`, `model/`, `service/`, `controller/`, `view/`, `adapters/`, `structures/`, `bench/`, `tests/`.

## Test files

| File | Covers |
|---|---|
| `tests/mapas_niebla.py` (new helper, not a test module) | crypt builders, game and service builders, independent route oracle |
| `tests/test_niebla_estados.py` (new) | US1-1, US1-2, US1-7 |
| `tests/test_vista_niebla.py` (new) | US1-3..US1-6, US1-8, US5 (`mapa`) |
| `tests/test_niebla_puertas.py` (new) | US2 |
| `tests/test_niebla_antorcha.py` (new) | US3 |
| `tests/test_niebla_retroceso.py` (new) | US4, US3-6, US8-2, US8-3 |
| `tests/test_ir_a_ruta.py` (new) | route search and tie-break (US6-2..US6-6), property test of SC-002 and SC-003 |
| `tests/test_ir_a_viaje.py` (new) | trip, stop reasons, scroll (US6-1, US6-7, US6-10, US7, US8-1) |
| `tests/test_ir_a_bitacora.py` (new) | log comments, saved commands, replay (US6-8, US6-9) |
| `tests/test_bench_ir_a.py` (new) | US9 |
| `tests/capturar_estado_niebla.py` (new helper, not a test module) | state of seeded games before any change |

## Common fixtures

**Model fixture**: build `Sala`/`Salida` by hand with the builders of `tests/mapas_cazador.py` (`cadena`, `grilla`, `cripta_aleatoria`, which link exits with `enlazar`). Create the player with `Jugador(vida_max=10**6, ataque=10, defensa=10**6, velocidad=100, inventario_max=10, sala=…)` and the game with `Partida(jugador, semilla=1)`. A sleeping enemy is an `Enemigo(..., sala=…)` appended to `sala.inactivos`. Torch: `partida.efectos.encender_antorcha(jugador, 10**6)`. Door change: `partida._poner_cerrada(salida, True)` (or `salida.cerrada = …` outside a player action).

**Service fixture**: `JuegoService(partida, FabricaFalsa())`; `FabricaFalsa.pobladas` lists the rooms whose content was requested, so a test can prove a room was not downloaded.

**`tests/mapas_niebla.py`** (created in T005; imports only from `model/`, `service/`, `tests/mapas_cazador.py` and `tests/estado_fijo.py`):
- `partida_en(salas, sala_jugador, velocidad=100)` → `Partida`; `servicio_en(partida)` → `JuegoService` with `FabricaFalsa`.
- `explorar_todo(salas)`: sets `conocimiento = 2` on every room and `memoria = 1` (open) or `2` (closed) on every door face to the real state, by plain assignment (test setup only, outside the history).
- `ruta_referencia(salas, partida, destino)`: the oracle. Plain lists, repeated relaxation until nothing changes: `dist[destino] = 0`, others infinite; `dist[r] = min over exits s of r with s.origen and s.destino both explored and the remembered state of s open: s.costo + dist[s.destino]`. The remembered state is read with the oracle's own rule (real state if the door touches the player's room, else `s.memoria`), not by calling `puerta_recordada`. Returns `(d, salida)` where `salida` is the open exit of the player's room with `s.costo + dist[s.destino] == d` and the lowest `(s.destino.id, s.direccion)`, `(0, None)` if the player is in `destino`, `(None, None)` if unreachable. No heap, no stamps, no `busq_*` fields.

## Phase 1: Baseline before any code change

**Purpose**: save the "before" numbers and state. Nothing in this phase edits code. Every later task depends on it.

- [X] T001 Check that `specs/003-fog-of-war/spec.md` and the plan artifacts are committed (commits `0773eaf` and `73cc881`) and that `git status` shows no change under `model/`, `structures/`, `data/`, `service/`, `dto/`, `view/`, `controller/`, `adapters/`, `bench/` or `main.py` (Constitution VII) — all FRs
- [X] T002 Run `python -m pytest` on the unchanged code and note the result. It is the "all green before" reference for Phase 3 and Phase 12 — FR-014
- [X] T003 [P] Run `python -m bench.bench_ciclo` three times on the unchanged code and save all three outputs, separated by a line `--- corrida N ---`, to `specs/003-fog-of-war/bench-antes-ciclo.txt`. Do not edit the output — FR-026
- [X] T004 [P] Capture the state of seeded games before any change — FR-014 (SC-006):
  - Create `tests/capturar_estado_niebla.py` (like `tests/capturar_estado_sin_cazadores.py`): it uses `resumen(semilla)` from `tests/estado_sin_cazadores.py` and writes the summaries for seeds 1, 2 and 3 to `specs/003-fog-of-war/estado-antes.txt`. Run it now, on the unchanged code.

**Checkpoint**: the baseline files exist and nothing else changed. Review before starting Phase 2.

---

## Phase 2: Foundational — fields and fixtures

**Purpose**: the two fields of the data model and the shared test helper. Blocks every story.

- [X] T005 Write `tests/mapas_niebla.py` as described in "Common fixtures" (`partida_en`, `servicio_en`, `explorar_todo`, `ruta_referencia`). Add a first self-check in `tests/test_niebla_estados.py`: the oracle gives `d` 250 and the first exit toward B for a chain with costs 100 and 150 with every room explored and every door open, and `(None, None)` when the exit of the middle room is closed — FR-017, FR-018
- [X] T006 In `model/sala_logica.py` add the module constants `DESCONOCIDA = 0`, `AVISTADA = 1`, `EXPLORADA = 2` and `NO_OBSERVADA = 0`, `ABIERTA = 1`, `CERRADA = 2`; add `Sala.conocimiento` (int, initial `DESCONOCIDA`: "`0` unknown, `1` sighted, `2` explored") and `Salida.memoria` (int, initial `NO_OBSERVADA`: "`0` never observed, `1` open, `2` closed, as of the last observation"). `Salida.enlazar` leaves `memoria` untouched (both faces start at 0). Neither field may touch `Salida.epoca_puertas`. Run `python -m pytest`; all green — FR-001, FR-006, FR-007

**Checkpoint**: fields exist, suite green, helper written.

---

## Phase 3: User Story 1 — The player only knows what they have explored (Priority: P1)

**Goal**: three room states, derived from the player's moves; the room view shows only what is known.

**Independent Test**: start a game, check the states at time 0, move through one exit, check explored, sighted and unknown rooms and the exit lines of the room view.

- [X] T007 [P] [US1] Write `tests/test_niebla_estados.py` (rest of the file): US1-1 (start: the starting room is explored at time 0, the destinations of its exits are sighted, every other room is unknown), US1-2 (entering a sighted room explores it and sights the destinations of its exits that are not explored), US1-7 (re-entering keeps the state), and `Partida.conocidas` holds exactly the rooms above level 0, in order of discovery. Docstrings `FR-001, FR-002, FR-003, FR-004 · US1-1`, etc. — FR-001, FR-002, FR-003, FR-004, FR-005
- [X] T008 [P] [US1] Write `tests/test_vista_niebla.py`, part room view: US1-3 (explored room: name, exits, costs, door states), US1-4 and US1-5 (a sighted room has no name in the exit line and an unknown room is not named anywhere), US1-6 (the full skeleton is in the rooms but the view is built from knowledge only: print a room whose neighbor has a distinctive name and assert the name is absent while sighted and present once explored), US1-8 (exit line toward a sighted room reads `sin explorar` with direction, cost and door state; toward an explored room it prints the name), per [contracts/vista-sala-niebla.md](./contracts/vista-sala-niebla.md) — FR-003, FR-004, FR-010, FR-011
- [X] T009 [US1] In `model/partida_logica.py` add `self.conocidas = []`, `_subir(sala, nivel)` (if `nivel > sala.conocimiento`: `historial.asignar(sala, "conocimiento", nivel)` and, when it came from `DESCONOCIDA`, `historial.lista_agregar(self.conocidas, sala)`) and `_explorar(sala)` (`_subir(sala, EXPLORADA)`, then `_subir(destino, AVISTADA)` for each exit whose destination is below `AVISTADA`). Call `_explorar(jugador.sala)` in `__init__` right after `_entrar_en_sala` (outside any history frame, so it is never undone) and `_explorar(salida.destino)` in `mover` right after `_entrar_en_sala(salida.destino)`, inside the action frame. Depends on T006, T007 — FR-001, FR-002, FR-004, FR-005, FR-013
- [X] T010 [US1] Fog in the view: in `dto/estado_vista_dto.py` `SalidaVistaDTO.nombre_destino` is `None` when the destination is not explored; in `service/juego_service.py` `estado_vista` fills it as `s.destino.nombre if s.destino.conocimiento == EXPLORADA else None`; in `view/vista_consola.py` `mostrar_estado` prints `sin explorar` when it is `None`. Depends on T008, T009 — FR-004, FR-010, FR-011
- [X] T011 [US1] Run the whole suite. Tests that print a room built by `tests/estado_fijo.py` compare with the golden files of spec 001, whose neighbors are now sighted. Do **not** edit those goldens: make the fixed state fully explored by calling `explorar_todo` on its rooms inside `armar_estado_fijo` (import the helper from `tests/mapas_niebla.py` or inline the loop) so the part-one view is unchanged. If any other existing test fails because of fog, fix its setup the same way and list it in the commit message — FR-010, FR-014 (SC-006)

**Checkpoint**: states and view work. Review before Phase 4.

---

## Phase 4: User Story 2 — The map remembers doors as last observed (Priority: P1)

**Goal**: remembered door state with continuous observation while inside either room.

**Independent Test**: observe an automatically closing door open, move away, let it close, check the map still shows it open until the player is again in one of its two rooms.

- [ ] T012 [P] [US2] Write `tests/test_niebla_puertas.py`: US2-1 (a door observed open is remembered open), US2-2 (the door closes while the player is in a room that does not touch it: the remembered state is still open), US2-3 (the player enters one of its two rooms: the remembered state is closed), US2-4 (observed from one side, later seen from the other: the latest observation is kept), US2-5 (the player stays in the room and the door closes automatically: the map shows closed at that moment); both faces of a door always agree; a real change of `cerrada` never changes `Salida.epoca_puertas` through `memoria`. Use `partida.puerta_recordada(salida)` as the reading API — FR-006, FR-007
- [ ] T013 [US2] In `model/partida_logica.py` add `_memorizar_puertas(sala)` (for each exit of `sala`, `historial.asignar` of `memoria` on the exit and on its opposite, `CERRADA` if `cerrada` else `ABIERTA`) and `puerta_recordada(salida)` (returns the real state, as `ABIERTA`/`CERRADA`, when `salida.origen is jugador.sala or salida.destino is jugador.sala`, else `salida.memoria`). In `mover`, inside the action frame, call `_memorizar_puertas(jugador.sala)` **before** changing the room. Depends on T012 — FR-006, FR-007, FR-013
- [ ] T014 [US2] Run `python -m pytest tests/test_niebla_puertas.py tests/test_niebla_estados.py tests/test_puertas.py -v` and the whole suite; all green — FR-006, FR-007

**Checkpoint**: door memory works.

---

## Phase 5: User Story 3 — The lit torch explores the neighbors (Priority: P1)

**Goal**: with the torch lit, entering a room explores its neighbors through any exit, without activating anything and without downloading content.

**Independent Test**: light the torch, enter a room with a closed exit toward a room that has an enemy and a trap, check what is known and that nothing activated.

- [ ] T015 [P] [US3] Write `tests/test_niebla_antorcha.py`: US3-1 (every neighbor, open or closed, becomes explored), US3-2 (the neighbor has a sleeping enemy and an armed trap: it is explored; the enemy stays in `sala.inactivos` and not in `partida.enemigos`; the trap stays armed; the player's life is unchanged; `FabricaFalsa.pobladas` does not contain the neighbor), US3-3 (torch not lit: only the entered room), US3-4 (neighbor behind a closed door is explored), US3-5 (the neighbor's other doors keep `memoria == NO_OBSERVADA` and the route search does not use them; only the door joining the room entered to that neighbor is observed). The destinations of the neighbors' exits become sighted. Lighting the torch while standing in a room does not explore that room's neighbors — FR-008, FR-009, FR-017
- [ ] T016 [US3] In `model/partida_logica.py` add `_explorar_vecinas(sala)` (`_explorar(salida.destino)` for each exit of `sala`) and, in `mover` right after `_explorar(salida.destino)`, call it when `jugador.efecto_activo("antorcha")` is not `None`. It must not call `_entrar_en_sala`, `activar_enemigo`, `activar_trampas` or `poblar_sala`. Depends on T009, T015 — FR-008, FR-009
- [ ] T017 [US3] Run `python -m pytest tests/test_niebla_antorcha.py tests/test_efectos.py -v` and the whole suite; all green — FR-008, FR-009

**Checkpoint**: torch works.

---

## Phase 6: User Story 4 — Knowledge is part of the game state (Priority: P1)

**Goal**: knowledge is reverted by the scroll, rebuilt by loading a saved game, and identical in every run.

**Independent Test**: explore, save and load and compare; read a scroll and compare with the knowledge before the reverted action.

- [ ] T018 [P] [US4] Write `tests/test_niebla_retroceso.py`: US4-2 (a move that explored a room is reverted with `partida.retroceder()`: the room returns to sighted or unknown, `conocidas` loses it), US4-3 (the door memory written by the reverted move returns to its previous value), scenario 5 / US3-6 (a move made with the torch lit is reverted: the neighbors explored by the torch return to their previous level and the room entered too), reverting only the last of several moves keeps the earlier knowledge — FR-013, FR-014
- [ ] T019 [P] [US4] In `tests/test_niebla_retroceso.py` add US4-1 and US4-4: a helper `instantanea_conocimiento(salas, partida)` returns the list `(id, conocimiento)` per room and `(origen.id, direccion, memoria)` per exit and `[s.id for s in conocidas]`. US4-1: play a command list on `Controlador` + `JuegoService` (`VistaSilenciosa`, rooms rebuilt by the same builder), then rebuild the rooms and re-execute the saved command list as `Aplicacion._reejecutar` does; the two snapshots are equal. US4-4: the same crypt, seed and commands twice give equal snapshots after every command — FR-012, FR-014
- [ ] T020 [US4] Run `python -m pytest tests/test_niebla_retroceso.py -v`. If a test fails, the cause is a write to `conocimiento`, `memoria` or `conocidas` outside `historial.asignar`/`lista_agregar` or outside the action frame: fix it in `model/partida_logica.py` — FR-013, FR-014. Then run the whole suite

**Checkpoint**: all P1 knowledge rules hold. Review before the trip phases.

---

## Phase 7: User Story 6 — "ir a" takes the player to an explored room (Priority: P1)

**Goal**: route over the known map, ordinary steps, log comments, destination named by id.

**Independent Test**: build a crypt with known and unknown parts, order trips to different rooms, check the route, the time and the log.

- [ ] T021 [P] [US6] Write `tests/test_ir_a_ruta.py` (needs T022; fails until then): US6-3 (cheaper route with more exits wins), US6-4 (first step toward the neighbor with the lowest id among those on a route of minimum cost; with equal ids the lowest direction name; also a grid crypt with many equal routes), US6-5 (a sighted room is never used even if it would shorten the route), US6-6 (a door remembered closed is never used, and `abrir_puerta` is never called: wrap it and assert zero calls, with the key in the inventory), the player already in the destination returns `(None, 0)`, no route returns `(None, None)`, and the exit toward an unobserved door is not used. Order independence: permute `Sala.salidas` and `Sala.entradas` of every room (reverse and rotate them) and check the first step and `d` do not change. Heap reuse: two searches in a row with the same `RutaConocida` object give the same results as two fresh objects (the heap is emptied at the start of each search). Randomized check: 200 seeded crypts from `cripta_aleatoria`, `explorar_todo`, then random rooms left unexplored and doors left unobserved; `RutaConocida.siguiente_paso` equals `ruta_referencia` — FR-017, FR-018, FR-021
- [ ] T022 [US6] Create `model/ruta_conocida.py` with `RutaConocida.siguiente_paso(partida, destino)` as in plan §The route search: the object keeps one `MonticuloMinimo` and calls `vaciar()` on it at the start of every search (the search stops as soon as the player's room is extracted, so entries are left over); the stamp is taken from `Busqueda.nueva_estampa()` (import `Busqueda` from `model/ruta_cazador.py`) as the very first step, before any early return, even when there is no route or the player is already in `destino`; backwards over `Sala.entradas` from `destino`, only incoming exits `x` with `x.origen.conocimiento == EXPLORADA` and `partida.puerta_recordada(x) == ABIERTA`, stop when the player's room is extracted (skip stale entries), then choose among the open exits of the player's room whose destination is explored and marked with this stamp and `s.costo + dist == d` the lowest `(s.destino.id, s.direccion)`. Returns `(salida, d)`, `(None, 0)` or `(None, None)`. Imports only `structures/monticulo` and model files; no `dict`, `set`, `heapq`, `bisect`, `collections`. Depends on T013, T021 — FR-017, FR-018, FR-021
- [ ] T023 [P] [US6] Write `tests/test_ir_a_viaje.py`, part basic trips (needs T024, T025): US6-1 (an unexplored destination, and an id that matches no known room, are rejected: `aceptado` is False, `reloj` and the whole knowledge snapshot unchanged), US6-2 (explored destination: the player ends there, `motivo == "llegada"`, `pasos` equals the exits crossed), US6-7 (three steps with costs 100, 300 and 50 and speed 100: the clock advances 100, 300 and 50 between steps, and an automatic door closing event scheduled in between fires between steps), US6-10 (already in the destination: `llegada`, 0 steps, no time) — FR-016, FR-019, FR-022
- [ ] T024 [US6] Create `model/viaje_logica.py` with the reason constants `LLEGADA`, `ENEMIGOS`, `DANO`, `FIN_PARTIDA`, `SIN_RUTA`, `RETROCESO` and `Viaje(partida, destino, mover)` with `paso()` as in plan §Trips, in this task only: if the player is in `destino`, return `LLEGADA`; compute the route; if none, return `SIN_RUTA` without calling `mover`; otherwise call `mover(salida.direccion)` and return `None` (the checks after the step come in T033). Depends on T022 — FR-019, FR-020, FR-021, FR-022
- [ ] T025 [US6] In `service/juego_service.py` add `ir_a(id_sala)`: look the room up in `partida.conocidas` comparing `str(sala.id).lower()` with `str(id_sala).lower()`; not found or `conocimiento != EXPLORADA` → `ViajeResultadoDTO(False, "no_explorada", 0)` with no state change; otherwise loop `Viaje.paso()` with `self.mover` as the move function until a reason comes out and return `ViajeResultadoDTO(True, motivo, pasos)` (also keep the list of directions taken in `direcciones`). Create `dto/viaje_dto.py` with `ViajeResultadoDTO(aceptado, motivo, pasos, direcciones)`. Depends on T023, T024 — FR-016, FR-019
- [ ] T026 [P] [US6] Write `tests/test_ir_a_bitacora.py` (needs T027–T029): US6-8 (a trip of three steps writes `# ir a <id>` then three move lines to the log file, and the saved command list (`controlador.comandos`) holds the three moves and not the order), US6-9 (a rejected order writes the comment and no move, and adds nothing to `controlador.comandos`), the log reader skips lines beginning with `#` and returns only the move lines, an old log without comments reads exactly as before, a trip stopped by `sin_ruta` after one step writes exactly one move line (moves are written only for steps taken), and replaying the moves from the log reaches the same `resumen_final()` and knowledge snapshot as the original trip — FR-016, FR-024
- [ ] T027 [P] [US6] In `adapters/bitacora_partida.py` add `comentar(texto)` (writes `# <texto>` and flushes, like `anotar`); in `adapters/lector_bitacora.py` `leer` ignore body lines that start with `#` ([contracts/bitacora-comentarios.md](./contracts/bitacora-comentarios.md)). `VERSION_FORMATO` stays 1. Depends on T026 — FR-024
- [ ] T028 [US6] In `controller/controlador.py` add the command `ir a <id>`: add `"ir"` to the commands not recorded generically in `ejecutar`; `_cmd_ir_a(palabras)` requires `palabras[1] == "a"` and a third word (otherwise the message `Uso: ir a <id>`), writes the comment `ir a <id>` with `bitacora.comentar` (if the log exists) before anything else, calls `servicio.ir_a`, and for each direction in `resultado.direcciones` appends it to `self.comandos` and to the log with `bitacora.anotar`. On rejection shows the message `Esa sala no está explorada.`; on acceptance shows `Viaje detenido: <texto>` with the text of the reason (`llegada` → `llegaste a tu destino`, `enemigos` → `hay enemigos en la sala`, `dano` → `recibiste daño`, `fin_partida` → `la partida terminó`, `sin_ruta` → `no hay ruta conocida`, `retroceso` → `retrocediste con un pergamino`) through the existing guarded message helper, so replay with no view prints nothing extra. Depends on T025, T027 — FR-016, FR-023, FR-024
- [ ] T029 [US6] Run `python -m pytest tests/test_ir_a_ruta.py tests/test_ir_a_viaje.py tests/test_ir_a_bitacora.py -v` and the whole suite. Check `model/ruta_conocida.py` and `model/viaje_logica.py` with `grep -nE "heapq|bisect|collections|networkx|\bdict\(|\bset\(|\bfrozenset\(|\{\}|\{[^}]*:[^}]*\}"` (review each hit by hand: f-strings are not indexes) and that they import nothing from `view/`, `controller/` or `service/` — FR-017, FR-021

**Checkpoint**: "ir a" works up to arrival and no-route. Review before Phase 8.

---

## Phase 8: User Story 7 — The trip is recomputed and stops when it should (Priority: P1)

**Goal**: the stop reasons, in the order of FR-022, and door observation during the trip.

**Independent Test**: run trips in which a door was remembered open but is closed, a room has sleeping enemies, and the player is damaged; check each trip stops for the right reason.

- [ ] T030 [P] [US7] In `tests/test_ir_a_viaje.py` add the doors and recomputation scenarios: scenario 2 / US7-1 (the map remembers a door as open but it is closed; on observing it the map is updated, the route is recomputed and, with no alternative, the trip stops with `sin_ruta` and the clock has not moved since the last step), US7-2 (an alternative known route exists: the trip continues along it), US7-9 (clock events change a door state between two steps: the next step uses the route computed with the state at that moment). Docstrings cite `FR-006, FR-020, FR-022` — FR-006, FR-020, FR-022
- [ ] T031 [P] [US7] In `tests/test_ir_a_viaje.py` add the stop reasons: scenario 3 / US7-3 (the route enters a room with sleeping enemies: they end in `partida.enemigos` activated by the part-one rule and the reason is `enemigos`), US7-4 (a room with active enemies), US7-5 (damage from a trap, from an enemy attack in the clock events of the step, and from a poison pulse between two steps: reason `dano`), US7-6 (the step reaches the exit room and wins, and a step in which the player dies: the trip takes no further step; reason per the order), US7-7 (several reasons at once: arrival at the destination in a room with enemies reports `llegada`; damage and enemies reports `enemigos`; a death in a trap in the destination room reports `fin_partida`, not `llegada`; a victory at the destination reports `fin_partida`; a non-fatal trap at the destination reports `llegada` before `dano`), US7-8 (no known route before a step: `sin_ruta`, no time consumed), US7-10 (a hunter walks into the player's room during the clock events of a step in a room that had no enemies: the reason is `enemigos`) — FR-022, FR-023
- [ ] T032 [US7] Extend `Viaje.paso()` with the checks after `mover`, in the order of FR-022: `partida.terminada` → `FIN_PARTIDA`; player in `destino` → `LLEGADA`; alive enemies of `partida.enemigos` with `sala is jugador.sala` → `ENEMIGOS`; `jugador.vida` lower than before the step → `DANO`; otherwise `None`. Record `jugador.vida` before calling `mover`. Route recomputation per step is already in T024; confirm nothing is kept between steps. Depends on T030, T031 — FR-020, FR-022
- [ ] T033 [US7] Run `python -m pytest tests/test_ir_a_viaje.py -v` and the whole suite; all green — FR-020, FR-022

**Checkpoint**: trips stop for every reason of FR-022.

---

## Phase 9: User Story 8 — The scroll reverts only the last step (Priority: P1)

**Goal**: a scroll reverts one step, the trip does not continue and stops with its own reason.

**Independent Test**: start a trip, read the scroll after a step, check the state and that no further step is taken.

- [ ] T034 [P] [US8] In `tests/test_ir_a_viaje.py` add scenario 6 / US8-1 (the console cannot interrupt a running trip, so "during" means between two steps): drive the trip by hand with `Viaje` and a move function wrapper that, after the first step, calls `partida.retroceder()` once (a rewind of the last step); the next `paso()` returns `RETROCESO`, no further move is made, and only the last step was reverted (room, clock and `acciones_jugador` equal the state after the first step minus the rewound step). Also with `JuegoService.retroceder()` and a real scroll in the inventory — FR-022, FR-023, FR-025
- [ ] T035 [P] [US8] In `tests/test_niebla_retroceso.py` add US8-2 (the reverted step explored new rooms and observed doors: both return to the previous state) and US8-3 (a scroll read after a finished trip reverts only the last step of the trip) — FR-013, FR-025
- [ ] T036 [US8] In `model/partida_logica.py` add `self.retrocesos = 0` in `__init__`, a plain attribute **not** written through the history, and add 1 to it in `retroceder()` when `historial.deshacer()` succeeds. In `Viaje` store `partida.retrocesos` at creation and return `RETROCESO` at the start of `paso()` if it changed. Depends on T034, T035 — FR-022, FR-025
- [ ] T037 [US8] Run `python -m pytest tests/test_ir_a_viaje.py tests/test_niebla_retroceso.py tests/test_retroceso_aleatorio.py -v` and the whole suite; all green — FR-025

**Checkpoint**: all P1 stories done. Review before the P2 phases.

---

## Phase 10: User Story 5 — The player can view the known map (Priority: P2)

**Goal**: the `mapa` command lists explored rooms, their exits and the sighted rooms.

**Independent Test**: explore some rooms and run the command; check it lists exactly what is known and consumes no time.

- [ ] T038 [P] [US5] In `tests/test_vista_niebla.py` add the map part, per [contracts/comando-mapa.md](./contracts/comando-mapa.md): US5-1 (each explored room with its id, name and exits with costs and remembered door states; an exit toward a sighted room reads `sin explorar` with no id and no name), US5-2 (unknown rooms do not appear), US5-3 (the command changes nothing: `reloj` and the knowledge snapshot are equal before and after), explored rooms are sorted by id, a door never observed reads `sin observar`, the room the player is in is marked `(tú estás aquí)`, and `mapa_vista()` returns a snapshot of plain values: every field of the DTOs is `int`, `str`, `bool`, `None` or a list of those, with no reference to a `Sala`, `Salida` or any model object — FR-005, FR-015, FR-004
- [ ] T039 [US5] Create `dto/mapa_vista_dto.py` (`MapaVistaDTO(id_sala_actual, salas)`, `SalaConocidaDTO(id_sala, nombre, salidas)`, `SalidaConocidaDTO(direccion, id_destino, nombre_destino, costo, puerta)` with the fields of [data-model.md](./data-model.md), `puerta` being `"abierta"`, `"cerrada"` or `"sin observar"`). In `service/juego_service.py` add `mapa_vista()`: copy `partida.conocidas`, keep those with `conocimiento == EXPLORADA`, sort by id with `ordenar` from `structures/ordenamientos.py` (key = room id), build the DTO reading doors with `partida.puerta_recordada`, and for a destination that is not explored set `id_destino` and `nombre_destino` to `None`. Add `VistaConsola.mostrar_mapa(mapa)` and a no-op `VistaSilenciosa.mostrar_mapa`. In `controller/controlador.py` add the command `mapa` (recorded generically, like `inv`) calling a guarded helper `_mostrar_mapa` that does nothing when `vista is None`. Depends on T038 — FR-015, FR-005, FR-004
- [ ] T040 [US5] Run `python -m pytest tests/test_vista_niebla.py -v` and the whole suite; all green — FR-015

**Checkpoint**: `mapa` works.

---

## Phase 11: User Story 9 — "ir a" is fast (Priority: P2)

**Goal**: one route computation with the full known map of the reference crypt takes at most 5 ms at the 99th percentile; the maximum is reported.

**Independent Test**: run `bench_ir_a` and read the verdict.

- [ ] T041 [P] [US9] Write `tests/test_bench_ir_a.py` (small configuration, like `tests/test_bench_cazador.py`): US9-2 (the same seed builds the same crypt twice: compare `(id, direction, destination id, cost)` of every exit), the report has the average, 99th percentile and maximum, the benchmark builds games with `Partida` directly and `grep`-style check that `bench/bench_ir_a.py` contains no import of `view`, and every measured route equals `ruta_referencia` on the small configuration — FR-026, FR-027
- [ ] T042 [US9] Create `bench/bench_ir_a.py`: a seeded crypt builder (reuse `armar_cripta`/`_salas_conexas` of `bench/bench_cazador.py` after reading them, or write a seeded builder in the new file) with `num_salas` rooms and costs from the same set, `explorar_todo`-style marking of every room explored and every door remembered open **by plain assignment**; `ejecutar(pequeno=False)` measures `RutaConocida.siguiente_paso` alone (microseconds, 2000 repetitions, player and destination drawn per repetition from `random.Random(semilla)`, far apart) and, for information, a whole step (route plus move plus event cycle) for 100 rooms (the verdict size), then 500 and 1000 rooms as information. It prints average, 99th percentile and maximum, and the verdict `p99 <= 5 ms` for 100 rooms. Register it in the `--bench` list of `main.py` next to `bench_cazador`. Imports nothing from `view/`. Depends on T041 — FR-026, FR-027
- [ ] T043 [US9] Run `python -m bench.bench_ir_a`, `python -m pytest tests/test_bench_ir_a.py -v`, and record the output in `specs/003-fog-of-war/bench-ir-a.txt`. The verdict at 100 rooms must be `<= 5 ms` at the 99th percentile — FR-026 (SC-007)

**Checkpoint**: performance evidence saved.

---

## Phase 12: Polish & cross-cutting

- [ ] T044 [P] Write the no-view replay test in `tests/test_ir_a_bitacora.py`: record a game with a trip and a `mapa` command using `BitacoraPartida(tmp_path)` and `VistaSilenciosa`, then replay the log with `Controlador(servicio, None, None, None)` on rebuilt rooms and the seed from `LectorBitacora`; `resumen_final()` and the knowledge snapshot are equal, and no class defined in `view/` is instantiated during the replay (monkeypatch the constructors as `tests/test_salida_replay.py` does) — FR-014, FR-024, Constitution III
- [ ] T045 [P] Test that the hunters' cache survives a trip: in `tests/test_ir_a_viaje.py`, with a hunter in the shared mode on a crypt where the player makes a trip step between two hunter turns, the hunter's decision equals `decision_referencia` of `tests/mapas_cazador.py` (the "ir a" search shares the stamp counter, so the cached search is recomputed). Add the no-route case, mirroring `test_cache_busqueda_ajena_entre_dos_turnos` in `tests/test_cazador_equivalencia.py`: the hunter decides once (its search is cached), `ir a` toward a destination with no known route is run (the player does not move and no time passes), and on the hunter's next turn `Busqueda.ultima_estampa` has changed, the search is recomputed and the decision equals `decision_referencia` — FR-011 of spec 002, FR-017
- [ ] T046 Constitution gate, limited to what this feature adds (`model/sala_logica.py`, `model/partida_logica.py`, `model/ruta_conocida.py`, `model/viaje_logica.py`, `dto/`, `service/juego_service.py`, `controller/controlador.py`, `adapters/`, `view/vista_consola.py`, `bench/bench_ir_a.py`) — FR-014, FR-021, FR-026:
  - none uses `dict`, `set`, `heapq`, `bisect`, `collections`, `networkx` or another graph library (`grep -nE "heapq|bisect|collections|networkx|\bdict\(|\bset\(|\bfrozenset\(|\{\}|\{[^}]*:[^}]*\}" <files>`, reviewing each hit by hand: f-strings and JSON parsing are not indexes); the auxiliary structures are `MonticuloMinimo`, lists and integer fields;
  - `model/` and `structures/` import nothing from `view/` or `controller/`;
  - `grep -rn "Vista" bench/` finds nothing, and `--replay` creates no `view/` class (T044);
  - `structures/agenda.py` and `structures/historial.py` are unchanged (`git diff --stat` empty);
  - the "ir a" step moves only through `JuegoService.mover` (`grep -n "mover" model/viaje_logica.py service/juego_service.py`);
  - `grep -n "poblar_sala" model/` is empty (exploring never downloads content, Constitution V).
- [ ] T047 Run `python -m bench.bench_ciclo` three times into `specs/003-fog-of-war/bench-despues-ciclo.txt` (same separators as T003). Every scenario keeps p99 ≤ 20 ms. Compare the average per cycle with the "before" file as an investigation trigger, not a gate: if it is more than 10% slower (best of 3 runs each), find the cause (likely the exploration and door-memory work in `Partida.mover`) and write it down before moving on — FR-026
- [ ] T048 Run the whole suite, `python -m pytest`; all green. Compare the count with T002 plus the new tests. Run `tests/capturar_estado_niebla.py` into a temporary file and compare it with `specs/003-fog-of-war/estado-antes.txt`: they must be equal (knowledge does not change the game state) — FR-014 (SC-001, SC-006)
- [ ] T049 [P] Update `README.md`: add `mapa` and `ir a <id>` to the command table, and a short paragraph on fog of war (explored, sighted and unknown rooms; the torch; trips stop and why); mention `bench_ir_a` among the benchmarks and the new `tests/` files in section 4 — FR-015, FR-016
- [ ] T050 [P] Write the property test for SC-002 and SC-003 in `tests/test_ir_a_ruta.py`: for 100 seeded crypts from `cripta_aleatoria` (with some doors closed and changing, a torch lit in some games), play random sequences of moves, `ir a` orders toward random known and unknown ids, and waits through `JuegoService`, and after every command (a) build the room view and the known map and assert every room name and id they show belongs to an explored room (a sighted room appears only as `sin explorar`), and (b) for every trip step taken, assert the room entered and the route's rooms were explored, the door crossed was remembered open or touched the player's room, and `abrir_puerta` was never called. A violation fails the test with the seed — FR-010, FR-017, FR-021 (SC-002, SC-003)
- [ ] T051 Check every case of assignment Appendix B that concerns fog of war, door memory, the torch and "ir a" against `spec.md`: for each case write, in a note under this task, the scenario of the spec and the test that covers it. If a case has no scenario, stop and correct the spec in its own commit before the code that depends on it (Constitution IX). It needs the text of Appendix B, which is not in the repository: ask for it if it is not at hand — all FRs
- [ ] T052 Write the justification for the separate search in `docs/DECISIONES.md` (create the file if it does not exist), under the heading `5.3 Búsqueda de «ir a» separada de la del cazador`: "ir a" has its own search class over the player's known subgraph (explored rooms and exits remembered open) and does not reuse the hunter's full-map search; it shares the min-heap (`structures/monticulo.py`) and takes its stamps from the shared counter so the hunters' saved search is recomputed. Copy the reasons from `specs/003-fog-of-war/research.md` R2 (a flag on the hunter's `Busqueda.calcular` would add a branch to the hunters' hot path; the two searches differ in what they traverse) and R6 (stamp rule A and its cost) — FR-017, FR-018
- [ ] T053 Manual check from `quickstart.md` — FR-004, FR-008, FR-015, FR-016, FR-024: run `python main.py --offline` on a recorded crypt and report exactly what could be checked (sighted exits, `mapa`, torch, `ir a` to an explored and to an unexplored room, the `# ir a` comments in the generated `partida_*.log`, and `--replay` of that log). If the offline recording has no torch, say so and report that only the automated tests cover it
- [ ] T054 Add a note under T053 saying what was checked and what was not, and update `specs/003-fog-of-war/checklists/requirements.md` only if a spec correction was needed (a spec correction goes in its own commit before the code that depends on it) — all FRs

---

## Dependencies & Execution Order

```text
Phase 1 (T001–T004)  baseline: nothing else may start before T003–T004 are saved
→ Phase 2  foundations   T005, T006
→ Phase 3  US1           T007, T008 → T009 → T010 → T011
→ Phase 4  US2           T012 → T013 → T014
→ Phase 5  US3           T015 → T016 → T017
→ Phase 6  US4           T018, T019 → T020
→ Phase 7  US6           T021 → T022 → T023 → T024 → T025 → T026, T027 → T028 → T029
→ Phase 8  US7           T030, T031 → T032 → T033
→ Phase 9  US8           T034, T035 → T036 → T037
→ Phase 10 US5           T038 → T039 → T040
→ Phase 11 US9           T041 → T042 → T043
→ Phase 12 polish        T044, T045, T046, T050 → T047 → T048 → T049, T051, T052 → T053 → T054
```

- Phase 2 depends only on Phase 1. Phases 3 to 5 each add code to `model/partida_logica.py`, so they are sequential.
- Phase 6 is mostly tests over Phases 3 to 5; a failure there is fixed in `model/partida_logica.py`.
- Phase 7 needs Phases 3 and 4 (explored rooms and `puerta_recordada`); Phases 8 and 9 edit `model/viaje_logica.py` after it, so they are sequential.
- Phase 10 (`mapa`) needs Phases 3 and 4 only and could run in parallel with Phases 7 to 9 in a second session, since it touches `dto/mapa_vista_dto.py`, `view/` and a different part of the controller and service; it is placed late because it is P2.
- Phase 11 needs Phase 7 (`RutaConocida`).
- Edits to the same file are sequential: `model/partida_logica.py` (T009 → T013 → T016 → T036), `model/viaje_logica.py` (T024 → T032 → T036), `service/juego_service.py` (T010 → T025 → T039), `controller/controlador.py` (T028 → T039), `tests/test_ir_a_viaje.py` (T023 → T030 → T031 → T034 → T045), `tests/test_ir_a_ruta.py` (T021 → T050), `tests/test_vista_niebla.py` (T008 → T038), `tests/test_niebla_retroceso.py` (T018 → T019 → T035), `tests/test_ir_a_bitacora.py` (T026 → T044).
- `[P]` marks tasks that touch different files with no unfinished dependency; with one implementer they can be done in any order inside their phase.

### Parallel examples

```text
Phase 1:  T003 ∥ T004 (different outputs)
Phase 3:  T007 ∥ T008 (different test files)
Phase 7:  T021 ∥ T023 ∥ T026 (write the tests first), T027 ∥ T022 (adapters vs model)
Phase 10 ∥ Phases 7–9 (different production files)
Phase 12: T044 ∥ T045 ∥ T049
```

## Implementation Strategy

1. **Phase 1 first.** The "before" benchmark output and the seeded state file are taken on the unchanged code.
2. **Foundations and knowledge** (Phases 2 to 6): the three room states, door memory, the torch and rollback, reviewed one phase at a time. MVP of the fog: Phase 3 alone gives a game where the player only sees what they have explored.
3. **"ir a"** (Phases 7 to 9): the route and the trip first, then the stop reasons, then the scroll. MVP of the command: Phase 7.
4. **Known map and benchmark** (Phases 10 and 11), then polish (Phase 12).
5. Commit per phase; a spec correction always goes in its own commit before the code that follows it (Constitution VII). Review each phase's checkpoint before starting the next.
6. **Scenario coverage** (Constitution IX): US1-1, US1-2, US1-7 → T007; US1-3..US1-6, US1-8 → T008; US2-1..5 → T012; US3-1..5 → T015; US3-6 and scenario 5 → T018; US4-1, US4-4 → T019; US4-2, US4-3 → T018; US5-1..3 → T038; US6-1, US6-2, US6-7, US6-10 → T023; US6-3..6 → T021; US6-8, US6-9 → T026; US7-1, US7-2, US7-9 → T030; US7-3..8 → T031; US8-1 → T034; US8-2, US8-3 → T035; US9-1 → T042 and T043; US9-2 → T041; SC-002 and SC-003 → T050; Appendix B → T051; decision §5.3 → T052.
7. **Mandatory scenarios of the assignment** (spec Input): 1 → US6-1 (T023); 2 → US7-1 (T030); 3 → US7-3 (T031); 4 → US3-2 (T015); 5 → US3-6 (T018); 6 → US8-1 (T034).
