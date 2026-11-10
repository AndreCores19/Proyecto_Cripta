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

The console room view stops receiving the game model. The service builds a view DTO from the game
state, the controller passes it to the view, and the DTO carries each exit's cost. The part-one
agenda benchmark is re-run with variable move costs and many actors to confirm or revisit the heap
decision (section 5.6).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `requests` (HTTP, unchanged); no new dependencies

**Storage**: Unchanged. The crypt skeleton is never persisted: it is downloaded from the service
every time a game starts (read from the recording of that crypt version in `--offline` mode), so
exit costs are never stored. Only catalog entries are cached. Saved games and replay logs store the
crypt version and are rejected on mismatch by the existing check (`aplicacion.py`
`validar_guardado`, `_versiones_coinciden`).

**Testing**: pytest (`tests/`), one test per acceptance scenario, each citing its FR

**Target Platform**: Desktop console (Windows/Linux), headless modes `--replay`, `--bench`, `--verificar`

**Project Type**: CLI game, five-layer architecture (data → logic → service → controller → view)

**Performance Goals**: A player action (including the enemy turns it triggers) must cost no more
with variable exit costs than with fixed costs in the part-one agenda benchmark; see §Measurements.

**Constraints**: Constitution I (no `dict`/`set`/`heapq`/`bisect`/`collections` in evaluated
structures), II (determinism), III (layers and DTOs), IV (no hardcoded crypt data), V (version
check only). `intervalo` and `nuevo_tiempo_por_velocidad` in `model/tiempo_logica.py` are reused
unchanged.

**Scale/Scope**: Benchmarks at 100–3000 pending events (same sizes as part one), up to 3000 active enemies.

## Constitution Check

*GATE: checked before Phase 0 and re-checked after Phase 1 — PASS, with one recorded item under Complexity Tracking.*

| Principle / gate | Status | Notes |
|---|---|---|
| I. Own data structures | PASS | No new evaluated structure. The cost is an integer attribute on `Salida`. The agenda stays the hand-written binary heap in `structures/agenda.py`. The benchmark only re-runs the part-one candidates (heap, unsorted list, sorted list). The view DTO holds plain lists of DTOs for display only; it is not an index or cache in an evaluated problem. No `dict`/`set`/`heapq`/`bisect`/`collections` introduced in `model/`, `structures/`, `data/` or `dto/`. |
| II. Determinism | PASS | Costs come from data. The agenda tie-break (`tiempo`, then `num_sec`) is unchanged. Building the view DTO reads state and never changes it. Benchmark crypts are generated from a fixed seed. |
| III. Layered architecture | PASS (for the room view) | Data in: `SalidaDTO.costo` → `RepositorioCripta` → `Salida.costo`. Data out: `JuegoService.estado_vista()` builds `EstadoVistaDTO` from the game state, `Controlador.jugar` passes it to `mostrar_estado`, and `VistaConsola` no longer receives `Partida` there. The model imports nothing from `view/` or `controller/`. `--replay`, `--bench` and `--verificar` do not instantiate `VistaConsola`; replay drives `Controlador.ejecutar`, which never builds the state DTO. The other view methods that still receive the model are listed under Complexity Tracking. |
| IV. No hardcoded data | PASS | The only constant is the default 100 (FR-002), which is the existing `COSTO_MOVER` in `tiempo_logica.py`. |
| V. Network budget and versions | PASS | No new request: `costo` arrives inside the skeleton pages that are already downloaded. Invalidation stays in the existing crypt-version comparison. |
| VI. Evidence-backed performance | PASS (pending data) | The agenda decision is kept or changed only from the §Measurements numbers. |
| VII. Spec before code | PASS | `spec.md` and this plan are committed (`1c49751`, `955acb5` and later). Spec corrections go in their own commit before any code. |
| VIII. What goes where | PASS | Where an actor is during a move is now a spec rule (FR-016); this plan only maps it to code. |
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
| FR-010 | dto + service + controller + view | New `dto/estado_vista_dto.py`; `JuegoService.estado_vista()`; `Controlador.jugar` calls `self.vista.mostrar_estado(self.servicio.estado_vista())`; `VistaConsola.mostrar_estado(estado)` prints from the DTO, with exit lines `N -> Sala (abierta, costo 300)`. `VistaReplay` and `VistaSilenciosa` keep their no-op `mostrar_estado`, with the parameter renamed to `estado`. |
| FR-011 | data | No change: exit costs are read from the skeleton downloaded on every start (offline recording in `--offline` mode). They are never written to saved games, replay logs or the catalog cache. |
| FR-012 | app | No change: a saved game (`validar_guardado`) or replay log (`_versiones_coinciden`) whose crypt version differs is rejected by the existing check. Tests confirm that a different-version save and log are refused and that a same-version save uses the fresh skeleton's costs. |
| FR-014 | all | Covered by the determinism tests and a replay determinism test on a crypt with costs. |
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

### View DTO (C1)

`EstadoVistaDTO` carries exactly what `VistaConsola.mostrar_estado` prints today, plus exit costs:

- room: id, name; clock
- player: name, HP / max HP, attack, defense, speed, equipped weapon and armour names (or `None`), effect types
- exits of the current room: direction, destination name, closed flag, cost
- enemies in the current room (same filter as today: `enemigo.sala is sala`): name, id, HP / max HP, effect types
- traps of the current room: name, damage, armed flag
- objects of the current room: instance id, name
- the last 20 log lines

The service builds it in O(exits + enemies + traps + objects + 20) per call; the view prints it
without touching the model. Later specs add fields to this DTO. Full shape:
[data-model.md](./data-model.md#estadovistadto-dtoestado_vista_dtopy).

### Complexity

- Reading a cost: O(1) per exit when the skeleton loads; the extra comparison in the door loop is O(1) per exit, so loading stays O(salas + salidas).
- Scheduling a move: unchanged, O(log n) for `programar` on the heap (n = pending events).
- Speed change: unchanged, O(log n) `reprogramar`.
- View DTO: O(exits + active enemies + traps + objects in the room) per redraw, interactive mode only.

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
│   └── room-view.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
dto/salida_dto.py              # + costo (None when not declared)                       (Andrea)
dto/estado_vista_dto.py        # new: EstadoVistaDTO and its parts                        (Andrea)
data/repositorio_cripta.py     # pass costo to Salida; extend inconsistent-door check    (Andrea)
service/juego_service.py       # + estado_vista() builds EstadoVistaDTO from Partida     (Andrea)
controller/controlador.py      # jugar passes servicio.estado_vista() to mostrar_estado  (Andrea)
view/vista_consola.py          # mostrar_estado(estado) prints from the DTO, with costs  (Andrea)
view/vista_replay.py           # mostrar_estado(estado) stays a no-op                    (Andrea)
view/vista_silenciosa.py       # mostrar_estado(estado) stays a no-op                    (Andrea)
model/sala_logica.py           # Salida.costo_declarado, Salida.costo, enlazar shares cost (Emily)
model/partida_logica.py        # _programar_movimiento; player and enemy moves use it    (Emily)
model/tiempo_logica.py         # unchanged (intervalo, nuevo_tiempo_por_velocidad, COSTO_MOVER)
model/efectos_logica.py        # unchanged
structures/agenda.py           # unchanged unless §Measurements says otherwise
bench/bench_ciclo.py           # seeded variable-cost crypt builder                      (Emily)
bench/bench_agenda.py          # variable-cost load for the part-one candidates           (Emily)
tests/test_costos_datos.py     # new (Andrea): DTO, repository linking, inconsistent-cost door
tests/test_vista_costos.py     # new (Andrea): estado_vista DTO contents + room view output (US4)
tests/test_version_cripta.py   # new (Andrea): fresh skeleton, old-version save/log rejected (US5)
tests/test_costos_salida.py    # new (Emily): move durations, FR-016 order, enemies, speed changes (US1–US3)
tests/test_puertas.py          # + (Emily): Salida.costo sharing rules in enlazar
```

**Structure Decision**: existing single-project layered layout; one new DTO module and new test files, no new directories.

## Complexity Tracking

| Item | Why it remains | Plan |
|---|---|---|
| `VistaConsola.mostrar_final(partida)`, `mostrar_inventario(partida)` and `mostrar_inventario_ordenado(objetos, …)` still receive model objects. `Controlador.jugar` also passes `partida` to `persistencia.registrar_puntaje`, but that goes to the data layer, not the view. | Out of scope for this feature: the request limits the view DTO to what the room view shows. These methods existed in part one and show nothing related to exit costs. | Principle III is still not met for these three methods. Track them as a follow-up that extends `EstadoVistaDTO` (or adds sibling DTOs) in a later spec. `/speckit-analyze` will keep flagging them until then. |
