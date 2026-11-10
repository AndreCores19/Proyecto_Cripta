---

description: "Task list for Terrain — Exit Costs"
---

# Tasks: Terrain — Exit Costs

**Input**: Design documents from `specs/001-exit-costs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required. Constitution IX says every acceptance scenario needs an automated test that cites its FR. Each owner writes the tests for her own tasks.

**Owners**:
- **Andrea**: data, DTOs, the service view method, controller, view, replay and version tests.
- **Emily**: engine model, move scheduling, section 5.6 measurements.

Every task is tagged `(Owner: …)`.

## Format: `[ID] [P?] [Story] Description (Owner) — FR`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: user story from spec.md (US1–US5)
- Every test function's docstring MUST cite its FR and scenario, e.g. `"""FR-004 · US1-5"""`.

## Path Conventions

Single-project layered layout at the repo root: `dto/`, `data/`, `model/`, `service/`, `controller/`, `view/`, `structures/`, `bench/`, `tests/`.

## Test files and owners

| File | Owner | Covers |
|---|---|---|
| `tests/test_costos_datos.py` (new) | Andrea | DTO reading, repository linking, inconsistent-door cost (US1-6, US1-7 at load time) |
| `tests/test_vista_costos.py` (new) | Andrea | `EstadoVistaDTO`, `estado_vista()`, controller wiring, console output (US4) |
| `tests/test_version_cripta.py` (new) | Andrea | fresh skeleton, save/log version rejection (US5) |
| `tests/test_replay_costos.py` (new) | Andrea | record a log on a crypt with costs and replay it (FR-014) |
| `tests/test_costos_salida.py` (new) | Emily | move durations, FR-016 order, enemies, speed changes, determinism (US1–US3, SC-002–SC-005) |
| `tests/test_puertas.py` (existing) | Emily | `Salida.costo` / `enlazar` sharing rules |

**Common test fixture** (Emily's model tests): build `Sala`/`Salida` by hand and link them with `enlazar`, as `tests/test_puertas.py` does. Use `Jugador(vida_max=…, ataque=…, defensa=…, velocidad=…, inventario_max=10, sala=…)` and `Enemigo(id_enemigo, tipo, nombre, vida, vida_max, ataque, defensa, velocidad, comportamiento, sala)`. Use `Partida(jugador, semilla=1)` and `partida.activar_enemigo(e)`. Give actors a huge `vida_max` and `defensa` when combat is not under test.

---

## Phase 1: Setup

- [x] T001 Commit `specs/001-exit-costs/spec.md` and the plan artifacts before any code change, per Constitution VII. Done: spec and plan are committed (Owner: Emily) — all FRs
- [ ] T002 Before any code change, run `python -m bench.bench_agenda` on the unchanged code and save its full output to `specs/001-exit-costs/bench-parte1.txt` as the part-one baseline for §Measurements in plan.md (Owner: Emily) — FR-014

---

## Phase 2: Foundational (blocking all user stories)

**Purpose**: every exit carries a cost from the skeleton into the model. Andrea's DTO change and Emily's `Salida` attribute run in parallel; the repository needs both.

### Tests

- [ ] T003 [P] Write tests in `tests/test_costos_datos.py` for `SalidaDTO.desde_json` (Owner: Andrea) — FR-001, FR-002:
  - `{"sala": 2, "costo": 300}` gives `costo == 300`
  - `{"sala": 2}` gives `costo is None` (not 100)
- [ ] T004 [P] Write tests in `tests/test_puertas.py` for `Salida`, using the linking table from data-model.md (Owner: Emily) — FR-002, FR-005:
  - None/None → both `costo == 100`
  - x/None → both x
  - None/y → both y
  - x/x → both x
  - an exit with no opposite returns its declared value, or 100
  - `costo_declarado` stays `None` when neither side declares one

### Implementation

- [ ] T005 [P] In `dto/salida_dto.py`, add `costo` to `SalidaDTO.__init__` (default `None`) and read it in `desde_json` with `datos.get("costo")`. "`None` = not declared. No range check (FR-001)" (Owner: Andrea) — FR-001, FR-002
- [ ] T006 [P] In `model/sala_logica.py` (Owner: Emily) — FR-002, FR-005:
  - Add `Salida.__init__(..., costo=None)`, storing `self.costo_declarado`.
  - Add a read-only property `costo` returning `costo_declarado`, or `COSTO_MOVER` (imported from `model/tiempo_logica.py`) when it is `None`.
  - In `enlazar`, copy a non-`None` `costo_declarado` to the side whose value is `None`, the same way `llave` is shared.
- [ ] T007 In the second loop of `construir_salas` in `data/repositorio_cripta.py`, pass `costo=salida_dto.costo` when creating each `Salida`. Depends on T005 and T006 (Owner: Andrea) — FR-001, FR-011
- [ ] T008 In the third loop of `construir_salas` in `data/repositorio_cripta.py`, before `salida.enlazar(otra)`: if `salida.costo_declarado` and `otra.costo_declarado` are both not `None` and differ, raise `ValueError` starting with "Puerta inconsistente:" that names both rooms, both directions and both costs. Use the same message style as the existing check. Depends on T007 (Owner: Andrea) — FR-013
- [ ] T009 Add to `tests/test_costos_datos.py`, building rooms with `RepositorioCripta.construir_salas` from `SalaDTO`s. Depends on T008 (Owner: Andrea) — FR-005, FR-013:
  - A→B declares 300 and B→A declares nothing → both exits cost 300 (US1-7 at load)
  - sides declare 100 and 200 → `ValueError` matching "Puerta inconsistente" (US1-6)
  - the existing room-mismatch inconsistent door still raises

**Checkpoint**: `python -m pytest tests/test_costos_datos.py tests/test_puertas.py` is green, and every exit in the model has `costo`.

---

## Phase 3: User Story 1 — Movement duration depends on the exit crossed (P1) 🎯 MVP

**Goal**: when the player moves through an exit at T, the player is in the destination room at T and their next action is at `T + intervalo(salida.costo, velocidad)`.

**Independent test**: build rooms with exit costs, record `T = partida.reloj`, call `partida.mover(dir)`, then check `partida.jugador.sala` and the player's next action time.

### Tests

- [ ] T010 [US1] Write tests in `tests/test_costos_salida.py` using the common fixture (Owner: Emily). Read the next action time as `partida.jugador.evento.tiempo` right after `partida.mover`; `mover` advances the clock to that action, so `partida.reloj` equals it after the call:
  - US1-1: cost 300, speed 100, move at T → player is in the destination room and next action is at T+300 (FR-003, FR-004, FR-016)
  - US1-2: no cost → T+100 (FR-002, FR-004)
  - US1-3: both sides declare 250 → A→B and then B→A each take 250 (FR-005)
  - US1-4: cost 50, speed 150 → T+33 (FR-004)
  - US1-5: cost 1, speed 1000 → T+1 (FR-004, FR-006)
  - US1-7: only A→B declares 300 → moving B→A takes 300 (FR-005)
  - US1-8: in a room whose exits cost 500, `atacar` and `esperar_jugador` take the part-one intervals (FR-006)
- [ ] T011 [US1] Add FR-016 order tests to `tests/test_costos_salida.py`. Wrap `partida._programar_movimiento` (after T012) with a test double that records `partida.jugador.sala`, `partida.reloj` and the destination's trail mark when it is called, then calls the original (Owner: Emily) — FR-016:
  - the player is already in the destination room at T, before the next action is scheduled
  - the destination room's trail mark is T (`sala.rastro == T`)
  - an armed trap in the destination room fires at T, before the next action
  - entering the exit room ends the game at T with victory, and no next action is scheduled

### Implementation

- [ ] T012 [US1] In `model/partida_logica.py`, add `Partida._programar_movimiento(self, actor, salida)`, which calls `self._programar_siguiente(actor, salida.costo)`. Do not modify `intervalo` or `nuevo_tiempo_por_velocidad` (Owner: Emily) — FR-003, FR-004, FR-007
- [ ] T013 [US1] In `Partida.mover` (`model/partida_logica.py`), replace `self._programar_siguiente(self.jugador, COSTO_MOVER)` with `self._programar_movimiento(self.jugador, salida)`. Keep the existing order: refresh trail → `_entrar_en_sala` → traps → victory → schedule. Remove `COSTO_MOVER` from that file's import if it is no longer used there (Owner: Emily) — FR-003, FR-016

**Checkpoint**: US1 tests green; MVP done.

---

## Phase 4: User Story 2 — Enemies are subject to the same exit costs (P1)

**Goal**: enemy moves use the exit cost and follow FR-016; the decision rules are unchanged.

### Tests

- [ ] T014 [US2] Add to `tests/test_costos_salida.py` (Owner: Emily):
  - US2-1: a wanderer with speed 100 in a room whose only open exit costs 200. When its turn runs at T (call `partida._actuar_enemigo(enemigo)` with `partida.reloj = T`), it is in the destination room and `enemigo.evento.tiempo == T + 200` (FR-007, FR-016)
  - US2-2: a tracker in a room with two open exits (costs 250 and 40). Set the neighbouring rooms' `rastro` and `partida.reloj` so that both trails are within `RASTRO_VIGENCIA` and one is fresher. `partida._decidir_rastreador(enemigo)` returns the exit to the fresher trail, the same exit the part-one rule picks from that state, regardless of cost. Add a second case with equal trails: the tie goes to the lowest room id (FR-008)
  - US2-3: an enemy with speed 50, given `partida.reloj = T`, through `partida._programar_movimiento(enemigo, salida)` on a cost-120 exit → `enemigo.evento.tiempo == T + 240` (FR-007). The docstring must state that the hunter spec must include an equivalent scenario using real hunter behaviour.

### Implementation

- [ ] T015 [US2] In the enemy turn in `model/partida_logica.py` (the block after `_decidir_errante` / `_decidir_rastreador`), when `salida is not None`, call `self._programar_movimiento(enemigo, salida)`; otherwise keep `self._programar_siguiente(enemigo, COSTO_ESPERAR)`. Update the comment "Atacar, moverse y esperar cuesta 100". Do not touch `_decidir_errante` or `_decidir_rastreador` (Owner: Emily) — FR-006, FR-007, FR-008, FR-016

---

## Phase 5: User Story 3 — Speed change while waiting for the next action (P1)

**Goal**: confirm that the existing rescaling (`EfectosLogica._cambiar_velocidad` → `nuevo_tiempo_por_velocidad` → `agenda.reprogramar`) applies to the next action scheduled by a move. No production code change is expected.

- [ ] T016 [US3] Add to `tests/test_costos_salida.py`, following plan.md "Timing semantics". Use an **enemy**, so the pending event can be inspected without advancing to it (Owner: Emily) — FR-009 (US3-3 also FR-006):
  - Setup: set `partida.reloj` to the move time (0 unless stated), then `partida._programar_movimiento(enemigo, salida)` on an exit with the given cost, giving `ev = enemigo.evento`. Then set `partida.reloj` to the change time and call `partida.efectos.aplicar_velocidad(enemigo, nueva - vieja, 10**6)`. The long duration keeps the end-of-effect event out of the way.
  - US3-1: speed 100, cost 500 (event at 500); at reloj 100 change to 200 → `ev.tiempo == 300`
  - US3-2: speed 200, cost 2000 (event at 1000); at reloj 900 change to 50 → `ev.tiempo == 1300`
  - US3-3: speed 10, cost 1, scheduled at reloj 91 (event at 101); at reloj 100 change to 1000 → `ev.tiempo == 101` (remaining = max(1, 1×10//1000) = 1)
  - One player-level case: before moving, apply a speed effect with `aplicar_velocidad(jugador, +100, 100)` at reloj 0. The effect ends at t=100, during the next action's wait. Check that the player's next action ends at `100 + max(1, (end − 100) × 200 // 100)`, where `end` is the time scheduled at the faster speed.
- [ ] T017 [US3] If any T016 test fails, fix it in `model/efectos_logica.py` without changing `nuevo_tiempo_por_velocidad` in `model/tiempo_logica.py`. Otherwise mark this task done with no change (Owner: Emily) — FR-009

---

## Phase 6: User Story 4 — The player sees the cost of each exit (P2)

**Goal**: the room view is drawn from `EstadoVistaDTO` (no `Partida` in the view), and exit lines read `N -> Pasillo (abierta, costo 300)` (contracts/room-view.md).

### Tests

- [ ] T018 [P] [US4] Write tests in `tests/test_vista_costos.py`. Build the service like `armar_servicio()` in `tests/test_service.py` (Owner: Andrea) — FR-010:
  - US4-1: `servicio.estado_vista().salidas` has `norte` with `costo 300` and `sur` with `costo 100`
  - US4-2: a closed exit with cost 40 has `cerrada is True` and `costo 40`
  - `VistaConsola().mostrar_estado(estado)`, captured with `capsys`, prints `(abierta, costo 300)`, `(abierta, costo 100)` and `(cerrada, costo 40)`
  - The rest of the output is identical to the part-one format for the same state: room line, `Tiempo:`, player lines, enemies (same filter as today), traps, objects, last 20 log lines
- [ ] T019 [P] [US4] Add to `tests/test_vista_costos.py`: a fake view records the argument passed to `mostrar_estado` while `Controlador.jugar` runs one loop iteration (fake `pedir_comando` returns `"salir"`). Assert it is an `EstadoVistaDTO` and not a `Partida` (Owner: Andrea) — FR-010, Constitution III

### Implementation

- [ ] T020 [P] [US4] Create `dto/estado_vista_dto.py` with `EstadoVistaDTO`, `JugadorVistaDTO`, `SalidaVistaDTO`, `EnemigoVistaDTO`, `TrampaVistaDTO` and `ObjetoVistaDTO`, with exactly the fields in data-model.md "EstadoVistaDTO". `SalidaVistaDTO.costo` is "int, already resolved: declared or 100". Use plain classes and plain lists, and import nothing from `model/` (Owner: Andrea) — FR-010
- [ ] T021 [US4] Add `JuegoService.estado_vista(self)` in `service/juego_service.py`. It builds an `EstadoVistaDTO` from `self.partida`, following the "From" column in data-model.md: exits in room order with `salida.costo`; enemies where `enemigo.sala is sala`; `bitacora.obtener_todos()[-20:]`. It must only read state, never change it. Depends on T006 and T020 (Owner: Andrea) — FR-010
- [ ] T022 [US4] In `controller/controlador.py` `jugar`, replace `self.vista.mostrar_estado(partida)` with `self.vista.mostrar_estado(self.servicio.estado_vista())`. Depends on T021 (Owner: Andrea) — FR-010
- [ ] T023 [US4] In `view/vista_consola.py`, rewrite `mostrar_estado(self, estado)` to print only from the DTO, with the same lines as today, and exit lines as `f"  {s.direccion} -> {s.nombre_destino} ({'cerrada' if s.cerrada else 'abierta'}, costo {s.costo})"`. In `view/vista_replay.py` and `view/vista_silenciosa.py`, rename the `mostrar_estado` parameter to `estado` and keep them as no-ops. Depends on T020 (Owner: Andrea) — FR-010

---

## Phase 7: User Story 5 — Exit costs are always current; old saves and logs are rejected by version (P2)

**Goal**: prove that the existing behaviour meets FR-011 and FR-012. No new invalidation mechanism.

- [ ] T024 [P] [US5] Write tests in `tests/test_version_cripta.py`, using fakes for the source and the catalog repository and no network (Owner: Andrea):
  - US5-1: a `RepositorioCripta` with a fake source whose `pagina_esqueleto` returns exits with `costo` → the built rooms carry those costs, and the fake records that the skeleton pages were requested (FR-011)
  - US5-2: `Aplicacion.validar_guardado` on a save whose header `version_cripta` differs returns the "otra cripta o versión" message (FR-012)
  - US5-3: `Aplicacion._versiones_coinciden` is False for a log with a different `version_cripta` (FR-012)
  - US5-4: a save with the matching version is accepted, and moves use the costs from the freshly built skeleton (FR-011, FR-012)
- [ ] T025 [US5] Check that no code path writes exit costs into saves (`adapters/guardado_binario.py`), logs (`adapters/bitacora_partida.py`) or the catalog cache (`adapters/almacen_fichas.py`), and that `VERSION_FORMATO` is unchanged. Record the result in the module docstring of `tests/test_version_cripta.py` (Owner: Andrea) — FR-011, FR-012

---

## Phase 8: Section 5.6 measurements (Emily)

- [ ] T026 [P] In `bench/bench_ciclo.py`, next to `armar_partida`, add a function that builds the same room chain with exit costs drawn from `random.Random(seed)` over {1, 10, 50, 100, 250, 500, 1000}, with the same cost on both sides of each door. Depends on T006 (Owner: Emily) — FR-014 (deterministic by seed, Constitution VI)
- [ ] T027 Extend `bench/bench_agenda.py`. Measure only the part-one candidates: `AgendaHeap`, `AgendaListaSinOrdenar`, `AgendaListaOrdenada`. Depends on T015 and T026 (Owner: Emily) — FR-003, FR-007, FR-014:
  - run `contar_operaciones` on the variable-cost builder with 300, 1000 and 3000 `errante` enemies
  - add a variable-increment version of `medir_ciclo`: increment = `intervalo(cost, speed)`, cost from the set above, speed in [50, 200]
  - print the fixed-increment and variable-increment results side by side
- [ ] T028 Run `python -m bench.bench_agenda` and fill the §Measurements table in `specs/001-exit-costs/plan.md` from `bench-parte1.txt` (T002) and T027. Apply the decision rule: keep the heap if it is the fastest, or within 10% of the fastest, at every size ≥ 300. If the rule fails, open a separate commit reopening the agenda decision (Owner: Emily) — FR-014

---

## Phase 9: Polish & cross-cutting

- [ ] T029 G1: in `tests/test_costos_salida.py`, run a seeded game for 500 player actions on rooms built by the T026 builder, with 50 wanderers and trackers, and with speed effects disabled (Owner: Emily) — FR-004, FR-006, FR-007, SC-002, SC-003:
  - Wrap `partida._programar_movimiento` to assert, at each call, that the newly scheduled `actor.evento.tiempo == partida.reloj + max(1, salida.costo * 100 // actor.velocidad)`.
  - Wrap `partida._programar_siguiente` to assert that every scheduled time is `> partida.reloj` (no action lasts 0).
  - Assert that at least one move was checked for every exit cost in the set.
- [ ] T030 SC-004 regression: in `tests/test_costos_salida.py`, a fixed seed and action sequence on rooms with no `costo` and on rooms with `costo` 100 everywhere produce identical `reloj`, rooms and HP for the player and every enemy (Owner: Emily) — FR-002, FR-014
- [ ] T031 FR-014 determinism: in `tests/test_costos_salida.py`, the same seed and actions on rooms with mixed costs, run twice, give identical final state. Same file as T030, so not parallel; do it after T030 (Owner: Emily) — FR-014
- [ ] T032 [P] G2: write `tests/test_replay_costos.py`. Run a game on rooms with mixed exit costs through `Controlador` with `VistaSilenciosa` and a `BitacoraPartida(tmp_path)` opened with a fixed crypt id, versions and seed, so every command is recorded. Close the log. Read it with `LectorBitacora` and replay its commands through a new `Partida(…, semilla=lector.semilla)` and `Controlador.ejecutar`, as `Aplicacion.reproducir` does. Compare `reloj`, player room and HP, and each enemy's id, room and HP. Use the fake fabrica from `tests/test_service.py`. Depends on T015 and T022 (Owner: Andrea) — FR-014
- [ ] T033 Run `python -m pytest`; all part-one tests stay green (Owners: Andrea, Emily) — FR-006, FR-008
- [ ] T034 Constitution gate, limited to new attributes or fields in the changed files that are used as an index or cache. Check that none of them is a `dict`, `set`, `heapq`, `bisect` or `collections` structure (`Salida.costo_declarado` is an int; the `EstadoVistaDTO` lists are display-only). Check that `model/` imports nothing from `view/`, `controller/` or `dto/estado_vista_dto.py`, and that `--replay`/`--bench`/`--verificar` never construct `VistaConsola` or call `estado_vista()` (Owners: Andrea for dto/data/service/controller/view, Emily for model/bench) — FR-015, Constitution I and III
- [ ] T035 Run the manual check in `specs/001-exit-costs/quickstart.md` (`python main.py`): exit lines show `costo`, and `Tiempo:` advances by `costo*100//velocidad` after a move (Owner: Andrea) — FR-010, FR-004

---

## Dependencies & Execution Order

```text
T001 (done) → T002                          baseline before any code
T003 ∥ T004 ∥ T005 ∥ T006                   Andrea: T003, T005 | Emily: T004, T006
T005 + T006 → T007 → T008 → T009            Andrea
Phase 2 → US1 (T010–T013) → US2 (T014–T015) → US3 (T016–T017)     Emily, same files
Phase 2 → US4 (T018–T023) ∥ US5 (T024–T025)                       Andrea
T006 → T026;  T015 + T026 → T027 → T028     Emily
T026 + T015 → T029 → T030 → T031            Emily, same file
T015 + T022 → T032                          Andrea
All → T033 → T034 → T035
```

- US1, US2 and US3 are sequential because they edit `model/partida_logica.py` and `tests/test_costos_salida.py`.
- Within US4, T018, T019 and T020 can start together. Then T021 → T022, and T023 after T020.
- US4 and US5 only need Phase 2, so Andrea can do them while Emily does US1–US3.

## Parallel Example

```text
After Phase 2:
  Andrea: T020 → T021 → T022 → T023 (tests T018, T019 alongside), then T024 → T025, then T032
  Emily:  T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017, with T026 alongside, then T027 → T028, then T029 → T030 → T031
```

## Implementation Strategy

1. **MVP**: Phase 1 + Phase 2 + US1. The player's moves take exit-dependent time, with FR-016 order verified.
2. Add US2 (enemies) and US3 (speed-change tests). This completes the timeline rules.
3. Add US4 (view DTO and costs in the view) and US5 (version tests) in parallel.
4. Phase 8 measurements, then Phase 9 (whole-game checks, determinism, replay, gates).
5. Commit per task group; a spec correction always goes in its own commit before the code that follows it (Constitution VII).
