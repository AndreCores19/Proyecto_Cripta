# Quickstart: validating exit costs

## Prerequisites

- Python 3.11+, with dependencies from `requirements.txt` installed (`pytest`, `requests`).
- `spec.md` committed (Constitution VII).

## Automated tests

```powershell
python -m pytest tests/test_costos_salida.py tests/test_puertas.py tests/test_service.py -v
```

Each test name or docstring cites its FR. Expected mapping:

| Scenario | Test checks | FR |
|---|---|---|
| US1-1..4 | next action at `reloj + max(1, costo*100//velocidad)` | FR-003, FR-004 |
| US1-5 | cost 1, speed 1000 → interval 1 | FR-004, FR-006 |
| US1-6 | sides declare 100 / 200 → "Puerta inconsistente" | FR-013 |
| US1-7 | one-sided 300 applies B→A | FR-005 |
| US1-8 | attack/wait unchanged next to cost-500 exits | FR-006 |
| US2-1..3 | wanderer / tracker / (hunter when it exists) move durations; same decisions as part one with the same seed | FR-007, FR-008 |
| US3-1..3 | speed change mid-crossing → end = now + max(1, (end−now)*old//new) | FR-009 |
| US4-1..2 | room view prints `costo` for open and closed exits | FR-010 |
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
