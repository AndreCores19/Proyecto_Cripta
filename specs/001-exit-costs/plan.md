# Implementation Plan: Terrain — Exit Costs

**Branch**: `001-exit-costs` | **Date**: 2026-11-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-exit-costs/spec.md`

## Summary

Each exit gets a cost read from the crypt skeleton (`costo`, default 100, shared by both sides of
a connection). Every move — player and enemies — keeps the part-one order (FR-016): the actor
enters the destination room at the start of the move, and its next action is scheduled at
`reloj + intervalo(salida.costo, actor.velocidad)` instead of the fixed `COSTO_MOVER`. Speed changes
while that next action is pending keep going through the existing `nuevo_tiempo_por_velocidad` +
`AgendaEventos.reprogramar` path (FR-009). The part-one inconsistent-door check in
`RepositorioCripta.construir_salas` is extended to compare declared costs.

To show exit costs without breaking Constitution III, this feature also closes every model leak
across the service boundary. The service returns DTOs or plain values for everything the
controller, the views and the persistence calls need. The controller never reads the game model,
and no view method receives a model object. The part-one agenda benchmark is re-run with variable
move costs and many actors to confirm or revisit the heap decision (section 5.6).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `requests` (HTTP, unchanged); no new dependencies

**Storage**: Unchanged. The crypt skeleton is never persisted: it is downloaded from the service
every time a game starts (read from the recording of that crypt version in `--offline` mode), so
exit costs are never stored. Only catalog entries are cached. Saved games and replay logs store the
crypt version and are rejected on mismatch by the existing check (`aplicacion.py`
`validar_guardado`, `_versiones_coinciden`). File formats are unchanged; `guardar_partida` and
`registrar_puntaje` get their inputs from DTOs or plain values instead of `Partida`.

**Testing**: pytest (`tests/`), one test per acceptance scenario, each citing its FR

**Target Platform**: Desktop console (Windows/Linux), headless modes `--replay` and `--bench` (the verification mode is introduced later by the solvability feature)

**Project Type**: CLI game, five-layer architecture (data → logic → service → controller → view)

**Performance Goals**: A player action (including the enemy turns it triggers) must cost no more
with variable exit costs than with fixed costs in the part-one agenda benchmark; see §Measurements.

**Constraints**: Constitution I (no `dict`/`set`/`heapq`/`bisect`/`collections` in evaluated
structures), II (determinism), III (layers and DTOs), IV (no hardcoded crypt data), V (version
check only). `intervalo` and `nuevo_tiempo_por_velocidad` in `model/tiempo_logica.py` are reused
unchanged.

**Scale/Scope**: Benchmarks at 100–3000 pending events (same sizes as part one), up to 3000 active enemies.

## Constitution Check

*GATE: checked before Phase 0 and re-checked after Phase 1 — PASS.*

| Principle / gate | Status | Notes |
|---|---|---|
| I. Own data structures | PASS | No new evaluated structure. The cost is an integer attribute on `Salida`. The agenda stays the hand-written binary heap in `structures/agenda.py`. The benchmark only re-runs the part-one candidates (heap, unsorted list, sorted list). The view DTOs hold plain lists for display only; they are not an index or cache in an evaluated problem. No `dict`/`set`/`heapq`/`bisect`/`collections` introduced in `model/`, `structures/`, `data/` or `dto/`. |
| II. Determinism | PASS | Costs come from data. The agenda tie-break (`tiempo`, then `num_sec`) is unchanged. The DTO builders only read state. `atacar` by id resolves the target by scanning `partida.enemigos` in list order, the same order the controller used before. Benchmark crypts are generated from a fixed seed. |
| III. Layered architecture | PASS | Data in: `SalidaDTO.costo` → `RepositorioCripta` → `Salida.costo`. Data out: every service method the controller calls returns a DTO from `dto/` or a plain value (bool, int, str). The controller holds no reference to `Partida`, `Sala`, `Enemigo` or `Objeto`. Every view method (`mostrar_estado`, `mostrar_final`, `mostrar_inventario`, `mostrar_inventario_ordenado`) receives DTOs. `Aplicacion.reproducir` and `_reejecutar` use the service too. The model imports nothing from `view/` or `controller/`. **No class from `view/` is instantiated in `--replay` or `--bench`.** `--bench` never touches `view/`. `--replay` runs the controller with `vista=None` and prints through plain functions in `adapters/salida_replay.py`, and `VistaReplay` is deleted (see "Replay output without view classes"). |
| IV. No hardcoded data | PASS | The only constant is the default 100 (FR-002), which is the existing `COSTO_MOVER` in `tiempo_logica.py`. |
| V. Network budget and versions | PASS | No new request: `costo` arrives inside the skeleton pages that are already downloaded. Invalidation stays in the existing crypt-version comparison. |
| VI. Evidence-backed performance | PASS (pending data) | The agenda decision is kept or changed only from the §Measurements numbers. |
| VII. Spec before code | PASS | `spec.md` and this plan are committed (`1c49751`, `955acb5` and later). Spec corrections go in their own commit before any code. |
| VIII. What goes where | PASS | Where an actor is during a move is a spec rule (FR-016); this plan only maps it to code. The boundary DTOs are design, not new rules. |
| IX. Traceability | PASS | Every test cites its FR; the mapping is in [quickstart.md](./quickstart.md). |

## Design

### Where each requirement lands

| FR | Layer | Change |
|---|---|---|
| FR-001, FR-002 | dto | `SalidaDTO.desde_json` reads `datos.get("costo")`. Its value is `None` when the exit doesn't declare one. |
| FR-005, FR-013 | data + model | In the third loop of `RepositorioCripta.construir_salas`, before `salida.enlazar(otra)`, raise the "Puerta inconsistente" `ValueError` when both sides declare a cost and the costs differ. `Salida.enlazar` copies the declared cost to the side that has none, the same way it already shares `llave` and `cierre_automatico`. |
| FR-002 | model | `Salida.costo` (property) returns `costo_declarado`, or `COSTO_MOVER` (100) when it is `None`. Exits with no opposite side keep their own value. |
| FR-003, FR-004, FR-007 | model | New `Partida._programar_movimiento(actor, salida)` = `_programar_siguiente(actor, salida.costo)`. It is used in `Partida.mover` (replacing `COSTO_MOVER`) and in the enemy turn when `salida is not None` (replacing the `COSTO_ESPERAR` that is scheduled today after an enemy moves). The hunter feature MUST schedule its moves through the same method. |
| FR-016 | model | Already how the engine works; this feature must not change the order. In `Partida.mover`: refresh the trail of the origin room → enter the destination room (`_entrar_en_sala`, which marks the trail and activates enemies) → traps → victory check → `_programar_movimiento`. Enemies change room at the start of their turn and then schedule. Tests check that the actor is in the destination room at T and its next action is at T + interval. |
| FR-006 | model | Attack, wait and the other costs are unchanged. An enemy that does not move still schedules `COSTO_ESPERAR`. |
| FR-008 | model | `_decidir_errante` / `_decidir_rastreador` are unchanged. Following the reworded US2-2, tests check the rule: from a fixed state (room, neighbouring trail marks, clock, open exits) with costs other than 100, the tracker picks the exit the part-one rule picks. Identical sequences across whole games are only compared when every cost is 100 (SC-004). |
| FR-009 | model | No code change. `EfectosLogica._cambiar_velocidad` already rescales the actor's pending next action with `nuevo_tiempo_por_velocidad`, where `end_time` is that next action's time. Tests cover the case where it was scheduled by an expensive move. |
| FR-010 | dto + service + controller + view | The room view prints from `EstadoVistaDTO`; exit lines read `N -> Sala (abierta, costo 300)`. See "Service boundary DTOs" for the rest of the boundary. |
| FR-011 | data | No change: exit costs are read from the skeleton downloaded on every start (offline recording in `--offline` mode). They are never written to saved games, replay logs or the catalog cache. |
| FR-012 | app | No change in behaviour: a saved game (`validar_guardado`) or replay log (`_versiones_coinciden`) whose crypt version differs is rejected by the existing check. Tests confirm that a different-version save and log are refused and that a same-version save uses the fresh skeleton's costs. |
| FR-014 | all | Covered by the determinism tests and a replay determinism test on a crypt with costs (replay and benchmark modes; there is no verification mode yet). The DTO refactor and the replay output change must not change any printed output or any game state; golden files captured from the unchanged code are the reference. |
| FR-015 | all | Costs are only ever read from JSON. |

### Timing semantics (FR-016, FR-004, FR-009)

A move is instantaneous in space: at the move's start time T the actor is already in the
destination room, and traps, victory and trail marks apply at T. The move's duration is the gap
until the actor's next action, scheduled at `T + intervalo(salida.costo, velocidad)`. Its
"end time" in FR-009 is the time of that pending event (`actor.evento.tiempo`), and a speed
change rescales it through `reprogramar`.

To test FR-009 at a time between T and the next action, use an actor whose pending event can be
inspected without advancing to it (an enemy, or the player before `avanzar_hasta_jugador` runs).
Set the clock to the change time and apply the speed change. `mover` advances the clock to the
player's next action, so a player-level test must schedule the speed change as an event (e.g. the
end of a speed effect) that fires before it.

### Service boundary DTOs (Constitution III)

Every crossing from the service outward carries a DTO from `dto/` or a plain value. `JuegoService`
is the only class above the model that touches `Partida`. Full field lists are in
[data-model.md](./data-model.md).

| Consumer today | Reads today | Replaced by |
|---|---|---|
| `Controlador.jugar` loop condition | `servicio.partida.terminada` | `servicio.terminada()` → bool |
| `VistaConsola.mostrar_estado(partida)` | `Partida` | `servicio.estado_vista()` → `EstadoVistaDTO` (includes exit costs) |
| `mostrar_final(partida)` (console, silent) | `Partida` | `servicio.resumen_final()` → `ResumenFinalDTO` |
| `persistencia.registrar_puntaje(partida)` | `Partida` | `registrar_puntaje(resumen)` with the same `ResumenFinalDTO` |
| `Controlador._cmd_guardar` → `persistencia.guardar_partida(partida, …)` | `partida.semilla` | `guardar_partida(servicio.semilla(), comandos, nombre)` → int |
| `Controlador._cmd_recoger` | `servicio.partida.jugador.sala.objetos` | `servicio.objetos_en_sala()` → list of `ObjetoVistaDTO` |
| `Controlador._enemigos_en_sala` / `_elegir_enemigo` | `partida.enemigos`, `jugador.sala`, `esta_vivo()`; passes an `Enemigo` to `servicio.atacar` | `servicio.enemigos_en_sala()` → list of `EnemigoVistaDTO` (alive, in the player's room, in `partida.enemigos` order); `servicio.atacar(id_enemigo)` resolves the id inside the service |
| `mostrar_inventario(partida)` | `Partida` inventory | `servicio.inventario_vista()` → `InventarioVistaDTO` |
| `servicio.vista_ordenada(criterio)` → `mostrar_inventario_ordenado` | list of model `Objeto` | the same method returns a list of `ObjetoInventarioDTO`, sorted by the existing `Inventario.vista_ordenada` |
| `Aplicacion._reejecutar` | `controlador.servicio.partida.terminada` | `controlador.servicio.terminada()` |
| `Aplicacion.reproducir` | `partida.terminada`; `VistaReplay().mostrar_final(partida)` | `servicio.terminada()`; `imprimir_final_replay(servicio.resumen_final())`, a plain function (see below) |

Rules:
- DTOs are snapshots made of plain values and lists of other DTOs. They never hold a model reference, and `dto/` imports nothing from `model/`.
- The views print exactly what they print today, apart from the exit costs. The console `mostrar_final` shows all 20 log lines in `ResumenFinalDTO.bitacora`; the replay summary shows the last 6 by slicing the same list.
- `JuegoService.atacar(id_enemigo)` returns `False` when no living enemy with that id is in the player's room. `tests/test_service.py` is updated to call it with the id.
- `Aplicacion` remains the composition root. It still builds the `Partida` (`fabrica.nueva_partida`, setting the player's name), but after that it only talks to the game through the service.

### Replay output without view classes (Constitution III, analysis C2)

Principle III says `--replay` MUST NOT instantiate any view class. Today `Aplicacion.reproducir` creates `VistaReplay` and hands it to the controller. New design:

- **Plain output functions** in a new module `adapters/salida_replay.py` (outside `view/`, no classes, no imports from `model/`). Each one prints exactly the text `VistaReplay` prints today:
  - `imprimir_final_replay(resumen)`: the separator, the last 6 lines of `resumen.bitacora` indented by two spaces, `Tiempo final: {resumen.reloj}`, and the victory / death / quit line (same text as `VistaReplay.mostrar_final`).
  - `imprimir_reporte(solicitudes, presupuesto, aciertos, fallos)`: same text as `VistaReplay.mostrar_reporte`.
  - The version-mismatch message in `reproducir` is printed with `print`, with the same text.
- **Controller without a view**: `Controlador(servicio, vista, bitacora, persistencia, avisar=None)`. When `vista is None`:
  - `mostrar_mensaje(texto)` calls `avisar(texto)` if it is given.
  - `mostrar_estado`, `mostrar_inventario`, `mostrar_inventario_ordenado` and `mostrar_final` are skipped. `VistaReplay` implemented them as no-ops, so the output doesn't change.
  
  All view calls in the controller go through one small helper per method, so the `None` check lives in one place. `reproducir` builds `Controlador(servicio, None, None, None, avisar=print)`, so replay messages are still printed at the same moment as today.
- **`VistaReplay` is deleted.** Its only other user was `VistaSilenciosa`, which inherits from it. `VistaSilenciosa` becomes a standalone class with all methods as no-ops (no `mostrar_reporte`, which is never called on it). It is still used only by `Aplicacion._reejecutar` when loading a save in interactive mode, which is not `--replay`.
- `Aplicacion._reportar(vista)` stays for interactive mode (`VistaConsola.mostrar_reporte`). `reproducir` calls `imprimir_reporte` with the same four values.
- `--bench` imports nothing from `view/` today, and that does not change.

Before deleting `VistaReplay`, capture its output for a fixed state as the expected text for the new functions (see tasks).

Complexity per call: O(size of what is shown). For example, O(exits + enemies + traps + objects + 20) for `estado_vista`, and O(inventory) for `inventario_vista`. None of these run in the `--bench` paths.

### Complexity (engine)

- Reading a cost: O(1) per exit when the skeleton loads; the extra comparison in the door loop is O(1) per exit, so loading stays O(salas + salidas).
- Scheduling a move: unchanged, O(log n) for `programar` on the heap (n = pending events).
- Speed change: unchanged, O(log n) `reprogramar`.
- `atacar(id_enemigo)`: O(active enemies) to resolve the id, the same scan the controller did before.

## Measurements (section 5.6)

The part-one benchmark `bench/bench_agenda.py` is extended (measurement code only):

1. **Real operations per player action with variable costs**: a variant of `armar_partida` (in `bench/bench_ciclo.py`) assigns exit costs from a seeded RNG over {1, 10, 50, 100, 250, 500, 1000}. The variant runs 100 rooms with 300, 1000 and 3000 `errante` enemies. Output: programar/extraer/cancelar/reprogramar per action and the maximum number of pending events. This is compared with the existing fixed-cost run.
2. **Extract + schedule (µs/op)**: same candidates and sizes as part one (100, 300, 1000, 3000). The increment is drawn as `intervalo(cost, speed)`, with costs from the set above and speeds in [50, 200], instead of `randint(1, 200)`. Both increment models are printed side by side.
3. **Cancel + schedule (µs/op)**: unchanged method, re-run for comparison.
4. **Candidates**: only the part-one candidates (binary heap, unsorted list, sorted list) are measured, under the new load. No new candidate is added.

**Decision rule**: keep the binary heap if it is the fastest, or within 10% of the fastest, of the three part-one candidates at every size ≥ 300 in both increment models. Otherwise record the numbers here and reopen the agenda decision in a separate commit.

| Measurement | Part one (fixed 100) | Part two (variable) | Decision |
|---|---|---|---|
| ops/action, 300 enemies | _to fill from `--bench`_ | _to fill_ | |
| µs extract+schedule, n=3000 (heap / unsorted / sorted) | _to fill_ | _to fill_ | |
| µs cancel+schedule, n=3000 (heap / unsorted / sorted) | _to fill_ | _to fill_ | |

## Project Structure

### Documentation (this feature)

```text
specs/001-exit-costs/
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── skeleton-exit.md
│   ├── room-view.md
│   └── service-boundary.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
dto/salida_dto.py              # + costo (None when not declared)                          (Andrea)
dto/estado_vista_dto.py        # new: EstadoVistaDTO and its parts (room view)              (Andrea)
dto/inventario_vista_dto.py    # new: InventarioVistaDTO, ObjetoInventarioDTO              (Andrea)
dto/resumen_final_dto.py       # new: ResumenFinalDTO (end of game + score)                 (Andrea)
data/repositorio_cripta.py     # pass costo to Salida; extend inconsistent-door check      (Andrea)
service/juego_service.py       # + estado_vista, resumen_final, inventario_vista, objetos_en_sala,
                               #   enemigos_en_sala, terminada, semilla; atacar(id_enemigo);
                               #   vista_ordenada returns DTOs                             (Andrea)
controller/controlador.py      # no Partida/Sala/Enemigo/Objeto access; only service DTOs;
                               #   vista may be None (replay), messages go to avisar       (Andrea)
view/vista_consola.py          # every method prints from DTOs; exit lines show costo      (Andrea)
view/vista_replay.py           # DELETED                                                   (Andrea)
view/vista_silenciosa.py       # standalone (no longer inherits VistaReplay), DTO params, no-ops (Andrea)
adapters/salida_replay.py      # new: imprimir_final_replay(resumen), imprimir_reporte(...) (Andrea)
aplicacion.py                  # reproducir: no view class, Controlador(..., None, ..., avisar=print),
                               #   imprimir_final_replay / imprimir_reporte; _reejecutar uses
                               #   servicio.terminada(); guardar_partida(semilla, …),
                               #   registrar_puntaje(resumen)                              (Andrea)
model/sala_logica.py           # Salida.costo_declarado, Salida.costo, enlazar shares cost (Emily)
model/partida_logica.py        # _programar_movimiento; player and enemy moves use it      (Emily)
model/tiempo_logica.py         # unchanged (intervalo, nuevo_tiempo_por_velocidad, COSTO_MOVER)
model/efectos_logica.py        # unchanged
structures/agenda.py           # unchanged unless §Measurements says otherwise
bench/bench_ciclo.py           # seeded variable-cost crypt builder                        (Emily)
bench/bench_agenda.py          # variable-cost load for the part-one candidates             (Emily)
tests/test_costos_datos.py     # new (Andrea): DTO, repository linking, inconsistent-cost door
tests/test_vista_costos.py     # new (Andrea): estado_vista DTO contents + room view output (US4)
tests/test_frontera_servicio.py # new (Andrea): every service→controller/view crossing is a DTO/plain value;
                               #   output of mostrar_final/inventario unchanged; atacar by id
tests/test_service.py          # updated (Andrea): atacar(id_enemigo)
tests/test_version_cripta.py   # new (Andrea): fresh skeleton, old-version save/log rejected (US5)
tests/test_replay_costos.py    # new (Andrea): record + replay on a crypt with costs (FR-014)
tests/test_salida_replay.py    # new (Andrea): replay output equals the captured VistaReplay text;
                               #   no view/ class is instantiated during reproducir
specs/001-exit-costs/salida-parte1/ # captured part-one output of the views and VistaReplay (golden files)
tests/test_costos_salida.py    # new (Emily): move durations, FR-016 order, enemies, speed changes (US1–US3)
tests/test_puertas.py          # + (Emily): Salida.costo sharing rules in enlazar
```

**Structure Decision**: existing single-project layered layout. This feature adds three DTO modules, one output-function module in `adapters/` and new test files, and removes `view/vista_replay.py`. The only new directory is the golden-output folder under `specs/`.

## Complexity Tracking

No constitution violations to justify.
