---

description: "Task list for Terrain — Exit Costs"
---

# Tasks: Terrain — Exit Costs

**Input**: Design documents from `specs/001-exit-costs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (skeleton-exit, room-view, service-boundary), quickstart.md

**Tests**: Required. Constitution IX says every acceptance scenario needs an automated test that cites its FR, and every task cites at least one FR.

**Owner**: Emily owns this feature end to end (spec, plan, every task and every test) and implements it with the agent. Tasks therefore carry no per-task owner tag.

## Format: `[ID] [P?] [Story] Description — FR`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: user story from spec.md (US1–US5)
- Every test function's docstring MUST cite its FR and scenario (plus the Constitution principle where relevant), e.g. `"""FR-004 · US1-5"""`.

## Path Conventions

Single-project layered layout at the repo root: `dto/`, `data/`, `model/`, `service/`, `controller/`, `view/`, `adapters/`, `structures/`, `bench/`, `tests/`, plus `aplicacion.py`.

## Test files

| File | Covers |
|---|---|
| `tests/estado_fijo.py` (new helper, not a test module) | `FabricaFalsa`, fixed game states, `AppFalsa`, `LectorFalso`, `cargar_golden(nombre)`; imports nothing from other test modules |
| `tests/test_costos_datos.py` (new) | DTO reading, repository linking, inconsistent-door cost (US1-6, US1-7 at load time) |
| `tests/test_vista_costos.py` (new) | `EstadoVistaDTO`, `estado_vista()`, room view output vs golden (US4) |
| `tests/test_frontera_servicio.py` (new) | every service → controller/view/persistence crossing ([contracts/service-boundary.md](./contracts/service-boundary.md)) |
| `tests/test_service.py` (existing) | `atacar(id_enemigo)` |
| `tests/test_salida_replay.py` (new) | replay output vs golden, no `view/` class in `--replay` |
| `tests/test_version_cripta.py` (new) | fresh skeleton, save/log version rejection (US5) |
| `tests/test_replay_costos.py` (new) | record a log on a crypt with costs and replay it (FR-014) |
| `tests/test_costos_salida.py` (new) | move durations, FR-016 order, enemies, speed changes, determinism (US1–US3, SC-002–SC-005) |
| `tests/test_puertas.py` (existing) | `Salida.costo` / `enlazar` sharing rules |

**Common model fixture** (model tests):
- Build `Sala`/`Salida` by hand and link them with `enlazar`, as `tests/test_puertas.py` does.
- Create actors with `Jugador(vida_max=…, ataque=…, defensa=…, velocidad=…, inventario_max=10, sala=…)` and `Enemigo(id_enemigo, tipo, nombre, vida, vida_max, ataque, defensa, velocidad, comportamiento, sala)`.
- Create the game with `Partida(jugador, semilla=1)` and add enemies with `partida.activar_enemigo(e)`.
- Give actors a huge `vida_max` and `defensa` when combat is not under test.

**Isolated enemy setup** (used in T015 and T017): before calling the method under test:
1. Put the player in a room different from the enemy's and from its destination.
2. Remove the enemy's pending activation turn with `partida.agenda.cancelar(enemigo.evento)`.

After that, the only pending action of that enemy is the one the method under test schedules.

---

## Phase 1: Setup

- [x] T001 Commit `specs/001-exit-costs/spec.md` and the plan artifacts before any code change, per Constitution VII. Done — all FRs
- [x] T002 Run `python -m bench.bench_agenda` on the unchanged code and save the output to `specs/001-exit-costs/bench-parte1.txt` as the part-one baseline. Done in commit `08f9100` — FR-014
- [ ] T003 Golden output of the part-one views, captured **before any change to `view/`, `controller/`, `service/` or `aplicacion.py`** — FR-010, FR-014:
  - Create `tests/estado_fijo.py` (a helper, not a test module). It imports nothing from other test modules and contains:
    - `FabricaFalsa`, defined here (same behaviour as the one in `tests/test_service.py`, but not imported from it): `poblar_sala(sala)` records the room id, `marcar_en_uso(ids)` records the ids, and `nueva_partida(semilla)` returns `armar_estado_fijo()[1]`, a **freshly built** game on every call.
    - `armar_estado_fijo(final=None)`: builds a new `JuegoService` with a fixed seed and a new `FabricaFalsa`, following the pattern of `armar_servicio()` in `tests/test_service.py`. Every call builds new rooms, actors and game; nothing is shared between calls. The state has two linked rooms (one open exit, one closed with a key), one enemy with an effect in the player's room, one armed trap, two objects in the room, three objects in the inventory (one equipped, so `actual` is set), and at least 25 log lines. `final` is `None`, `"victoria"`, `"muerte"` or `"salida"` and sets `partida.victoria` / `partida.terminada` to match. Returns `(servicio, partida)`.
    - `LectorFalso(semilla, comandos, version_cripta, version_catalogo)`.
    - `AppFalsa(version_cripta, version_catalogo)`, with the attributes `reproducir` reads: `fabrica`, a new `FabricaFalsa` whose `nueva_partida` builds a fresh game from `armar_estado_fijo()` on every call; `repo_cripta.datos.version`; `repo_catalogo.version()` and its hit/miss counters; `cliente.solicitudes` and `cliente.presupuesto`. Set `_versiones_coinciden = Aplicacion._versiones_coinciden` and `_reportar = Aplicacion._reportar`. Every `reproducir` call MUST use a new `AppFalsa`; never reuse one between calls.
    - `cargar_golden(nombre)`: reads `specs/001-exit-costs/salida-parte1/<nombre>`.
  - Create `tests/capturar_salida_parte1.py` (run once with `python -m tests.capturar_salida_parte1`). It redirects stdout and writes these files to `specs/001-exit-costs/salida-parte1/`:
    - `estado.txt`: `VistaConsola().mostrar_estado(partida)`
    - `final_consola_{victoria,muerte,salida}.txt`: `VistaConsola().mostrar_final(partida)`
    - `inventario.txt`: `VistaConsola().mostrar_inventario(partida)`
    - `inventario_{peso,valor,nombre}.txt`: `VistaConsola().mostrar_inventario_ordenado(servicio.vista_ordenada(c), c)`
    - `final_replay_{victoria,muerte,salida}.txt`: `VistaReplay().mostrar_final(partida)`
    - `reporte_replay.txt` and `reporte_replay_sin_presupuesto.txt`: `VistaReplay().mostrar_reporte(12, 50, 7, 3)` and `(12, None, 0, 0)`
    - `replay_completo.txt`: `Aplicacion.reproducir(AppFalsa(v, v), LectorFalso(1, ["w", "d", "esperar", "zz"], v, v))`, with matching versions and a new `AppFalsa`. The commands include one blocked move and one unknown command, so controller messages are printed.
    - `replay_version.txt`: the same call with another new `AppFalsa(v, v)` and a lector whose `version_cripta` differs
    - Each capture of the views uses its own `armar_estado_fijo(...)` call, so no capture sees a game changed by another.
  - Commit `tests/estado_fijo.py`, `tests/capturar_salida_parte1.py` and the golden files in one commit before T021.

---

## Phase 2: Foundational (blocking all user stories)

**Purpose**: every exit carries a cost from the skeleton into the model. The DTO change (T006) and the `Salida` attribute (T007) touch different files and can be done in either order; the repository (T008) needs both.

### Tests

- [ ] T004 [P] Write tests in `tests/test_costos_datos.py` for `SalidaDTO.desde_json` — FR-001, FR-002:
  - `{"sala": 2, "costo": 300}` gives `costo == 300`
  - `{"sala": 2}` gives `costo is None` (not 100)
- [ ] T005 [P] Write tests in `tests/test_puertas.py` for `Salida`, using the linking table from data-model.md — FR-002, FR-005:
  - None/None → both `costo == 100`
  - x/None → both x
  - None/y → both y
  - x/x → both x
  - an exit with no opposite returns its declared value, or 100
  - `costo_declarado` stays `None` when neither side declares one

### Implementation

- [ ] T006 [P] In `dto/salida_dto.py`, add `costo` to `SalidaDTO.__init__` (default `None`) and read it in `desde_json` with `datos.get("costo")`. "`None` = not declared. No range check (FR-001)" — FR-001, FR-002
- [ ] T007 [P] In `model/sala_logica.py` — FR-002, FR-005:
  - Add `Salida.__init__(..., costo=None)`, storing `self.costo_declarado`.
  - Add a read-only property `costo` returning `costo_declarado`, or `COSTO_MOVER` (imported from `model/tiempo_logica.py`) when it is `None`.
  - In `enlazar`, copy a non-`None` `costo_declarado` to the side whose value is `None`, the same way `llave` is shared.
- [ ] T008 In the second loop of `construir_salas` in `data/repositorio_cripta.py`, pass `costo=salida_dto.costo` when creating each `Salida`. Depends on T006 and T007 — FR-001, FR-011
- [ ] T009 In the third loop of `construir_salas` in `data/repositorio_cripta.py`, before `salida.enlazar(otra)`: if `salida.costo_declarado` and `otra.costo_declarado` are both not `None` and differ, raise `ValueError` starting with "Puerta inconsistente:" that names both rooms, both directions and both costs. Use the same message style as the existing check. Depends on T008 — FR-013
- [ ] T010 Add to `tests/test_costos_datos.py`, building rooms with `RepositorioCripta.construir_salas` from `SalaDTO`s. Depends on T009 — FR-005, FR-013:
  - A→B declares 300 and B→A declares nothing → both exits cost 300 (US1-7 at load)
  - sides declare 100 and 200 → `ValueError` matching "Puerta inconsistente" (US1-6)
  - the existing room-mismatch inconsistent door still raises

**Checkpoint**: `python -m pytest tests/test_costos_datos.py tests/test_puertas.py` is green, and every exit in the model has `costo`.

---

## Phase 3: User Story 1 — Movement duration depends on the exit crossed (P1) 🎯 MVP

**Goal**: when the player moves through an exit at T, the player is in the destination room at T and their next action is at `T + intervalo(salida.costo, velocidad)`.

**Independent test**: build rooms with exit costs, record `T = partida.reloj`, call `partida.mover(dir)`, then check `partida.jugador.sala` and the player's next action time.

### Tests

- [ ] T011 [US1] Write tests in `tests/test_costos_salida.py` using the common fixture. Read the next action time as `partida.jugador.evento.tiempo` right after `partida.mover`; `mover` advances the clock to that action, so `partida.reloj` equals it after the call — FR-002, FR-003, FR-004, FR-005, FR-006, FR-016:
  - US1-1: cost 300, speed 100, move at T → player is in the destination room and next action is at T+300 (FR-003, FR-004, FR-016)
  - US1-2: no cost → T+100 (FR-002, FR-004)
  - US1-3: both sides declare 250 → A→B and then B→A each take 250 (FR-005)
  - US1-4: cost 50, speed 150 → T+33 (FR-004)
  - US1-5: cost 1, speed 1000 → T+1 (FR-004, FR-006)
  - US1-7: only A→B declares 300 → moving B→A takes 300 (FR-005)
  - US1-8: in a room whose exits cost 500, `atacar` and `esperar_jugador` take the part-one intervals (FR-006)
- [ ] T012 [US1] Add FR-016 order tests to `tests/test_costos_salida.py`. Wrap `partida._programar_movimiento` (after T013) with a test double that records `partida.jugador.sala`, `partida.reloj` and the destination's trail mark when it is called, then calls the original — FR-016:
  - the player is already in the destination room at T, before the next action is scheduled
  - the destination room's trail mark is T (`sala.rastro == T`)
  - an armed trap in the destination room fires at T, before the next action
  - entering the exit room ends the game at T with victory, and no next action is scheduled

### Implementation

- [ ] T013 [US1] In `model/partida_logica.py`, add `Partida._programar_movimiento(self, actor, salida)`, which calls `self._programar_siguiente(actor, salida.costo)`. Do not modify `intervalo` or `nuevo_tiempo_por_velocidad` — FR-003, FR-004, FR-007
- [ ] T014 [US1] In `Partida.mover` (`model/partida_logica.py`), replace `self._programar_siguiente(self.jugador, COSTO_MOVER)` with `self._programar_movimiento(self.jugador, salida)`. Keep the existing order: refresh trail → `_entrar_en_sala` → traps → victory → schedule. Remove `COSTO_MOVER` from that file's import if it is no longer used there — FR-003, FR-016

**Checkpoint**: US1 tests green; MVP done.

---

## Phase 4: User Story 2 — Enemies are subject to the same exit costs (P1)

**Goal**: enemy moves use the exit cost and follow FR-016; the decision rules are unchanged.

### Tests

- [ ] T015 [US2] Add to `tests/test_costos_salida.py`. Apply the isolated enemy setup in each case: player in another room, and the activation turn removed with `partida.agenda.cancelar(enemigo.evento)` — FR-007, FR-008, FR-016:
  - US2-1: a wanderer with speed 100 in a room whose only open exit costs 200; the player is in a third room. Set `partida.reloj = T` and call `partida._actuar_enemigo(enemigo)` → the wanderer is in the destination room and `enemigo.evento.tiempo == T + 200` (FR-007, FR-016)
  - US2-2: a tracker in a room with two open exits (costs 250 and 40). Set the neighbouring rooms' `rastro` and `partida.reloj` so that both trails are within `RASTRO_VIGENCIA` and one is fresher. `partida._decidir_rastreador(enemigo)` returns the exit to the fresher trail, the same exit the part-one rule picks from that state, regardless of cost. Add a second case with equal trails: the tie goes to the lowest room id (FR-008)
  - US2-3: an enemy with speed 50, after the isolated setup, with `partida.reloj = T`: `partida._programar_movimiento(enemigo, salida)` on a cost-120 exit → `enemigo.evento.tiempo == T + 240` (FR-007). The docstring must state that the hunter spec must include an equivalent scenario using real hunter behaviour.

### Implementation

- [ ] T016 [US2] In the enemy turn in `model/partida_logica.py` (the block after `_decidir_errante` / `_decidir_rastreador`), when `salida is not None`, call `self._programar_movimiento(enemigo, salida)`; otherwise keep `self._programar_siguiente(enemigo, COSTO_ESPERAR)`. Update the comment "Atacar, moverse y esperar cuesta 100". Do not touch `_decidir_errante` or `_decidir_rastreador` — FR-006, FR-007, FR-008, FR-016

---

## Phase 5: User Story 3 — Speed change while waiting for the next action (P1)

**Goal**: confirm that the existing rescaling (`EfectosLogica._cambiar_velocidad` → `nuevo_tiempo_por_velocidad` → `agenda.reprogramar`) applies to the next action scheduled by a move. No production code change is expected.

- [ ] T017 [US3] Add to `tests/test_costos_salida.py`, following plan.md "Timing semantics". Use an **enemy**, so the pending event can be inspected without advancing to it — FR-009 (US3-3 also FR-006):
  - Setup for each case:
    1. Apply the isolated enemy setup (player in another room, activation turn cancelled).
    2. Set `partida.reloj` to the move time (0 unless stated) and call `partida._programar_movimiento(enemigo, salida)` on an exit with the given cost; keep `ev = enemigo.evento`.
    3. Set `partida.reloj` to the change time and call `partida.efectos.aplicar_velocidad(enemigo, nueva - vieja, 10**6)`. The long duration keeps the end-of-effect event out of the way.
  - US3-1: speed 100, cost 500 (event at 500); at reloj 100 change to 200 → `ev.tiempo == 300`
  - US3-2: speed 200, cost 2000 (event at 1000); at reloj 900 change to 50 → `ev.tiempo == 1300`
  - US3-3: speed 10, cost 1, scheduled at reloj 91 (event at 101); at reloj 100 change to 1000 → `ev.tiempo == 101` (remaining = max(1, 1×10//1000) = 1)
  - One player-level case: at reloj 0, before moving, apply a speed effect with `aplicar_velocidad(jugador, +100, 100)`. The effect ends at t=100, while the player waits for their next action. Check that the player's next action ends at `100 + max(1, (end − 100) × 200 // 100)`, where `end` is the time scheduled at the faster speed.
- [ ] T018 [US3] If any T017 test fails, fix it in `model/efectos_logica.py` without changing `nuevo_tiempo_por_velocidad` in `model/tiempo_logica.py`. Otherwise mark this task done with no change — FR-009

---

## Phase 6: User Story 4 — The player sees the cost of each exit (P2)

**Goal**: the room view is drawn from `EstadoVistaDTO`, and exit lines read `N -> Pasillo (abierta, costo 300)` (contracts/room-view.md). This phase is self-contained: its checkpoint does not depend on the boundary phase.

### Tests

- [ ] T019 [P] [US4] Write tests in `tests/test_vista_costos.py`. Depends on T003 — FR-010:
  - US4-1: on rooms where `norte` costs 300 and `sur` declares no cost, `servicio.estado_vista().salidas` has `norte` with `costo 300` and `sur` with `costo 100`
  - US4-2: a closed exit with cost 40 has `cerrada is True` and `costo 40`
  - `VistaConsola().mostrar_estado(estado)`, captured with `capsys`, prints `(abierta, costo 300)`, `(abierta, costo 100)` and `(cerrada, costo 40)`
  - Golden: for `armar_estado_fijo()`, the output of `mostrar_estado(servicio.estado_vista())` equals `cargar_golden("estado.txt")` after appending `, costo 100` inside the parentheses of each exit line. All exits there have the default cost.
- [ ] T020 [US4] Add to `tests/test_vista_costos.py`, after T019 (same file): run `Controlador.jugar` for one loop iteration with a fake view. The fake view implements `mostrar_estado`, `pedir_comando` (returns `"salir"`), `mostrar_mensaje` and `mostrar_final` (which only records the call). Use `persistencia=None`. Assert that `mostrar_estado` received an `EstadoVistaDTO`, not a `Partida`. What `mostrar_final` receives is checked in T027 — FR-010

### Implementation

- [ ] T021 [P] [US4] Create `dto/estado_vista_dto.py` with `EstadoVistaDTO`, `JugadorVistaDTO`, `SalidaVistaDTO`, `EnemigoVistaDTO`, `TrampaVistaDTO` and `ObjetoVistaDTO`, with exactly the fields in data-model.md "EstadoVistaDTO". `SalidaVistaDTO.costo` is "int, already resolved: declared or 100". Use plain classes and plain lists, and import nothing from `model/`. Depends on T003 — FR-010
- [ ] T022 [US4] Add `JuegoService.estado_vista(self)` in `service/juego_service.py`. It builds an `EstadoVistaDTO` from `self.partida`, following the "From" column in data-model.md: exits in room order with `salida.costo`; enemies where `enemigo.sala is sala`; `bitacora.obtener_todos()[-20:]`. It must only read state, never change it. Depends on T007 and T021 — FR-010
- [ ] T023 [US4] In `controller/controlador.py` `jugar`, replace `self.vista.mostrar_estado(partida)` with `self.vista.mostrar_estado(self.servicio.estado_vista())`. Depends on T022 — FR-010
- [ ] T024 [US4] In `view/vista_consola.py`, rewrite `mostrar_estado(self, estado)` to print only from the DTO, with the same lines as today, and exit lines as `f"  {s.direccion} -> {s.nombre_destino} ({'cerrada' if s.cerrada else 'abierta'}, costo {s.costo})"`. In `view/vista_silenciosa.py`, rename the `mostrar_estado` parameter to `estado`; it stays a no-op. Depends on T021 — FR-010

**Checkpoint**: `python -m pytest tests/test_vista_costos.py` is green.

---

## Phase 7: User Story 5 — Exit costs are always current; old saves and logs are rejected by version (P2)

**Goal**: prove that the existing behaviour meets FR-011 and FR-012. No new invalidation mechanism.

- [ ] T025 [P] [US5] Write tests in `tests/test_version_cripta.py`, using fakes and no network — FR-011, FR-012:
  - US5-1: a `RepositorioCripta` with a fake source whose `datos_cripta` and `pagina_esqueleto` return a one-page skeleton whose exits declare `costo` → `cargar_esqueleto` + `construir_salas` give rooms carrying those costs, and the fake records that the skeleton page was requested (FR-011)
  - US5-2: `validar_guardado` on a save whose header `version_cripta` differs returns the "otra cripta o versión" message. Call it as `Aplicacion.validar_guardado(fake_app, ruta)`, where `fake_app` has `repo_cripta.datos` and `repo_catalogo.version()`, so no real `Aplicacion` is built. Write the save with `GuardadoBinario().guardar(ruta, cabecera, [], [])` into `tmp_path`, with an empty `contenidos` list and no commands (FR-012)
  - US5-3: `Aplicacion._versiones_coinciden(fake_app, lector)` is False for a lector with a different `version_cripta` (FR-012)
  - US5-4 (repository level): `aplicacion.py` loads a save in `_sesion` → `_reiniciar_salas`, which calls `repo_cripta.construir_salas(self.dtos)` with the skeleton DTOs downloaded at start. Reproduce that step: build rooms from the same DTOs twice with `construir_salas`, as a load does. Check that the second build has the same costs from the DTOs, and that `validar_guardado` accepts a save (written with an empty `contenidos` list) whose versions match (FR-011, FR-012)
- [ ] T026 [US5] Check that no code path writes exit costs into saves (`adapters/guardado_binario.py`), logs (`adapters/bitacora_partida.py`) or the catalog cache (`adapters/almacen_fichas.py`), and that `VERSION_FORMATO` is unchanged. Record the result in the module docstring of `tests/test_version_cripta.py` — FR-011, FR-012

---

## Phase 8: Service boundary (Constitution III, cross-cutting)

**Goal**: everything the service hands outward is a DTO or plain value ([contracts/service-boundary.md](./contracts/service-boundary.md)). The controller never reads the game model, and no view method receives a model object. Printed output equals the golden files apart from exit costs.

### Tests

- [ ] T027 [P] Write `tests/test_frontera_servicio.py`, using `armar_estado_fijo` and `cargar_golden` from `tests/estado_fijo.py`. Depends on T003 — FR-010, FR-014:
  - Each of `estado_vista`, `resumen_final`, `inventario_vista`, `vista_ordenada(c)` (for `peso`, `valor`, `nombre`), `objetos_en_sala` and `enemigos_en_sala` returns no instance of a class defined in `model/`. Walk DTO attributes and lists recursively and check each value's `type(x).__module__` does not start with `model.`
  - `terminada()` returns a bool and `semilla()` an int
  - `enemigos_en_sala()` lists only living enemies in the player's room, in `partida.enemigos` order
  - `atacar(id)` with a living enemy in the room returns True and damages or defeats it. `atacar("x")` returns False and changes nothing
  - `controller/controlador.py` contains no `.partida` and no `from model` (read the file text)
  - Moved here from the US4 test: run `Controlador.jugar` for one loop with a recording fake view (`pedir_comando` returns `"salir"`). Assert that `mostrar_final` received a `ResumenFinalDTO`.
  - Golden, captured with `capsys`:
    - `VistaConsola().mostrar_final(servicio.resumen_final())` equals `final_consola_{victoria,muerte,salida}.txt` for the three `final` values
    - `mostrar_inventario(servicio.inventario_vista())` equals `inventario.txt`
    - `mostrar_inventario_ordenado(servicio.vista_ordenada(c), c)` equals `inventario_{c}.txt`
- [ ] T028 [P] Update `tests/test_service.py` `test_servicio_esperar_y_atacar` to call `servicio.atacar("r1")` instead of `servicio.atacar(rata)` — FR-006

### Implementation

- [ ] T029 [P] Create `dto/resumen_final_dto.py` (`ResumenFinalDTO`) and `dto/inventario_vista_dto.py` (`InventarioVistaDTO`, `ObjetoInventarioDTO`), with exactly the fields in data-model.md "Other service boundary DTOs". Use plain classes and lists, and import nothing from `model/` — FR-010, FR-014
- [ ] T030 In `service/juego_service.py`, add the methods below, as in data-model.md "Lists and plain values". Depends on T021 and T029 — FR-006, FR-010, FR-014:
  - `resumen_final()`, `inventario_vista()`, `objetos_en_sala()`, `enemigos_en_sala()`, `terminada()` and `semilla()`
  - change `vista_ordenada(criterio)` to return a list of `ObjetoInventarioDTO` in the order of `inventario.vista_ordenada`
  - change `atacar(enemigo)` to `atacar(id_enemigo)`: resolve it as the first enemy in `partida.enemigos` with `str(e.id_enemigo).lower() == str(id_enemigo).lower()`, `e.sala is jugador.sala` and `e.esta_vivo()`. Return False if there is none; otherwise call `partida.atacar(e)` and `actualizar_fichas()` as today
- [ ] T031 In `controller/controlador.py`, remove every read of the game model. Depends on T023 and T030 — FR-010, FR-014:
  - `jugar`: loop on `self.servicio.terminada()`; then `resumen = self.servicio.resumen_final()`, `self.vista.mostrar_final(resumen)` and `self.persistencia.registrar_puntaje(resumen)` when `resumen.victoria or resumen.terminada`
  - `_cmd_recoger`: use `self.servicio.objetos_en_sala()`
  - `_enemigos_en_sala` / `_elegir_enemigo`: use `self.servicio.enemigos_en_sala()` and return the chosen `id_enemigo`; `_cmd_atacar` calls `self.servicio.atacar(id_enemigo)`
  - `_cmd_inventario`: `self.vista.mostrar_inventario(self.servicio.inventario_vista())`
  - `_cmd_guardar`: `self.persistencia.guardar_partida(self.servicio.semilla(), self.comandos, nombre)`
  
  No `self.servicio.partida` may remain.
- [ ] T032 In `view/vista_consola.py`, make `mostrar_final(resumen)` print all of `resumen.bitacora` (the last 20). Make `mostrar_inventario(inv)` use the `>` marker from `actual` and ` (equipado)` from `equipado`, and make `mostrar_inventario_ordenado(objetos, criterio)` use the DTO fields, with the same text as the golden files. In `view/vista_silenciosa.py`, rename the parameters to `resumen` / `inv`; the methods stay no-ops. Depends on T029 — FR-010, FR-014
- [ ] T033 In `aplicacion.py`, outside `reproducir` (handled in Phase 9), only talk to the game through the service after it is built. Depends on T030 — FR-012, FR-014:
  - `_reejecutar`: `controlador.servicio.terminada()`
  - `guardar_partida(self, semilla, comandos, nombre)` uses `semilla`
  - `registrar_puntaje(self, resumen)` builds `Puntaje(resumen.nombre_jugador, datos.id_cripta, datos.version, resumen.acciones, resumen.enemigos_derrotados, resumen.reloj, resumen.victoria)`
  
  Building the game in `_sesion` (`fabrica.nueva_partida`, setting the player's name) stays as it is.

**Checkpoint**: `python -m pytest tests/test_frontera_servicio.py tests/test_service.py tests/test_vista_costos.py` is green, and a text search finds no `servicio.partida` outside `service/`.

---

## Phase 9: Replay without view classes (Constitution III)

**Goal**: `--replay` instantiates no class from `view/`. Its printed output equals `replay_completo.txt` and `replay_version.txt` from T003 (plan.md "Replay output without view classes", R8).

### Tests

- [ ] T034 [P] Write `tests/test_salida_replay.py`, using `tests/estado_fijo.py`. Depends on T003 — FR-012, FR-014:
  - `imprimir_final_replay(servicio.resumen_final())` output equals `final_replay_{victoria,muerte,salida}.txt` for the three `final` values
  - `imprimir_reporte(12, 50, 7, 3)` and `imprimir_reporte(12, None, 0, 0)` equal `reporte_replay.txt` and `reporte_replay_sin_presupuesto.txt`
  - Monkeypatch `VistaConsola.__init__` and `VistaSilenciosa.__init__` to raise `AssertionError("vista instanciada en --replay")`. Then run `Aplicacion.reproducir(AppFalsa(v, v), LectorFalso(1, ["w", "d", "esperar", "zz"], v, v))` and compare the captured output with `replay_completo.txt`. Then run it again with **another new** `AppFalsa(v, v)` and a lector with a different `version_cripta`, and compare with `replay_version.txt`. Never reuse an `AppFalsa` between `reproducir` calls; its `fabrica.nueva_partida` builds a fresh game from `armar_estado_fijo()` each time (FR-012)
  - `importlib.util.find_spec("view.vista_replay") is None`, and `VistaSilenciosa.__mro__ == (VistaSilenciosa, object)`

### Implementation

- [ ] T035 [P] Create `adapters/salida_replay.py` with two plain functions and no classes. Copy the text and order of `view/vista_replay.py` exactly. Import nothing from `model/` or `view/` — FR-014:
  - `imprimir_final_replay(resumen)`: the 40-dash separator, each of `resumen.bitacora[-6:]` as `f"  {mensaje}"`, `f"Tiempo final: {resumen.reloj}"`, then "¡Victoria! Escapaste de la cripta." / "Has muerto." / "Saliste de la partida." by `victoria` / `terminada`
  - `imprimir_reporte(solicitudes, presupuesto, aciertos, fallos)`: same lines as `VistaReplay.mostrar_reporte`
- [ ] T036 In `controller/controlador.py`, add the `avisar=None` parameter to `Controlador.__init__` and allow `vista=None`. Depends on T031 (same file) — FR-014:
  - Route every view call through one private helper per method: `_mostrar_mensaje`, `_mostrar_estado`, `_mostrar_final`, `_mostrar_inventario`, `_mostrar_inventario_ordenado`.
  - When `self.vista is None`, `_mostrar_mensaje(texto)` calls `self.avisar(texto)` if `avisar` is not `None`, and the other helpers do nothing.
  - When `vista` is given, behaviour is unchanged.
- [ ] T037 In `aplicacion.py` `reproducir`. Depends on T030, T035 and T036 — FR-012, FR-014:
  - On a version mismatch, `print` the same message text and return.
  - Otherwise build `Controlador(servicio, None, None, None, avisar=print)` and loop on `servicio.terminada()`.
  - Then call `imprimir_final_replay(servicio.resumen_final())` and `imprimir_reporte(self.cliente.solicitudes, self.cliente.presupuesto, self.repo_catalogo.aciertos_memoria + self.repo_catalogo.aciertos_disco, self.repo_catalogo.fallos)`.
  - Remove `from view.vista_replay import VistaReplay`; `_reportar(vista)` stays for interactive mode.
- [ ] T038 Make `view/vista_silenciosa.py` standalone: remove `from view.vista_replay import VistaReplay` and the inheritance. Keep `mostrar_estado`, `pedir_comando`, `mostrar_mensaje`, `mostrar_inventario`, `mostrar_final` and `mostrar_inventario_ordenado` as no-ops with DTO parameter names. Depends on T032 (same file) — FR-014
- [ ] T039 Delete `view/vista_replay.py` after checking that `grep -rn "vista_replay\|VistaReplay" --include=*.py .` finds no references outside `tests/capturar_salida_parte1.py`. That script is kept as the record of how the golden files were made (its full part-one version stays in Git history from T003). Remove its `from view.vista_replay import VistaReplay` import and replace its whole body with `import sys`, a `print` saying the golden files were captured from the part-one code in commit <T003 hash> and can no longer be regenerated, and `sys.exit(1)`. Then check that `grep` finds no `vista_replay`/`VistaReplay` references at all. Depends on T037 and T038 — FR-014

**Checkpoint**: `python -m pytest tests/test_salida_replay.py` is green, and `python main.py --replay <log>` prints the same text as before.

---

## Phase 10: Section 5.6 measurements

- [ ] T040 [P] In `bench/bench_ciclo.py`, next to `armar_partida`, add `armar_partida_costos(num_salas, num_enemigos, semilla)`. It builds the same room chain with exit costs drawn from `random.Random(semilla)` over {1, 10, 50, 100, 250, 500, 1000}, with the same cost on both sides of each door. Depends on T007 — FR-014 (deterministic by seed, Constitution VI)
- [ ] T041 Extend `bench/bench_agenda.py`. Measure only the part-one candidates: `AgendaHeap`, `AgendaListaSinOrdenar`, `AgendaListaOrdenada`. Depends on T016 and T040 — FR-003, FR-007, FR-014:
  - run `contar_operaciones` on `armar_partida_costos` with 300, 1000 and 3000 `errante` enemies
  - add a variable-increment version of `medir_ciclo`: increment = `intervalo(cost, speed)`, cost from the set above, speed in [50, 200]
  - print the fixed-increment and variable-increment results side by side
- [ ] T042 Run `python -m bench.bench_agenda` and fill the §Measurements table in `specs/001-exit-costs/plan.md` from `bench-parte1.txt` (T002) and T041. Apply the decision rule: keep the heap if it is the fastest, or within 10% of the fastest, at every size ≥ 300. If the rule fails, open a separate commit reopening the agenda decision — FR-014

---

## Phase 11: Polish & cross-cutting

- [ ] T043 G1: in `tests/test_costos_salida.py`, run a seeded game on rooms built by `armar_partida_costos` — FR-004, FR-006, FR-007, SC-002, SC-003:
  - The test imports this builder from `bench/bench_ciclo.py`. That dependency on benchmark code is accepted, so the test and the benchmark use the same costed crypt.
  - Use a fixed seed, 50 wanderers and trackers, and a fixed sequence of 500 player actions (moves and waits). No speed effects are applied.
  - A fixed seed plus a fixed action sequence is a replayed game in the sense of SC-002: running it again reproduces the same game (FR-014).
  - Wrap `partida._programar_movimiento` to assert, at each call, that the newly scheduled `actor.evento.tiempo == partida.reloj + max(1, salida.costo * 100 // actor.velocidad)`.
  - Wrap `partida._programar_siguiente` to assert that every scheduled time is `> partida.reloj` (no action lasts 0).
  - Assert that at least one move was checked for every exit cost in the set.
  
  Depends on T016 and T040.
- [ ] T044 SC-004 regression: in `tests/test_costos_salida.py`, a fixed seed and action sequence on rooms with no `costo` and on rooms with `costo` 100 everywhere produce identical `reloj`, rooms and HP for the player and every enemy — FR-002, FR-014
- [ ] T045 FR-014 determinism: in `tests/test_costos_salida.py`, the same seed and actions on rooms with mixed costs, run twice, give identical final state. Same file as T044, so not parallel; do it after T044 — FR-014
- [ ] T046 [P] G2: write `tests/test_replay_costos.py` — FR-014:
  - Define a helper `armar_salas(semilla)` that builds a fresh set of rooms with mixed exit costs (and the same enemies) from `random.Random(semilla)`. Call it once for the recording and once for the replay, with the same seed, so the replay never reuses rooms the recorded game changed.
  - Recording: build a service on `armar_salas(7)`, with `FabricaFalsa` from `tests/estado_fijo.py`. Run a fixed command list through `Controlador.ejecutar` with `VistaSilenciosa` and a `BitacoraPartida(tmp_path)` opened with `abrir(id_cripta, version, version, semilla)`. Close the log.
  - Replay: read the log with `LectorBitacora(tmp_path / f"partida_{id_cripta}_{semilla}.log")` and `leer()`. Build a new service on `armar_salas(7)` with `Partida(…, semilla=lector.semilla)`, and replay `lector.comandos` through `Controlador(servicio, None, None, None).ejecutar`, as `Aplicacion.reproducir` does after T037.
  - Compare `resumen_final()` (clock, victory, actions) and `estado_vista()` (room, player HP, enemies in the room) between the two runs.
  
  Depends on T016, T031 and T036.
- [ ] T047 Run `python -m pytest`; all part-one tests stay green — FR-006, FR-008, FR-014
- [ ] T048 Constitution gate, limited to new attributes or fields in the changed files that are used as an index or cache — FR-014, FR-015:
  - None of them is a `dict`, `set`, `heapq`, `bisect` or `collections` structure. `Salida.costo_declarado` is an int; the DTO lists are display-only.
  - `model/` imports nothing from `view/`, `controller/` or the view DTO modules, and `dto/` and `adapters/salida_replay.py` import nothing from `model/` or `view/`.
  - No class from `view/` is instantiated in `--replay` (checked by T034) or `--bench` (`grep -rn "Vista" bench/` finds nothing).
- [ ] T049 Run the manual check in `specs/001-exit-costs/quickstart.md` — FR-004, FR-010, FR-014:
  - `python main.py`: exit lines show `costo`, `Tiempo:` advances by `costo*100//velocidad` after a move, and `inv`, `inv peso`, `atacar`, `recoger`, `guardar` and the end screen behave as in part one
  - `python main.py --replay <log>` prints the same text as part one, apart from any differences in the game itself

---

## Dependencies & Execution Order

```text
T001, T002 (done)
T003 golden capture → before T021, T024, T029–T039 (any change to view/controller/service/aplicacion)
T004, T005, T006, T007 (independent files)
T006 + T007 → T008 → T009 → T010
Phase 2 → US1 (T011–T014) → US2 (T015–T016) → US3 (T017–T018)
Phase 2 + T003 → US4 (T019–T024) → Boundary (T027–T033) → Replay (T034–T039)
Phase 2 → US5 (T025–T026)
T007 → T040;  T016 + T040 → T041 → T042
T016 + T040 → T043 → T044 → T045
T016 + T031 + T036 → T046
All → T047 → T048 → T049
```

- US1, US2 and US3 are sequential because they edit `model/partida_logica.py` and `tests/test_costos_salida.py`.
- Edits to the same file are sequential: controller (T023 → T031 → T036), `vista_silenciosa.py` (T024 → T032 → T038), `aplicacion.py` (T033 → T037).
- `[P]` marks tasks that touch different files with no unfinished dependency. With a single implementer they can be done in any order within their phase, or handed to separate agent sessions.

## Suggested Order

```text
T003 → Phase 2 (T004–T010) → US1 (T011–T014)                      MVP
→ US2 (T015–T016) → US3 (T017–T018)
→ US4 (T019–T024) → US5 (T025–T026)
→ Boundary (T027–T033) → Replay (T034–T039)
→ Measurements (T040–T042) → Polish (T043–T049)
```

## Implementation Strategy

1. **Before any view, controller, service or `aplicacion.py` change**: T003 golden capture.
2. **MVP**: Phase 2 + US1. The player's moves take exit-dependent time, with FR-016 order verified.
3. Add US2 (enemies) and US3 (speed-change tests). This completes the timeline rules.
4. Add US4 (room view with costs), then the service boundary phase and the replay phase, which close Constitution III. US5 version tests go alongside.
5. Section 5.6 measurements, then polish (whole-game checks, determinism, replay, gates).
6. Commit per task group; a spec correction always goes in its own commit before the code that follows it (Constitution VII).
