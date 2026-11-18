# Quickstart: Crypt Solvability Verification

How to check the feature end to end once it is built. Everything runs offline or with fakes; no test needs
the network.

## Automated checks

```powershell
python -m pytest tests/test_solvabilidad_orden.py tests/test_solvabilidad_informe.py tests/test_solvabilidad_llaves.py tests/test_solvabilidad_comandos.py tests/test_bench_solvabilidad.py -v
python -m pytest
```

Test builders and the independent oracle (full pass per key, plain lists) are in `tests/mapas_solvabilidad.py`.

## Manual check

```powershell
python grabar_offline.py                          # re-records the offline package, now with llaves.json (needs the network once)
python main.py --offline --verificar cripta-03    # prints the report; no game, no view
python main.py --offline cripta-03                # solvable: shows verdict and order of keys, then the game starts
python -m bench.bench_solvabilidad                # 300-room verdict and the naive comparison
```

For a non-solvable crypt: without `--forzar` the report is shown and the game does not start; with `--forzar`
the report is shown and the game starts.

## Scenarios → checks

| Scenario | What to check | FR |
|---|---|---|
| US1-1 | solvable crypt: verdict and order shown, game starts | FR-014, FR-008 |
| US1-2 / mandatory 4 | non-solvable crypt without `--forzar`: report shown, no game | FR-015 |
| US1-3 | the player's knowledge changes nothing (the same verdict with a fresh game and a played one) | FR-001 |
| US2-1 | chained keys: every key after the keys that open its way, checked against the oracle | FR-008, FR-009 |
| US2-2 / mandatory 3 | several valid orders: two runs give the same order, lowest id first | FR-010, FR-011 |
| US2-3 | rooms and keys listed in another order give the same order | FR-010 |
| US3-1 / mandatory 1 | exit key behind the only door it opens: not solvable, a cycle of length one | FR-012 |
| US3-2 | report lists exactly the unobtainable keys, frontier doors and locations | FR-012 |
| US3-3 | chain of keys: the concrete cycle, the same in two runs | FR-012, FR-010 |
| US3-4 | the report comes from one pass: counting door and room visits, no pass per key | FR-013 |
| US4-1 / mandatory 2 | key dropped by a wandering enemy: located in the enemy's initial room | FR-003 |
| US4-2 | key carried by an enemy in an unreachable room: not obtainable, reported with its location | FR-003, FR-012 |
| US5-1 | `--forzar` starts a non-solvable crypt | FR-016 |
| US6-1, US6-2 | `--verificar` prints the report, starts no game, creates no view class | FR-017 |
| US7-1 | the key query counts in the budget (fake client counts one request) | FR-002, FR-004 |
| US7-2 | another crypt version: the saved answer is not used, the query is made again | FR-005 |
| US7-3 | same version: the saved answer is used, no query | FR-005, FR-004 |
| US7-offline | `--offline` reads `llaves.json`, counts nothing | FR-006 |
| US8-1 | synthetic crypt shaped like the largest published one: maximum ≤ 200 ms | FR-018 |
| US8-2 | chained-key crypts: verification grows ~linearly, naive grows ~quadratically, same order of keys | FR-019, FR-021 |
| US8-3 | same seed, same synthetic crypt | FR-020 |

Contracts: [consulta-llaves.md](./contracts/consulta-llaves.md), [cache-llaves.md](./contracts/cache-llaves.md),
[paquete-offline-llaves.md](./contracts/paquete-offline-llaves.md),
[reporte-verificacion.md](./contracts/reporte-verificacion.md),
[comandos-verificar-forzar.md](./contracts/comandos-verificar-forzar.md). Data: [data-model.md](./data-model.md).
