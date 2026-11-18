# Contract: command line

## `--checkpoint-cada K`

- Accepted with a normal game, a game started by name, and `--replay`; ignored by `--verificar`.
- K must be a positive integer. Missing value, `0`, negative or non-numeric: argparse-style error,
  exit status 2, nothing runs, no request is made (FR-019).
- Absent: the default K (`model/linea_tiempo_logica.K_POR_DEFECTO`, provisional 50, replaced by task T068 with the measured value; see
  `plan.md`, "Default K").
- Loading a game saved with K1 while `--checkpoint-cada K2` was typed and K2 ≠ K1: the game uses K1
  and shows "Se ignora --checkpoint-cada: esta partida se guardó con K=<K1>." (FR-017). If the option
  was not typed, no notice.

## `--replay LOG --hasta T`

- `--hasta` requires `--replay`; T is a non-negative integer. Malformed or negative: error message,
  exit status 1, **no state printed** (FR-013). A bad log is reported as in earlier specs (no state).
- Replays the log through `Controlador` with no view (`vista=None`; output through
  `adapters/salida_replay.py`), builds the timeline as the game does, stops as soon as the clock is
  ≥ T or the commands end, then prints the summary of instant T (same text as in-game, FR-014).
- If T is greater than the final clock: prints the final state and the line
  "La partida terminó antes (instante <final clock>)." (FR-015).
- Exit status 0 in both cases. No view class is created (FR-016). Requests/budget as `--replay` does
  today (the catalog); the query itself makes none.

## `--bench`

Runs the existing benchmarks plus `bench_linea_tiempo` (report format in
[reporte-bench-linea-tiempo.md](./reporte-bench-linea-tiempo.md)); `bench_historial` prints the
part-one figures next to the with-timeline figures. No network, no view (FR-016, FR-024, FR-025).
