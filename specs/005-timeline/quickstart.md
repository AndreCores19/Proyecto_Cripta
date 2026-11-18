# Quickstart: validating the timeline

Prerequisites: Python 3.11+, `pip install -r requirements.txt`, the offline pack in `offline/`
(`--offline` needs no network). Details of each interface are in `contracts/`; entities in
`data-model.md`.

## 0. Baseline (already saved)

`specs/005-timeline/bench-antes.txt` holds `bench_historial` and `bench_guardado` as they were before
any code change. Do not regenerate it.

## 1. Automated tests

```bash
python -m pytest tests -k "linea_tiempo" -q
```

Expect: every acceptance scenario of the spec passes, each test naming its FR; the oracle test
compares a query with the live summary at every decision for K = 1, 3, 7 and K > game length.

## 2. Consult in a game (US1, US2)

```bash
python main.py cripta-01 --offline --checkpoint-cada 5
```

Play ~20 commands (moves, an attack, a pick-up), then:

| Type | Expect |
|---|---|
| `historia 0` | initial state |
| `historia #3` | state just before your 3rd action |
| `historia <current clock>` | the current state |
| `historia <current clock + 1>` | rejected, nothing changes |
| `historia #<actions + 1>`, `historia`, `historia -2` | rejected with the accepted forms |

Then `salir`: the `saves/partida_*.log` file must not contain a single `historia` line.

## 3. Scroll (US3)

With a scroll in the inventory: act 4 times, `retroceder`, then `historia #4` must be rejected unless
you have taken a new 4th action, and any instant must not show the reverted action. Repeat with
the reverted action being a move into a room you had never entered, and then enter that room again:
`historia` for the instants after the scroll must show the same room contents and object ids the
game shows. The consumed scroll must not appear in any instant after the rewind point.

## 4. Replay without a view (US4)

```bash
python main.py --offline --replay saves/partida_<cripta>_<seed>.log --hasta 300
python main.py --offline --replay saves/partida_<cripta>_<seed>.log --hasta 99999999
python main.py --offline --replay saves/partida_<cripta>_<seed>.log --hasta -1
```

Expect: the summary equal to `historia 300` typed in the game; the second prints the final state and
"the game ended earlier"; the third prints an error and no state. No view is created.

## 5. Save, load, old format (US5)

`guardar prueba`, quit, start again, `cargar prueba` (the commands are re-executed and the
timeline is rebuilt): the same `historia` answers as before saving, also for a game saved after a
scroll; a different `--checkpoint-cada` gives the notice and keeps the saved K. Then try a v1 file
(`tests/fixtures/guardado_v1.sav`, written by the part-one code): "Formato de guardado incompatible",
file untouched, current game unchanged. An empty file and random bytes: "unreadable".

## 6. Benchmarks (US6, US7, US8)

```bash
python -m bench.bench_linea_tiempo
python -m bench.bench_historial
python -m bench.bench_guardado      # unchanged scenarios; header +4 bytes only
python main.py --bench
```

Expect: the report of `contracts/reporte-bench-linea-tiempo.md` with K = 10, 50, 200 and the
no-checkpoint row, p99 ≤ 50 ms at the default K on ≥ 5 000 actions, "max actions re-played ≤ K"
for every K row, linear memory growth, the part-one figures next to the with-timeline figures, and
no checkpoint off the K grid, identical output for the same seed on two runs. Copy the tables into `docs/DECISIONES.md` and the
chosen default K into `plan.md`.

## 7. Layer and network checks

A test makes every class in `view/` raise on construction and runs `--replay ... --hasta` and the
benchmark; a test with a client that raises on any call runs 100 queries on a long game and checks
that the request counter did not move and that `partida.log` is byte-for-byte the same.

## 8. Appendix B: several events at the same instant

In a seeded test game, pick an instant at which two or more non-player events run (for example two
enemies acting) and the player has no decision. `historia <t>` must show the state after all of them.
Then pick an instant at which the player has a decision: the state is the one just before it and
events of that instant that come later in agenda order are not shown ("the decision wins").
