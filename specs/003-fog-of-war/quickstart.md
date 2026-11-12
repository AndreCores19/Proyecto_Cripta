# Quickstart: validating fog of war and "ir a"

## Prerequisites

- Python 3.11+, dependencies from `requirements.txt` installed (`pytest`, `requests`).
- `spec.md` committed (Constitution VII).
- Baseline saved before any code change:

```powershell
python -m bench.bench_ciclo > specs/003-fog-of-war/bench-antes-ciclo.txt
```

## Automated tests

```powershell
python -m pytest tests/test_niebla_estados.py tests/test_niebla_puertas.py tests/test_niebla_antorcha.py tests/test_niebla_retroceso.py tests/test_ir_a_ruta.py tests/test_ir_a_viaje.py tests/test_ir_a_bitacora.py tests/test_vista_niebla.py tests/test_bench_ir_a.py -v
python -m pytest
```

Each test name or docstring cites its FR. Expected mapping:

| Scenario | Test checks | FR |
|---|---|---|
| US1-1, US1-2 | start: only the starting room explored, its destinations sighted; entering a sighted room explores it | FR-001..FR-004 |
| US1-3..US1-6 | explored room shows name, exits, costs, doors; sighted shows no name; unknown does not appear | FR-003..FR-005, FR-010, FR-011 |
| US1-7 | re-entering keeps the state | FR-001 |
| US1-8 | exit toward a sighted room shows no destination name | FR-004, FR-010 |
| US2-1..US2-5 | map keeps the last observed door state; refreshed on observation; continuous while inside | FR-006, FR-007 |
| US3-1..US3-4 | torch explores all neighbors, open or closed; no enemy or trap activated; no content read | FR-008, FR-009 |
| US3-5 | torch does not observe the neighbor's other doors | FR-009, FR-017 |
| US3-6 / scenario 5 | scroll reverts the rooms explored by the torch | FR-013, FR-014 |
| US4-1..US4-4 | save, load and replay give identical knowledge; scroll restores it | FR-012..FR-014 |
| US5-1..US5-3 | `mapa` lists explored rooms and their exits, sighted rooms, no unknown ones, no time | FR-005, FR-015 |
| US6-1 / scenario 1 | unexplored destination rejected, no time consumed, comment only in the log | FR-016, FR-024 |
| US6-2..US6-5 | cheapest route, lowest-id first step, only explored rooms | FR-017, FR-018 |
| US6-6 | remembered-closed door never opened even with the key | FR-017, FR-021 |
| US6-7 | per-step time follows exit cost; clock events between steps | FR-019 |
| US6-8, US6-9 | log has one move per step and a comment for the order, also when rejected | FR-024 |
| US6-10 | already in the destination: arrival, no time | FR-022 |
| US7-1 / scenario 2 | door remembered open but closed: map updated, route recomputed, trip stops with no extra time | FR-006, FR-020, FR-022 |
| US7-2 | alternative known route is taken | FR-020 |
| US7-3 / scenario 3 | sleeping enemies activate by the part-one rules and the trip stops | FR-022 |
| US7-4..US7-6 | stops for active enemies, damage (trap, enemy, poison) and end of game | FR-022, FR-023 |
| US7-7 | several reasons at once: the first in the order of FR-022 is shown | FR-022, FR-023 |
| US7-8, US7-9 | stops when no route remains; recomputed after clock events | FR-020, FR-022 |
| US8-1 / scenario 6 | scroll between steps reverts only the last step, the trip does not continue and stops with its own reason | FR-022, FR-023, FR-025 |
| US8-2, US8-3 | knowledge of the last step reverts with it | FR-013, FR-025 |
| US9-1 | one route computation on the full known map ≤ 5 ms | FR-026 |
| US9-2 | same seed, same synthetic crypt | FR-027 |
| Hunter cache | a trip step between two hunter turns does not change the hunter decision | FR-011 (spec 002) |
| No view | replay of a game with a trip creates no `view/` class | Constitution III |

Route and tie-break tests compare `RutaConocida` with an oracle written in `tests/` (plain repeated
relaxation over lists) on seeded random crypts with closed doors and unexplored rooms.

## Benchmarks

```powershell
python -m bench.bench_ir_a
python -m bench.bench_ciclo > specs/003-fog-of-war/bench-despues-ciclo.txt
```

Expected: `bench_ir_a` prints, per crypt size, the average, the 99th percentile and the maximum of one
route computation and of a whole step, with the verdict `p99 <= 5 ms` for the reference size.
`bench_ciclo` keeps p99 ≤ 20 ms in every scenario; compare the averages with the "before" file.

## Manual check

```powershell
python main.py --offline
```

Start a game, confirm only the starting room has a name and its exits read `sin explorar`; walk one
step and run `mapa`; light a torch (`usar` on it) and enter a room to see the neighbors named; run
`ir a <id>` toward an explored room and toward an unexplored one; read the generated `partida_*.log`
and check the `# ir a` comments and the move lines.
