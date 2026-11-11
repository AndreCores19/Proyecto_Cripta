# Quickstart: validating exit costs

## Prerequisites

- Python 3.11+, with dependencies from `requirements.txt` installed (`pytest`, `requests`).
- `spec.md` committed (Constitution VII).

## Automated tests

```powershell
python -m pytest tests/test_costos_datos.py tests/test_puertas.py tests/test_costos_salida.py tests/test_vista_costos.py tests/test_frontera_servicio.py tests/test_service.py tests/test_version_cripta.py tests/test_replay_costos.py tests/test_salida_replay.py -v
```

Each test name or docstring cites its FR. Expected mapping:

| Scenario | Test checks | FR |
|---|---|---|
| US1-1 | actor in destination room at T; next action at T+300 | FR-003, FR-004, FR-016 |
| US1-2, US1-4 | next action at `T + max(1, costo*100//velocidad)` | FR-002, FR-004 |
| US1-3 | both sides declare 250 → 250 in both directions | FR-005 |
| US1-5 | cost 1, speed 1000 → interval 1 | FR-004, FR-006 |
| US1-6 | sides declare 100 / 200 → "Puerta inconsistente" | FR-013 |
| US1-7 | one-sided 300 applies B→A | FR-005 |
| US1-8 | attack/wait unchanged next to cost-500 exits | FR-006 |
| US2-1, US2-3 | wanderer (and enemy via `_programar_movimiento` for the hunter case) in destination at T, next action at T + interval | FR-007, FR-016 |
| US2-2 | from a fixed state (room, trails, clock, open exits) with costs ≠ 100, the tracker picks the part-one rule's exit | FR-008 |
| US3-1..3 | speed change before the next action → next action at now + max(1, (end−now)*old//new) | FR-009 |
| US4-1..2 | `estado_vista()` exits carry `costo`; the room view prints it for open and closed exits; the view never receives `Partida` | FR-010 |
| Replay | `--replay` creates no `view/` class; its output equals the golden files captured from part-one `VistaReplay` | FR-014, Constitution III |
| Boundary | every service → controller/view/persistence crossing is a DTO or plain value ([contracts/service-boundary.md](./contracts/service-boundary.md)); end-of-game and inventory output unchanged; `atacar` by id | FR-010, FR-014, Constitution III |
| US5-1 | exit costs come from the skeleton downloaded at start | FR-011 |
| US5-2..3 | saved game / replay log from another crypt version refused | FR-012 |
| US5-4 | same-version save loads and uses the fresh skeleton's costs | FR-011, FR-012 |
| SC-004 | crypt without any `costo` → same final state as part one | FR-002, FR-014 |

## Manual check

1. Run the game (`python main.py`, or with `--offline` on a recorded part-two crypt).
2. In a room, check that each exit line shows `costo N`.
3. Move through an exit with a high cost and check that `Tiempo:` advances by `costo*100//velocidad`.

## Benchmarks (section 5.6)

```powershell
python -m bench.bench_agenda
```

Copy the fixed-cost and variable-cost tables into plan.md §Measurements and apply its decision rule.
