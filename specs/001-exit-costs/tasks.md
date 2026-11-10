---

description: "Task list for Terrain — Exit Costs"
---

# Tasks: Terrain — Exit Costs

**Input**: Design documents from `specs/001-exit-costs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (skeleton-exit, room-view, service-boundary), quickstart.md

**Tests**: Required. Constitution IX says every acceptance scenario needs an automated test that cites its FR. Each owner writes the tests for her own tasks.

**Owners**:
- **Andrea**: data, all DTOs, every `JuegoService` method that hands data outward, controller, views, `aplicacion.py`, boundary, replay and version tests.
- **Emily**: engine model, move scheduling, section 5.6 measurements.

Every task is tagged `(Owner: …)`.

## Format: `[ID] [P?] [Story] Description (Owner) — FR`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: user story from spec.md (US1–US5)
- Every test function's docstring MUST cite its FR and scenario (or Constitution principle), e.g. `"""FR-004 · US1-5"""`.

## Path Conventions

Single-project layered layout at the repo root: `dto/`, `data/`, `model/`, `service/`, `controller/`, `view/`, `structures/`, `bench/`, `tests/`, plus `aplicacion.py`.

## Test files and owners

| File | Owner | Covers |
|---|---|---|
| `tests/test_costos_datos.py` (new) | Andrea | DTO reading, repository linking, inconsistent-door cost (US1-6, US1-7 at load time) |
| `tests/test_vista_costos.py` (new) | Andrea | `EstadoVistaDTO`, `estado_vista()`, room view output (US4) |
| `tests/test_frontera_servicio.py` (new) | Andrea | every service → controller/view/persistence crossing ([contracts/service-boundary.md](./contracts/service-boundary.md)) |
| `tests/test_service.py` (existing) | Andrea | `atacar(id_enemigo)` |
| `tests/test_version_cripta.py` (new) | Andrea | fresh skeleton, save/log version rejection (US5) |
| `tests/test_replay_costos.py` (new) | Andrea | record a log on a crypt with costs and replay it (FR-014) |
| `tests/test_costos_salida.py` (new) | Emily | move durations, FR-016 order, enemies, speed changes, determinism (US1–US3, SC-002–SC-005) |
| `tests/test_puertas.py` (existing) | Emily | `Salida.costo` / `enlazar` sharing rules |

**Common model fixture** (Emily's tests):
- Build `Sala`/`Salida` by hand and link them with `enlazar`, as `tests/test_puertas.py` does.
- Create actors with `Jugador(vida_max=…, ataque=…, defensa=…, velocidad=…, inventario_max=10, sala=…)` and `Enemigo(id_enemigo, tipo, nombre, vida, vida_max, ataque, defensa, velocidad, comportamiento, sala)`.
- Create the game with `Partida(jugador, semilla=1)` and add enemies with `partida.activar_enemigo(e)`.
- Give actors a huge `vida_max` and `defensa` when combat is not under test.

**Isolated enemy setup** (used in T014 and T016): before calling the method under test:
1. Put the player in a room different from the enemy's and from its destination.
2. Remove the enemy's pending activation turn with `partida.agenda.cancelar(enemigo.evento)`.

After that, the only pending action of that enemy is the one the method under test schedules.

---

## Phase 1: Setup

- [x] T001 Commit `specs/001-exit-costs/spec.md` and the plan artifacts before any code change, per Constitution VII. Done (Owner: Emily) — all FRs
- [x] T002 Run `python -m bench.bench_agenda` on the unchanged code and save the output to `specs/001-exit-costs/bench-parte1.txt` as the part-one baseline. Done in commit `08f9100` (Owner: Emily) — FR-014

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

- [ ] T014 [US2] Add to `tests/test_costos_salida.py`. Apply the isolated enemy setup in each case: player in another room, and the activation turn removed with `partida.agenda.cancelar(enemigo.evento)` (Owner: Emily):
  - US2-1: a wanderer with speed 100 in a room whose only open exit costs 200; the player is in a third room. Set `partida.reloj = T` and call `partida._actuar_enemigo(enemigo)` → the wanderer is in the destination room and `enemigo.evento.tiempo == T + 200` (FR-007, FR-016)
  - US2-2: a tracker in a room with two open exits (costs 250 and 40). Set the neighbouring rooms' `rastro` and `partida.reloj` so that both trails are within `RASTRO_VIGENCIA` and one is fresher. `partida._decidir_rastreador(enemigo)` returns the exit to the fresher trail, the same exit the part-one rule picks from that state, regardless of cost. Add a second case with equal trails: the tie goes to the lowest room id (FR-008)
  - US2-3: an enemy with speed 50, after the isolated setup, with `partida.reloj = T`: `partida._programar_movimiento(enemigo, salida)` on a cost-120 exit → `enemigo.evento.tiempo == T + 240` (FR-007). The docstring must state that the hunter spec must include an equivalent scenario using real hunter behaviour.

### Implementation

- [ ] T015 [US2] In the enemy turn in `model/partida_logica.py` (the block after `_decidir_errante` / `_decidir_rastreador`), when `salida is not None`, call `self._programar_movimiento(enemigo, salida)`; otherwise keep `self._programar_siguiente(enemigo, COSTO_ESPERAR)`. Update the comment "Atacar, moverse y esperar cuesta 100". Do not touch `_decidir_errante` or `_decidir_rastreador` (Owner: Emily) — FR-006, FR-007, FR-008, FR-016

---

## Phase 5: User Story 3 — Speed change while waiting for the next action (P1)

**Goal**: confirm that the existing rescaling (`EfectosLogica._cambiar_velocidad` → `nuevo_tiempo_por_velocidad` → `agenda.reprogramar`) applies to the next action scheduled by a move. No production code change is expected.

- [ ] T016 [US3] Add to `tests/test_costos_salida.py`, following plan.md "Timing semantics". Use an **enemy**, so the pending event can be inspected without advancing to it (Owner: Emily) — FR-009 (US3-3 also FR-006):
  - Setup for each case:
    1. Apply the isolated enemy setup (player in another room, activation turn cancelled).
    2. Set `partida.reloj` to the move time (0 unless stated) and call `partida._programar_movimiento(enemigo, salida)` on an exit with the given cost; keep `ev = enemigo.evento`.
    3. Set `partida.reloj` to the change time and call `partida.efectos.aplicar_velocidad(enemigo, nueva - vieja, 10**6)`. The long duration keeps the end-of-effect event out of the way.
  - US3-1: speed 100, cost 500 (event at 500); at reloj 100 change to 200 → `ev.tiempo == 300`
  - US3-2: speed 200, cost 2000 (event at 1000); at reloj 900 change to 50 → `ev.tiempo == 1300`
  - US3-3: speed 10, cost 1, scheduled at reloj 91 (event at 101); at reloj 100 change to 1000 → `ev.tiempo == 101` (remaining = max(1, 1×10//1000) = 1)
  - One player-level case: at reloj 0, before moving, apply a speed effect with `aplicar_velocidad(jugador, +100, 100)`. The effect ends at t=100, while the player waits for their next action. Check that the player's next action ends at `100 + max(1, (end − 100) × 200 // 100)`, where `end` is the time scheduled at the faster speed.
- [ ] T017 [US3] If any T016 test fails, fix it in `model/efectos_logica.py` without changing `nuevo_tiempo_por_velocidad` in `model/tiempo_logica.py`. Otherwise mark this task done with no change (Owner: Emily) — FR-009

---

## Phase 6: User Story 4 — The player sees the cost of each exit (P2)

**Goal**: the room view is drawn from `EstadoVistaDTO`, and exit lines read `N -> Pasillo (abierta, costo 300)` (contracts/room-view.md).

### Tests

- [ ] T018 [P] [US4] Write tests in `tests/test_vista_costos.py`. Build the service like `armar_servicio()` in `tests/test_service.py` (Owner: Andrea) — FR-010:
  - US4-1: `servicio.estado_vista().salidas` has `norte` with `costo 300` and `sur` with `costo 100`
  - US4-2: a closed exit with cost 40 has `cerrada is True` and `costo 40`
  - `VistaConsola().mostrar_estado(estado)`, captured with `capsys`, prints `(abierta, costo 300)`, `(abierta, costo 100)` and `(cerrada, costo 40)`
  - The rest of the output is identical to the part-one format for the same state: room line, `Tiempo:`, player lines, enemies (same filter as today), traps, objects, last 20 log lines
- [ ] T019 [US4] Add to `tests/test_vista_costos.py`, after T018 (same file): run `Controlador.jugar` for one loop iteration with a fake view. The fake view implements `mostrar_estado`, `pedir_comando` (returns `"salir"`), `mostrar_mensaje` and `mostrar_final`, and records the arguments it receives. Use `persistencia=None`. Assert that `mostrar_estado` received an `EstadoVistaDTO`, not a `Partida`. Assert that `mostrar_final` received a `ResumenFinalDTO` (only passes once T030 is done) (Owner: Andrea) — FR-010, Constitution III

### Implementation

- [ ] T020 [P] [US4] Create `dto/estado_vista_dto.py` with `EstadoVistaDTO`, `JugadorVistaDTO`, `SalidaVistaDTO`, `EnemigoVistaDTO`, `TrampaVistaDTO` and `ObjetoVistaDTO`, with exactly the fields in data-model.md "EstadoVistaDTO". `SalidaVistaDTO.costo` is "int, already resolved: declared or 100". Use plain classes and plain lists, and import nothing from `model/` (Owner: Andrea) — FR-010
- [ ] T021 [US4] Add `JuegoService.estado_vista(self)` in `service/juego_service.py`. It builds an `EstadoVistaDTO` from `self.partida`, following the "From" column in data-model.md: exits in room order with `salida.costo`; enemies where `enemigo.sala is sala`; `bitacora.obtener_todos()[-20:]`. It must only read state, never change it. Depends on T006 and T020 (Owner: Andrea) — FR-010
- [ ] T022 [US4] In `controller/controlador.py` `jugar`, replace `self.vista.mostrar_estado(partida)` with `self.vista.mostrar_estado(self.servicio.estado_vista())`. Depends on T021 (Owner: Andrea) — FR-010
- [ ] T023 [US4] In `view/vista_consola.py`, rewrite `mostrar_estado(self, estado)` to print only from the DTO, with the same lines as today, and exit lines as `f"  {s.direccion} -> {s.nombre_destino} ({'cerrada' if s.cerrada else 'abierta'}, costo {s.costo})"`. In `view/vista_replay.py` and `view/vista_silenciosa.py`, rename the `mostrar_estado` parameter to `estado` and keep them as no-ops. Depends on T020 (Owner: Andrea) — FR-010

---

## Phase 7: User Story 5 — Exit costs are always current; old saves and logs are rejected by version (P2)

**Goal**: prove that the existing behaviour meets FR-011 and FR-012. No new invalidation mechanism.

- [ ] T024 [P] [US5] Write tests in `tests/test_version_cripta.py`, using fakes and no network (Owner: Andrea):
  - US5-1: a `RepositorioCripta` with a fake source whose `datos_cripta` and `pagina_esqueleto` return a one-page skeleton whose exits declare `costo` → `cargar_esqueleto` + `construir_salas` give rooms carrying those costs, and the fake records that the skeleton page was requested (FR-011)
  - US5-2: `validar_guardado` on a save whose header `version_cripta` differs returns the "otra cripta o versión" message. Call it as `Aplicacion.validar_guardado(fake_app, ruta)`, where `fake_app` has `repo_cripta.datos` and `repo_catalogo.version()`, so no real `Aplicacion` is built. Write the save with `GuardadoBinario().guardar` into `tmp_path` (FR-012)
  - US5-3: `Aplicacion._versiones_coinciden(fake_app, lector)` is False for a lector with a different `version_cripta` (FR-012)
  - US5-4 (repository level): `aplicacion.py` loads a save in `_sesion` → `_reiniciar_salas`, which calls `repo_cripta.construir_salas(self.dtos)` with the skeleton DTOs downloaded at start. Reproduce that step: build rooms from the same DTOs twice with `construir_salas`, as a load does. Check that the second build has the same costs from the DTOs, and that `validar_guardado` accepts a save whose versions match (FR-011, FR-012)
- [ ] T025 [US5] Check that no code path writes exit costs into saves (`adapters/guardado_binario.py`), logs (`adapters/bitacora_partida.py`) or the catalog cache (`adapters/almacen_fichas.py`), and that `VERSION_FORMATO` is unchanged. Record the result in the module docstring of `tests/test_version_cripta.py` (Owner: Andrea) — FR-011, FR-012

---

## Phase 8: Service boundary (Constitution III, cross-cutting — Andrea)

**Goal**: everything the service hands outward is a DTO or plain value ([contracts/service-boundary.md](./contracts/service-boundary.md)). The controller never reads the game model, and no view method receives a model object. Printed output is unchanged apart from exit costs.

### Tests

- [ ] T026 [P] Write `tests/test_frontera_servicio.py`, building the service with `armar_servicio()` from `tests/test_service.py` (Owner: Andrea) — FR-010, FR-014, Constitution III:
  - Each of `estado_vista`, `resumen_final`, `inventario_vista`, `vista_ordenada(c)` (for `peso`, `valor`, `nombre`), `objetos_en_sala` and `enemigos_en_sala` returns no instance of a class defined in `model/`. Walk DTO attributes and lists recursively and check each value's `type(x).__module__` does not start with `model.`
  - `terminada()` returns a bool and `semilla()` an int
  - `enemigos_en_sala()` lists only living enemies in the player's room, in `partida.enemigos` order
  - `atacar("r1")` with the rat in the room returns True and defeats it. `atacar("x")` returns False and changes nothing
  - `controller/controlador.py` contains no `.partida` and no `from model` (read the file text)
  - Capture with `capsys` the output of the new `mostrar_final(resumen)`, `mostrar_inventario(inv)` and `mostrar_inventario_ordenado(lista, c)` in `VistaConsola`, and `mostrar_final` in `VistaReplay`. Compare it with expected strings built for the same state in the part-one format, which is unchanged
- [ ] T027 [P] Update `tests/test_service.py` `test_servicio_esperar_y_atacar` to call `servicio.atacar("r1")` instead of `servicio.atacar(rata)` (Owner: Andrea) — FR-006, Constitution III

### Implementation

- [ ] T028 [P] Create `dto/resumen_final_dto.py` (`ResumenFinalDTO`) and `dto/inventario_vista_dto.py` (`InventarioVistaDTO`, `ObjetoInventarioDTO`), with exactly the fields in data-model.md "Other service boundary DTOs". Use plain classes and lists, and import nothing from `model/` (Owner: Andrea) — Constitution III
- [ ] T029 In `service/juego_service.py`, add the methods below, as in data-model.md "Lists and plain values". Depends on T020 and T028 (Owner: Andrea) — FR-006, Constitution III:
  - `resumen_final()`, `inventario_vista()`, `objetos_en_sala()`, `enemigos_en_sala()`, `terminada()` and `semilla()`
  - change `vista_ordenada(criterio)` to return a list of `ObjetoInventarioDTO` in the order of `inventario.vista_ordenada`
  - change `atacar(enemigo)` to `atacar(id_enemigo)`: resolve it as the first enemy in `partida.enemigos` with `str(e.id_enemigo).lower() == str(id_enemigo).lower()`, `e.sala is jugador.sala` and `e.esta_vivo()`. Return False if there is none; otherwise call `partida.atacar(e)` and `actualizar_fichas()` as today
- [ ] T030 In `controller/controlador.py`, remove every read of the game model. Depends on T029 (Owner: Andrea) — Constitution III:
  - `jugar`: loop on `self.servicio.terminada()`; then `resumen = self.servicio.resumen_final()`, `self.vista.mostrar_final(resumen)` and `self.persistencia.registrar_puntaje(resumen)` when `resumen.victoria or resumen.terminada`
  - `_cmd_recoger`: use `self.servicio.objetos_en_sala()`
  - `_enemigos_en_sala` / `_elegir_enemigo`: use `self.servicio.enemigos_en_sala()` and return the chosen `id_enemigo`; `_cmd_atacar` calls `self.servicio.atacar(id_enemigo)`
  - `_cmd_inventario`: `self.vista.mostrar_inventario(self.servicio.inventario_vista())`
  - `_cmd_guardar`: `self.persistencia.guardar_partida(self.servicio.semilla(), self.comandos, nombre)`
  
  No `self.servicio.partida` may remain.
- [ ] T031 In the views, print from DTOs with the same text as today. Depends on T028 (Owner: Andrea) — Constitution III:
  - `view/vista_consola.py`: `mostrar_final(resumen)` prints all of `resumen.bitacora` (the last 20); `mostrar_inventario(inv)`, with the `>` marker from `actual` and ` (equipado)` from `equipado`; `mostrar_inventario_ordenado(objetos, criterio)` with DTO fields
  - `view/vista_replay.py`: `mostrar_final(resumen)` prints `resumen.bitacora[-6:]`; rename the `mostrar_inventario` parameter
  - `view/vista_silenciosa.py`: rename the parameters; the methods stay no-ops
- [ ] T032 In `aplicacion.py`, after the game is built, only talk to it through the service. Depends on T029 (Owner: Andrea) — FR-012, FR-014, Constitution III:
  - `_reejecutar`: `controlador.servicio.terminada()`
  - `reproducir`: loop on `servicio.terminada()` and call `vista.mostrar_final(servicio.resumen_final())`
  - `guardar_partida(self, semilla, comandos, nombre)` uses `semilla`
  - `registrar_puntaje(self, resumen)` builds `Puntaje(resumen.nombre_jugador, datos.id_cripta, datos.version, resumen.acciones, resumen.enemigos_derrotados, resumen.reloj, resumen.victoria)`
  
  Building the game in `_sesion` (`fabrica.nueva_partida`, setting the player's name) stays as it is.

**Checkpoint**: `python -m pytest tests/test_frontera_servicio.py tests/test_service.py tests/test_vista_costos.py` is green, and a text search finds no `servicio.partida` outside `service/`.

---

## Phase 9: Section 5.6 measurements (Emily)

- [ ] T033 [P] In `bench/bench_ciclo.py`, next to `armar_partida`, add `armar_partida_costos(num_salas, num_enemigos, semilla)`. It builds the same room chain with exit costs drawn from `random.Random(semilla)` over {1, 10, 50, 100, 250, 500, 1000}, with the same cost on both sides of each door. Depends on T006 (Owner: Emily) — FR-014 (deterministic by seed, Constitution VI)
- [ ] T034 Extend `bench/bench_agenda.py`. Measure only the part-one candidates: `AgendaHeap`, `AgendaListaSinOrdenar`, `AgendaListaOrdenada`. Depends on T015 and T033 (Owner: Emily) — FR-003, FR-007, FR-014:
  - run `contar_operaciones` on `armar_partida_costos` with 300, 1000 and 3000 `errante` enemies
  - add a variable-increment version of `medir_ciclo`: increment = `intervalo(cost, speed)`, cost from the set above, speed in [50, 200]
  - print the fixed-increment and variable-increment results side by side
- [ ] T035 Run `python -m bench.bench_agenda` and fill the §Measurements table in `specs/001-exit-costs/plan.md` from `bench-parte1.txt` (T002) and T034. Apply the decision rule: keep the heap if it is the fastest, or within 10% of the fastest, at every size ≥ 300. If the rule fails, open a separate commit reopening the agenda decision (Owner: Emily) — FR-014

---

## Phase 10: Polish & cross-cutting

- [ ] T036 G1: in `tests/test_costos_salida.py`, run a seeded game on rooms built by `armar_partida_costos` (Owner: Emily) — FR-004, FR-006, FR-007, SC-002, SC-003:
  - The test imports this builder from `bench/bench_ciclo.py`. That dependency on benchmark code is accepted, so the test and the benchmark use the same costed crypt.
  - Use a fixed seed, 50 wanderers and trackers, and a fixed sequence of 500 player actions (moves and waits). No speed effects are applied.
  - A fixed seed plus a fixed action sequence is a replayed game in the sense of SC-002: running it again reproduces the same game (FR-014).
  - Wrap `partida._programar_movimiento` to assert, at each call, that the newly scheduled `actor.evento.tiempo == partida.reloj + max(1, salida.costo * 100 // actor.velocidad)`.
  - Wrap `partida._programar_siguiente` to assert that every scheduled time is `> partida.reloj` (no action lasts 0).
  - Assert that at least one move was checked for every exit cost in the set.
  
  Depends on T015 and T033.
- [ ] T037 SC-004 regression: in `tests/test_costos_salida.py`, a fixed seed and action sequence on rooms with no `costo` and on rooms with `costo` 100 everywhere produce identical `reloj`, rooms and HP for the player and every enemy (Owner: Emily) — FR-002, FR-014
- [ ] T038 FR-014 determinism: in `tests/test_costos_salida.py`, the same seed and actions on rooms with mixed costs, run twice, give identical final state. Same file as T037, so not parallel; do it after T037 (Owner: Emily) — FR-014
- [ ] T039 [P] G2: write `tests/test_replay_costos.py` (Owner: Andrea) — FR-014:
  - Define a helper `armar_salas(semilla)` that builds a fresh set of rooms with mixed exit costs (and the same enemies) from `random.Random(semilla)`. Call it once for the recording and once for the replay, with the same seed, so the replay never reuses rooms the recorded game changed.
  - Recording: build a service on `armar_salas(7)`, with the fake fabrica from `tests/test_service.py`. Run a fixed command list through `Controlador.ejecutar` with `VistaSilenciosa` and a `BitacoraPartida(tmp_path)` opened with a fixed crypt id, versions and seed. Close the log.
  - Replay: read the log with `LectorBitacora`. Build a new service on `armar_salas(7)` with `Partida(…, semilla=lector.semilla)`, and replay `lector.comandos` through `Controlador.ejecutar`, as `Aplicacion.reproducir` does.
  - Compare `resumen_final()` (clock, victory, actions) and `estado_vista()` (room, player HP, enemies in the room) between the two runs.
  
  Depends on T015 and T030.
- [ ] T040 Run `python -m pytest`; all part-one tests stay green (Owners: Andrea, Emily) — FR-006, FR-008
- [ ] T041 Constitution gate, limited to new attributes or fields in the changed files that are used as an index or cache (Owners: Andrea for dto/data/service/controller/view/aplicacion, Emily for model/bench) — FR-015, Constitution I and III:
  - None of them is a `dict`, `set`, `heapq`, `bisect` or `collections` structure. `Salida.costo_declarado` is an int; the DTO lists are display-only.
  - `model/` imports nothing from `view/`, `controller/` or `dto/` view modules, and `dto/` imports nothing from `model/`.
  - `--replay` and `--bench` never construct `VistaConsola`.
- [ ] T042 Run the manual check in `specs/001-exit-costs/quickstart.md` (`python main.py`) (Owner: Andrea) — FR-010, FR-004:
  - exit lines show `costo`
  - `Tiempo:` advances by `costo*100//velocidad` after a move
  - `inv`, `inv peso`, `atacar`, `recoger`, `guardar` and the end screen behave as in part one

---

## Dependencies & Execution Order

```text
T001, T002 (done)
T003 ∥ T004 ∥ T005 ∥ T006                     Andrea: T003, T005 | Emily: T004, T006
T005 + T006 → T007 → T008 → T009              Andrea
Phase 2 → US1 (T010–T013) → US2 (T014–T015) → US3 (T016–T017)       Emily, same files
Phase 2 → US4 (T018–T023) → Boundary (T026–T032)                     Andrea
Phase 2 → US5 (T024–T025)                                            Andrea, any time after Phase 2
T006 → T033;  T015 + T033 → T034 → T035       Emily
T015 + T033 → T036 → T037 → T038              Emily, same file
T015 + T030 → T039                            Andrea
All → T040 → T041 → T042
```

- US1, US2 and US3 are sequential because they edit `model/partida_logica.py` and `tests/test_costos_salida.py`.
- Andrea's chain: within US4, T018 and T020 start together (T019 follows T018 in the same file); then T021 → T022, and T023 after T020. The boundary phase follows: T026, T027 and T028 in parallel, then T029 → T030 / T031 / T032. T019's `mostrar_final` assertion passes only after T030.
- US5 (T024–T025) only needs Phase 2 and can slot in anywhere in Andrea's chain.

## Parallel Example

```text
After Phase 2:
  Andrea: T020 → T021 → T022 → T023 (tests T018, T019 alongside) → T028 → T029 → T030 → T031 → T032
          (tests T026, T027 alongside), T024 → T025, then T039
  Emily:  T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017, with T033 alongside,
          then T034 → T035, then T036 → T037 → T038
```

## Implementation Strategy

1. **MVP**: Phase 1 + Phase 2 + US1. The player's moves take exit-dependent time, with FR-016 order verified.
2. Add US2 (enemies) and US3 (speed-change tests). This completes the timeline rules.
3. Add US4 (room view with costs) and then the service boundary phase, which closes Constitution III. US5 version tests go alongside.
4. Phase 9 measurements, then Phase 10 (whole-game checks, determinism, replay, gates).
5. Commit per task group; a spec correction always goes in its own commit before the code that follows it (Constitution VII).
