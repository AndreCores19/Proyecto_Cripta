# Quickstart: validating the hunter

## Prerequisites

- Python 3.11+, with dependencies from `requirements.txt` installed (`pytest`, `requests`).
- `spec.md` committed (Constitution VII).

## Automated tests

```powershell
python -m pytest tests/test_monticulo.py tests/test_puertas.py tests/test_cazador_decision.py tests/test_cazador_equivalencia.py tests/test_cazador_conocimiento.py tests/test_catalogo_cazador.py tests/test_vista_cazador.py tests/test_bench_cazador.py tests/test_replay_cazador.py -v
python -m pytest
```

Each test name or docstring cites its FR. Expected mapping:

| Scenario | Test checks | FR |
|---|---|---|
| US1-1 | hunter in the player's room attacks and does not move | FR-002 |
| US1-2, US1-3 | `d` ≤ `rango` (also `d == rango`) → moves along a route of cost `d` | FR-003, FR-004, FR-005 |
| US1-4 | `d > rango` → stays, next action at T + 100 | FR-004 |
| US1-5 | only route through a closed door → waits, the door stays closed | FR-004, FR-009 |
| US1-6 | cheapest route wins over fewest exits | FR-003, FR-005 |
| US1-7 | speed 50, `costo` 120 → next action at T + 240, destination entered at T; speed change while crossing (hunter) rescales the pending action | FR-006 |
| US2-1, US2-2 | tie between neighbours → lowest room id, only among neighbours on a route of cost `d` | FR-007 |
| US2-3 | grid crypt with many equal routes → lowest id among the neighbours on a route of cost `d` | FR-007 |
| US3-1..5 | after a door closes or opens, the player moves, an actor dies or an automatic door closes, the decision equals the reference computation | FR-011, FR-012 |
| US4-1..4 | rooms never visited or not downloaded do not change any decision; same result with content downloaded or not | FR-008, FR-010, FR-014 |
| US5-1 | catalog entry `cazador` with `rango` 400 → hunter with `rango` 400 | FR-001 |
| US5-2, US5-3 | crypts without hunters equal the spec 001 result; wanderers and trackers keep their rules | FR-013 |
| US5-4 | hunter not activated yet takes no turns even with the player in range | FR-022 |
| US5-5 | entry with no `rango` → `rango` 0 | FR-001 |
| US6-1, US6-2 | hunter line shows `(cazador)`; rooms without hunters print as before | FR-016 |
| US7-1 | benchmark prints p99 and maximum of the event cycle with 30 hunters, also with `rango` reaching the whole crypt; verdict p99 <= 20 ms | FR-017 |
| US7-2 | decision time with the same region in a crypt ≥ 10× larger | FR-018 |
| US7-3, US7-4 | all FR-019 comparisons are printed; every mode takes the same decisions | FR-019, FR-011 |
| US7-5 | same seed, same synthetic crypt | FR-020 |
| US7-6 | benchmark and replay create no `view/` class | FR-021 |
| Search limit | a shared cache computed for a small `rango` is recomputed when a hunter with a bigger `rango` asks; the invariant error fires if forced | FR-018, FR-011 |
| Other search between turns | an unrelated search run between two hunter turns does not change the decision | FR-011 |
| Determinism | same crypt, seed and actions twice → same final state, including replay | FR-014 |

## Assignment Appendix B cases (Constitution IX)

The "Terreno y cazador" section of Appendix B has exactly seven cases; this mapping was confirmed against the full appendix. Where each is covered:

| Appendix B case | Acceptance scenario | Test |
|---|---|---|
| no open route to the player | spec 002 US1-5 | T017 in `tests/test_cazador_decision.py` |
| route cost above `rango` | spec 002 US1-4 | T016 in `tests/test_cazador_decision.py` |
| fewer rooms but higher cost vs more rooms and lower cost | spec 002 US1-6 | T018 in `tests/test_cazador_decision.py` |
| two neighbours tie | spec 002 US2-1 | T023 in `tests/test_cazador_decision.py` |
| a door on the route closes between turns | spec 002 US3-1 | T028 in `tests/test_cazador_equivalencia.py` |
| high-speed actor through an exit of cost 1 | spec 001 US1-5 | `test_costo_1_velocidad_1000_tarda_al_menos_1` in `tests/test_costos_salida.py` |
| speed change while crossing a costly exit | spec 001 US3-1, US3-2, US3-3 | `test_acelerar_a_mitad_de_un_movimiento_acorta_el_resto`, `test_frenar_a_mitad_de_un_movimiento_alarga_el_resto`, `test_el_resto_de_un_movimiento_nunca_baja_de_1` in `tests/test_costos_salida.py`; also for the hunter, T019 in `tests/test_cazador_decision.py` |

## Benchmarks (Constitution VI)

Before changing any code, save the baseline:

```powershell
python -m bench.bench_ciclo   > specs/002-hunter-enemy/bench-antes-ciclo.txt
python -m bench.bench_agenda  > specs/002-hunter-enemy/bench-antes-agenda.txt
```

After the last change:

```powershell
python -m bench.bench_ciclo   > specs/002-hunter-enemy/bench-despues-ciclo.txt
python -m bench.bench_agenda  > specs/002-hunter-enemy/bench-agenda-cazadores.txt
python -m bench.bench_cazador
python -m bench.bench_ciclo --modos > specs/002-hunter-enemy/bench-ciclo-modos.txt
```

`--modos` runs every `bench_ciclo` scenario once per hunter mode (`individual`, `compartido_sin_reuso`,
`compartido`); `bench-ciclo-modos.txt` is the output the mode decision in plan.md §Measurements used.

Copy the tables into plan.md §Measurements and apply its decision rule. `python main.py --bench`
runs all of them, including the per-mode run. The reference crypt is the synthetic one until the course publishes its own (spec
Clarifications).

## Manual check

1. `python main.py <crypt with a hunter>`: a room with a hunter lists it as `Name (cazador) [id] (Vida: …)`; other enemies and rooms print as before.
2. Walk away from the hunter inside and outside its `rango`: it follows only while the route cost is within `rango`, and `Tiempo:` advances by `costo*100//velocidad` for each of its moves in the log.
3. `python main.py --replay <log>` of that game prints the same text as before and creates no view.
