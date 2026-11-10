# Implementation Plan: Terrain — Exit Costs

**Branch**: `001-exit-costs` | **Date**: 2026-11-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-exit-costs/spec.md`

## Summary

Each exit gets a cost read from the crypt skeleton (`costo`, default 100, shared by both sides of
a connection). Every move — player and enemies — schedules the actor's next action with
`intervalo(salida.costo, actor.velocidad)` instead of the fixed `COSTO_MOVER`. Speed changes keep
going through the existing `nuevo_tiempo_por_velocidad` + `AgendaEventos.reprogramar` path, which
already rescales whatever action is pending. The part-one inconsistent-door check in
`RepositorioCripta.construir_salas` is extended to compare declared costs. The console view prints
each exit's cost. The part-one agenda benchmark is re-run with variable move costs and many actors
to confirm or revisit the heap decision (section 5.6).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `requests` (HTTP, unchanged); no new dependencies

**Storage**: Unchanged. The skeleton is never persisted by the game: it is re-read from the
service (or from offline recordings) on every start. Persisted saves and logs carry
`version_cripta` and are already rejected on mismatch (`aplicacion.py` `validar_guardado`,
`_versiones_coinciden`).

**Testing**: pytest (`tests/`), one test per acceptance scenario, each citing its FR

**Target Platform**: Desktop console (Windows/Linux), headless modes `--replay`, `--bench`, `--verificar`

**Project Type**: CLI game, five-layer architecture (data → logic → service → controller → view)

**Performance Goals**: A player action (including the enemy turns it triggers) must cost no more
with variable exit costs than with fixed costs in the part-one agenda benchmark; see §Measurements.

**Constraints**: Constitution I (no `dict`/`set`/`heapq`/`bisect`/`collections` in evaluated
structures), II (determinism), III (layers), IV (no hardcoded crypt data), V (version check only).
`intervalo` and `nuevo_tiempo_por_velocidad` in `model/tiempo_logica.py` are reused unchanged.

**Scale/Scope**: Benchmarks at 100–3000 pending events (same sizes as part one), up to 3000 active enemies.

## Constitution Check

*GATE: checked before Phase 0 and re-checked after Phase 1 — both PASS.*

| Principle / gate | Status | Notes |
|---|---|---|
| I. Own data structures | PASS | No new structure. The cost is an integer attribute on `Salida`. The agenda stays the hand-written binary heap in `structures/agenda.py`. The optional bucket-queue candidate in the benchmark is hand-written over plain lists. No `dict`/`set`/`heapq`/`bisect`/`collections` introduced in `model/`, `structures/` or `data/`. |
| II. Determinism | PASS | Costs come from data. The tie-break in the agenda (`tiempo`, then `num_sec`) is unchanged. Benchmark crypts are generated from a fixed seed. |
| III. Layered architecture | PASS | DTO (`SalidaDTO.costo`) → data (`RepositorioCripta`) → model (`Salida.costo`) → view. The model imports nothing from `view/` or `controller/`. `--bench` does not instantiate a view. |
| IV. No hardcoded data | PASS | Only the default 100 (a rule from the spec, FR-002) is a constant; it is `COSTO_MOVER`, already in `tiempo_logica.py`. |
| V. Network budget and versions | PASS | No new request: `costo` arrives inside the skeleton pages that are already downloaded. Invalidation stays in the existing crypt-version comparison. |
| VI. Evidence-backed performance | PASS (pending data) | The agenda decision is kept or changed only from the §Measurements numbers. |
| VII. Spec before code | ACTION | `spec.md` must be committed before any code commit. |
| VIII. What goes where | PASS | This plan adds no rule. |
| IX. Traceability | PASS | Every test cites its FR; the mapping is in [quickstart.md](./quickstart.md). |

## Design

### Where each requirement lands

| FR | Layer | Change |
|---|---|---|
| FR-001, FR-002 | dto | `SalidaDTO.desde_json` reads `datos.get("costo")`. Its value is `None` when the exit doesn't declare one. |
| FR-005, FR-013 | data + model | In the third loop of `RepositorioCripta.construir_salas`, before `salida.enlazar(otra)`, raise the "Puerta inconsistente" `ValueError` when both sides declare a cost and the costs differ. `Salida.enlazar` copies the declared cost to the side that has none, the same way it already shares `llave` and `cierre_automatico`. |
| FR-002 | model | `Salida.costo` (property) returns `costo_declarado`, or `COSTO_MOVER` (100) when it is `None`. Exits with no opposite side keep their own value. |
| FR-003, FR-004, FR-007 | model | New `Partida._programar_movimiento(actor, salida)` = `_programar_siguiente(actor, salida.costo)`. It is used in `Partida.mover` (replacing `COSTO_MOVER`) and in the enemy turn when `salida is not None` (replacing the `COSTO_ESPERAR` that is scheduled today after an enemy moves). The hunter feature MUST schedule its moves through the same method. |
| FR-006 | model | Attack, wait and the other costs are unchanged. An enemy that does not move still schedules `COSTO_ESPERAR`. |
| FR-008 | model | `_decidir_errante` / `_decidir_rastreador` are unchanged. |
| FR-009 | model | No code change. `EfectosLogica._cambiar_velocidad` already rescales the pending event with `nuevo_tiempo_por_velocidad`. Tests cover the case where that event is an expensive move. |
| FR-010 | view | `VistaConsola.mostrar_estado` prints `N -> Sala (abierta, costo 300)`. |
| FR-011, FR-012 | data / app | No change: the skeleton is always re-read, and saves and logs are rejected by the existing `version_cripta` check. Tests confirm that an old-version save or log is refused. |
| FR-014 | all | Covered by the replay determinism test on a crypt with costs. |
| FR-015 | all | Costs are only ever read from JSON. |

### Timing semantics (unchanged from part one)

In the current engine a move happens instantly, and then the actor's *next* action is scheduled
`intervalo(costo, velocidad)` later. "The move ends at T + interval" in the spec is therefore the
time of the actor's next event. A speed change while that event is pending is exactly the
"speed changes while crossing" case, and the existing rescaling already applies to it.

### Complexity

- Reading a cost: O(1) per exit when the skeleton loads; the extra comparison in the door loop is O(1) per exit, so loading stays O(salas + salidas).
- Scheduling a move: unchanged, O(log n) for `programar` on the heap (n = pending events).
- Speed change: unchanged, O(log n) `reprogramar`.

## Measurements (section 5.6)

The part-one benchmark `bench/bench_agenda.py` is extended (measurement code only):

1. **Real operations per player action with variable costs**: a variant of `armar_partida` (in `bench/bench_ciclo.py`) assigns exit costs from a seeded RNG over {1, 10, 50, 100, 250, 500, 1000}. The variant runs 100 rooms with 300, 1000 and 3000 `errante` enemies. Output: programar/extraer/cancelar/reprogramar per action and the maximum number of pending events. This is compared with the existing fixed-cost run.
2. **Extract + schedule (µs/op)**: same candidates and sizes as part one (100, 300, 1000, 3000). The increment is drawn as `intervalo(cost, speed)`, with costs from the set above and speeds in [50, 200], instead of `randint(1, 200)`. Both increment models are printed side by side.
3. **Cancel + schedule (µs/op)**: unchanged method, re-run for comparison.
4. **Extra candidate**: a hand-written fixed-width bucket queue. This is the natural rival when every interval is 100, and it should degrade as intervals spread out. It shows whether variable costs change the part-one ranking.

**Decision rule**: keep the binary heap if it is the fastest, or within 10% of the fastest, at every size ≥ 300 in both increment models. Otherwise record the numbers here and reopen the agenda decision in a separate commit.

| Measurement | Part one (fixed 100) | Part two (variable) | Decision |
|---|---|---|---|
| ops/action, 300 enemies | _to fill from `--bench`_ | _to fill_ | |
| µs extract+schedule, n=3000 (heap / unsorted / sorted / buckets) | _to fill_ | _to fill_ | |
| µs cancel+schedule, n=3000 | _to fill_ | _to fill_ | |

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
dto/salida_dto.py              # + costo (None when not declared)
data/repositorio_cripta.py     # pass costo to Salida; extend inconsistent-door check
model/sala_logica.py           # Salida.costo_declarado, Salida.costo, enlazar shares cost
model/partida_logica.py        # _programar_movimiento; player and enemy moves use it
model/tiempo_logica.py         # unchanged (intervalo, nuevo_tiempo_por_velocidad, COSTO_MOVER)
model/efectos_logica.py        # unchanged
structures/agenda.py           # unchanged unless §Measurements says otherwise
view/vista_consola.py          # print exit cost
bench/bench_ciclo.py           # seeded variable-cost crypt builder
bench/bench_agenda.py          # variable-cost scenarios + bucket-queue candidate
tests/test_costos_salida.py    # new: US1–US4 scenarios
tests/test_puertas.py          # + inconsistent-cost door, one-sided cost
tests/test_service.py          # + old-version save/log rejected (US5)
```

**Structure Decision**: existing single-project layered layout; no new directories besides the new test file.

## Complexity Tracking

No constitution violations to justify.
