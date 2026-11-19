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
python main.py cripta-02 --offline --checkpoint-cada 5
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

## Result of the run (T076, 2026-11-18)

Run against the real offline pack (`offline/`, a copy in a scratch folder so `saves/` and `cache/` stayed out of
the repo), Windows 11, Python 3.14.6. Sections 2–5 were played by a script that drives `main.py` through its
standard input and reads each answer, so every check below compares real output; 24 checks, 24 passed.

| § | What was checked | Result |
|---|---|---|
| 1 | `python -m pytest tests -k "linea_tiempo"` | 220 passed (inside the full run of T077: 610 passed) |
| 2 | cripta-02, 17 commands (moves, an attack, pick-ups): `historia 0`, `historia #3`, `historia <clock>`; `historia <clock+1>`, `historia #<n+1>`, `historia`, `historia -2` rejected with nothing changed; no `historia` line in `saves/partida_*.log` | pass |
| 3 | 3 waits and a move into a never-entered room, then `retroceder`: the reverted action is gone (`#21` rejected), `historia <now>` equals the game, the consumed scroll is in neither inventory; re-entering the room and picking up its object gives the same object ids in `historia` as in the game | pass |
| 4 | `--replay LOG --hasta 620` equals `historia 620` typed in the game; `--hasta 99999999` prints the final state and "La partida terminó antes"; `--hasta -1` exits 1 with an error and no state | pass |
| 5 | `guardar prueba`, quit, start again, `cargar prueba`: the same answers at 0, 150, 400 and the final clock (the game had read a scroll); with `--checkpoint-cada 7` the notice "Se ignora --checkpoint-cada: esta partida se guardó con K=5." and the same answers; `guardado_v1.sav` → "Formato de guardado incompatible", file untouched, game unchanged; empty file → "El archivo está truncado"; random bytes → "No es un archivo de guardado de Cripta" | pass |
| 6 | `bench_linea_tiempo`, `bench_historial`, `bench_guardado`: see `bench-linea-tiempo.txt`, `bench-despues.txt`, `plan.md` ("Default K") and `docs/DECISIONES.md` §5.5.1 and §5.6.2. `python main.py --bench` ran end to end (exit 0, 2 557 s) and printed "Default K: 10" (`referencia` K = 10: p99 15.35 ms). The non-timing columns (checkpoints, memory of checkpoints and of actions + ledger, max actions re-played, linearity, scroll reads, ledger entries, off-grid checkpoints) are identical on two runs of the same seed in separate processes; repeated inside one process the actions + ledger memory moves by 0.1 KB (`tracemalloc` noise), the game figures do not | pass |
| 7 | `tests/test_linea_tiempo_capas.py` (views and HTTP client raise; `--replay --hasta` and `--bench`), `test_linea_tiempo_consulta.py::test_las_consultas_no_tocan_la_red_ni_el_catalogo_aunque_la_ficha_se_haya_desalojado` (100 queries), `test_linea_tiempo_comando.py::test_la_consulta_no_queda_en_la_bitacora_ni_en_los_comandos_guardados` (log byte for byte) | pass |
| 8 | `test_linea_tiempo_consulta.py::test_varios_eventos_en_el_mismo_instante_se_ven_todos` and `::test_con_decision_del_jugador_en_t_gana_la_decision` | pass |

What the run showed, and what was fixed:

- §2 named `cripta-01`, which is not in the offline pack (it has cripta-02 … cripta-06); changed to cripta-02.
- The summary printed "Jugador: Jugador" while the game showed the player's own name: the scratch game never
  had the name, and the log does not record it, so `--replay --hasta` could not print it either (FR-014). The
  name is not one of the summary's fields (contract `comando-historia.md`), so `adapters/formato_historia.py`
  no longer prints it ("Jugador (Vida: …)"); test
  `test_linea_tiempo_comando.py::test_el_resumen_no_muestra_el_nombre_del_jugador_que_el_replay_no_conoce`.
- Information, not a failure: in the stress world `grande` (not the verdict world) K = 10 gave p99 54.31 ms in the
  full `--bench` run, against 47.64 ms in the T068 run; `referencia` stays far below the 25 ms rule.
