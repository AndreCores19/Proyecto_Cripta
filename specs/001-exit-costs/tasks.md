---

description: "Task list for Terrain — Exit Costs"
---

# Tasks: Terrain — Exit Costs

**Input**: Design documents from `specs/001-exit-costs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required. Constitution IX says every acceptance scenario needs an automated test that cites its FR. Each owner writes the tests for her own tasks.

**Owners**: **Andrea** (data and view) and **Emily** (engine). Every task is tagged `(Owner: …)`.

## Format: `[ID] [P?] [Story] Description (Owner) — FR`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: user story from spec.md (US1–US5)
- Every test function's docstring MUST cite its FR and scenario, e.g. `"""FR-004 · US1-5"""`.

## Path Conventions

Single-project layered layout at the repo root: `dto/`, `data/`, `model/`, `structures/`, `view/`, `bench/`, `tests/`.

## Test files and owners

| File | Owner | Covers |
|---|---|---|
| `tests/test_costos_datos.py` (new) | Andrea | DTO reading, repository linking, inconsistent-door cost (US1-6, US1-7 at load time, US5-1) |
| `tests/test_vista_costos.py` (new) | Andrea | console view (US4) |
| `tests/test_version_cripta.py` (new) | Andrea | save/log version rejection (US5-2..4) |
| `tests/test_costos_salida.py` (new) | Emily | move durations, enemies, speed changes (US1, US2, US3) |
| `tests/test_puertas.py` (existing) | Emily | `Salida.costo` / `enlazar` sharing rules |

---

## Phase 1: Setup

- [ ] T001 Commit `specs/001-exit-costs/spec.md` (and the plan artifacts) in a dedicated commit before any code change, per Constitution VII (Owner: Emily) — all FRs
- [ ] T002 Run `python -m bench.bench_agenda` on the unchanged code and save its output to `specs/001-exit-costs/bench-parte1.txt` as the part-one baseline for §Measurements in plan.md (Owner: Emily) — FR-014

---

## Phase 2: Foundational (blocking all user stories)

**Purpose**: every exit carries a cost from the skeleton into the model. Andrea's DTO and repository tasks lead; the model attribute is the only engine piece the repository needs.

### Tests

- [ ] T003 [P] Write tests in `tests/test_costos_datos.py` for `SalidaDTO.desde_json`: `{"sala": 2, "costo": 300}` gives `costo == 300`, and `{"sala": 2}` gives `costo is None` (not 100). Values are not range-checked, so `{"sala": 2, "costo": 0}` gives `costo == 0` with no error (Owner: Andrea) — FR-001, FR-002
- [ ] T004 [P] Write tests in `tests/test_puertas.py` for `Salida`. The linking table from data-model.md: None/None → both `costo == 100`; x/None → both x; None/y → both y; x/x → both x. An exit with no opposite returns its declared value, or 100. `costo_declarado` stays `None` when neither side declares one (Owner: Emily) — FR-002, FR-005

### Implementation

- [ ] T005 [P] Add `costo` to `SalidaDTO.__init__` (default `None`) and read it in `desde_json` with `datos.get("costo")` in `dto/salida_dto.py`; "`None` = not declared. No range check (FR-001)" (Owner: Andrea) — FR-001, FR-002
- [ ] T006 [P] In `model/sala_logica.py`, add `Salida.__init__(..., costo=None)` storing `self.costo_declarado`. Add a read-only property `costo` returning `costo_declarado`, or `COSTO_MOVER` (imported from `model/tiempo_logica.py`) when it is `None`. In `enlazar`, copy a non-`None` `costo_declarado` to the side whose value is `None`, the same way `llave` is shared (Owner: Emily) — FR-002, FR-005
- [ ] T007 In `data/repositorio_cripta.py` `construir_salas`, pass `costo=salida_dto.costo` when creating each `Salida` (second loop). Depends on T005 and T006 (Owner: Andrea) — FR-001, FR-011
- [ ] T008 In `data/repositorio_cripta.py` `construir_salas`, third loop, before `salida.enlazar(otra)`: if `salida.costo_declarado` and `otra.costo_declarado` are both not `None` and differ, raise `ValueError` starting with "Puerta inconsistente:" and naming both rooms, both directions and both costs. Use the same message style as the existing check. Depends on T007 (Owner: Andrea) — FR-013
- [ ] T009 Write tests in `tests/test_costos_datos.py`:
  - Building rooms from `SalaDTO`s where A→B declares 300 and B→A declares nothing gives cost 300 on both exits (US1-7 at load).
  - Sides declaring 100 and 200 raise `ValueError` matching "Puerta inconsistente" (US1-6).
  - The existing room-mismatch inconsistent door still raises.
  
  Depends on T008 (Owner: Andrea) — FR-005, FR-013

**Checkpoint**: `python -m pytest tests/test_costos_datos.py tests/test_puertas.py` is green; every exit in the model has `costo`.

---

## Phase 3: User Story 1 — Movement duration depends on the exit crossed (P1) 🎯 MVP

**Goal**: the player's move schedules the next action at `reloj + intervalo(salida.costo, velocidad)`.

**Independent test**: build rooms with exit costs, move the player, and check `partida.reloj` / the player's next event time.

### Tests

- [ ] T010 [US1] Write tests in `tests/test_costos_salida.py`, building `Sala`/`Salida` by hand as `tests/test_puertas.py` does (Owner: Emily):
  - US1-1: cost 300, speed 100 → next action at T+300 (FR-003, FR-004)
  - US1-2: no cost → T+100 (FR-002, FR-004)
  - US1-3: A→B declared 250 and linked; moving B→A uses 250 (FR-005)
  - US1-4: cost 50, speed 150 → T+33 (FR-004)
  - US1-5: cost 1, speed 1000 → T+1 (FR-004, FR-006)
  - US1-7: only A→B declares 300 → moving B→A takes 300 (FR-005)
  - US1-8: in a room whose exits cost 500, attack and wait take the part-one intervals (FR-006)

### Implementation

- [ ] T011 [US1] Add `Partida._programar_movimiento(self, actor, salida)` in `model/partida_logica.py`, which calls `self._programar_siguiente(actor, salida.costo)`. Do not modify `intervalo` or `nuevo_tiempo_por_velocidad` (Owner: Emily) — FR-003, FR-004, FR-007
- [ ] T012 [US1] In `Partida.mover` (`model/partida_logica.py`), replace `self._programar_siguiente(self.jugador, COSTO_MOVER)` with `self._programar_movimiento(self.jugador, salida)`. Remove `COSTO_MOVER` from that file's import if it is no longer used there (Owner: Emily) — FR-003

**Checkpoint**: US1 tests green; MVP done.

---

## Phase 4: User Story 2 — Enemies are subject to the same exit costs (P1)

**Goal**: enemy moves use the exit cost, and their decisions are unchanged.

### Tests

- [ ] T013 [US2] Add to `tests/test_costos_salida.py` (Owner: Emily):
  - US2-1: a wanderer with speed 100 moving through a cost-200 exit at T → next action at T+200 (FR-007)
  - US2-2: a tracker, a fixed seed and a fixed action sequence → the sequence of chosen exits is identical to a run where every exit cost is 100, and only the event times differ (FR-008)
  - US2-3: an enemy with speed 50 scheduled through `_programar_movimiento` on a cost-120 exit at T → T+240 (FR-007). The docstring must state that the hunter feature must reuse this method.

### Implementation

- [ ] T014 [US2] In the enemy turn in `model/partida_logica.py` (the block after `_decidir_errante` / `_decidir_rastreador`): when `salida is not None`, call `self._programar_movimiento(enemigo, salida)`; otherwise keep `self._programar_siguiente(enemigo, COSTO_ESPERAR)`. Update the comment "Atacar, moverse y esperar cuesta 100". Do not touch `_decidir_errante` or `_decidir_rastreador` (Owner: Emily) — FR-006, FR-007, FR-008

---

## Phase 5: User Story 3 — Speed change while crossing an expensive exit (P1)

**Goal**: confirm that the existing rescaling (`EfectosLogica._cambiar_velocidad` → `nuevo_tiempo_por_velocidad` → `agenda.reprogramar`) applies to move events. No production code change is expected.

- [ ] T015 [US3] Add to `tests/test_costos_salida.py`, changing speed through `partida.efectos.aplicar_velocidad` (Owner: Emily):
  - US3-1: speed 100, cost 500 at t=0, change to 200 at t=100 → ends at 300
  - US3-2: speed 200, end 1000, change to 50 at t=900 → ends at 1300
  - US3-3: end 101, speed 10 → 1000 at t=100 → ends at 101

  All cite FR-009; US3-3 also cites FR-006.
- [ ] T016 [US3] If any T015 test fails, fix it in `model/efectos_logica.py` without changing `nuevo_tiempo_por_velocidad` in `model/tiempo_logica.py`. Otherwise mark this task done with no change (Owner: Emily) — FR-009

---

## Phase 6: User Story 4 — The player sees the cost of each exit (P2)

**Goal**: room view lines read `N -> Pasillo (abierta, costo 300)` (contracts/room-view.md).

- [ ] T017 [P] [US4] Write tests in `tests/test_vista_costos.py`, capturing stdout with pytest's `capsys` from `VistaConsola().mostrar_estado(partida)` (Owner: Andrea):
  - US4-1: `norte` cost 300 → `costo 300`; `sur` with no cost → `costo 100` (FR-010)
  - US4-2: a closed exit with cost 40 → `(cerrada, costo 40)` (FR-010)
- [ ] T018 [US4] In `view/vista_consola.py` `mostrar_estado`, change the exit line to `f"  {salida.direccion} -> {salida.destino.nombre} ({estado}, costo {salida.costo})"`. Leave `VistaReplay` and `VistaSilenciosa` unchanged. Depends on T006 (Owner: Andrea) — FR-010

---

## Phase 7: User Story 5 — Exit costs are always current; old saves and logs are rejected by version (P2)

**Goal**: prove that the existing behaviour meets FR-011 and FR-012. No new invalidation mechanism.

- [ ] T019 [P] [US5] Write tests in `tests/test_version_cripta.py` (Owner: Andrea):
  - US5-1: a `RepositorioCripta` with a fake source whose `pagina_esqueleto` returns exits with `costo` → the built rooms carry those costs, and the fake source records that the skeleton pages were requested (FR-011)
  - US5-2: `Aplicacion.validar_guardado` on a save whose header `version_cripta` differs returns the "otra cripta o versión" message (FR-012)
  - US5-3: `Aplicacion._versiones_coinciden` is False for a log with a different `version_cripta` (FR-012)
  - US5-4: a save with the matching version is accepted, and moves use the costs from the freshly built skeleton (FR-011, FR-012)

  Use fakes for the source and the catalog repository, with no network.
- [ ] T020 [US5] Check that no code path writes exit costs into saves (`adapters/guardado_binario.py`), logs (`adapters/bitacora_partida.py`) or the catalog cache (`adapters/almacen_fichas.py`), and that `VERSION_FORMATO` is unchanged. Record the result in the test module docstring of `tests/test_version_cripta.py` (Owner: Andrea) — FR-011, FR-012

---

## Phase 8: Section 5.6 measurements (Emily)

- [ ] T021 [P] Add a function to `bench/bench_ciclo.py`, next to `armar_partida`, that builds the same room chain with exit costs drawn from `random.Random(seed)` over {1, 10, 50, 100, 250, 500, 1000}, with the same cost on both sides of each door (Owner: Emily) — FR-014 (deterministic by seed, Constitution VI)
- [ ] T022 Extend `bench/bench_agenda.py` with these additions (Owner: Emily) — FR-003, FR-007, FR-014:
  - `contar_operaciones` run on the variable-cost builder with 300, 1000 and 3000 `errante` enemies
  - a variable-increment version of `medir_ciclo`: increment = `intervalo(cost, speed)`, cost from the set above, speed in [50, 200]
  - the fixed-increment and variable-increment results printed side by side

  Only the part-one candidates: `AgendaHeap`, `AgendaListaSinOrdenar`, `AgendaListaOrdenada`. Depends on T014 and T021.
- [ ] T023 Run `python -m bench.bench_agenda`, fill the §Measurements table in `specs/001-exit-costs/plan.md` from T002 and T022, and apply the decision rule (keep the heap if it is the fastest or within 10% of the fastest at every size ≥ 300). If the rule fails, open a separate commit reopening the agenda decision (Owner: Emily) — FR-014

---

## Phase 9: Polish & cross-cutting

- [ ] T024 [P] SC-004 regression: in `tests/test_costos_salida.py`, a fixed seed and action sequence on rooms with no `costo` and on rooms with `costo` 100 everywhere produce identical `reloj`, rooms and HP (Owner: Emily) — FR-002, FR-014
- [ ] T025 [P] FR-014 determinism: in `tests/test_costos_salida.py`, the same seed and actions on rooms with mixed costs, run twice, give identical final state (Owner: Emily) — FR-014
- [ ] T026 Run `python -m pytest`; all part-one tests stay green (Owners: Andrea, Emily) — FR-006, FR-008
- [ ] T027 Constitution gate: grep the changed files in `model/`, `data/` and `dto/` for `dict(`, `{}`, `set(`, `heapq`, `bisect` and `collections` used as an index or cache, and check that `model/` imports nothing from `view/` or `controller/` (Owners: Andrea for data/dto/view, Emily for model) — FR-015
- [ ] T028 Run the manual check in `specs/001-exit-costs/quickstart.md` (`python main.py`): exit lines show `costo`, and `Tiempo:` advances by `costo*100//velocidad` (Owner: Andrea) — FR-010, FR-004

---

## Dependencies & Execution Order

```text
T001 → T002
T003 ∥ T004 ∥ T005 ∥ T006         (Andrea: T003, T005 | Emily: T004, T006)
T005 + T006 → T007 → T008 → T009   (Andrea)
Phase 2 done → US1 (T010–T012) → US2 (T013–T014) → US3 (T015–T016)   (Emily, same files)
Phase 2 done → US4 (T017–T018) ∥ US5 (T019–T020)                     (Andrea, in parallel with Emily)
T014 + T021 → T022 → T023
All → T024–T028
```

- US1, US2 and US3 are sequential because they edit `model/partida_logica.py` and `tests/test_costos_salida.py`.
- US4 and US5 only need Phase 2, so Andrea can do them while Emily does US1–US3.
- T021 (bench builder) can start as soon as T006 is done.

## Parallel Example

```text
After Phase 2:
  Andrea: T017 → T018, then T019 → T020
  Emily:  T010 → T011 → T012 → T013 → T014 → T015 → T016, with T021 alongside
```

## Implementation Strategy

1. **MVP**: Phase 1 + Phase 2 + US1. The player's moves take exit-dependent time.
2. Add US2 (enemies) and US3 (speed-change tests). This completes the timeline rules.
3. Add US4 (view) and US5 (version tests) in parallel.
4. Phase 8 measurements, then Phase 9 polish.
5. Commit per task group; a spec correction always goes in its own commit before the code that follows it (Constitution VII).
