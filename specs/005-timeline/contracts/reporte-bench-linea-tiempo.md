# Contract: `--bench` report for the timeline (FR-024 … FR-027)

Seeds are printed. Same seed → same game (FR-025). No network, no view.

```text
== Timeline: memory and query time (world=<name>, actions=<A>, seed=<s>, queries=<q>) ==
      K | checkpoints | memory checkpoints | memory actions + ledger | graph build | max actions re-played |
        | p99 (ms) | mean (ms) | worst (ms) | verdict p99 <= 50 ms
     10 | ...
     50 | ...
    200 | ...
   none | 1 (start) | ...                  | ...            | ...         | A (whole game)       | ...
Default K: <value>   rule: largest K with p99 <= 25 ms; memory of every K shown in the table above   -> <table row>
Linearity (K=<default>): A=<A> memory=<m1>  A=<2A> memory=<m2>  ratio=<m2/m1>   (expected ~2, not A*S)
Scroll reads=<n>  ledger entries kept=<n>  checkpoints off the K grid=0
Forward vs backward: re-simulate forward <x> us/action | invert backward <y> us/action |
                     closures per action in Historial <z> | extrapolated bytes at A actions <b>

== Part one under the new load (bench_historial) ==
scenario | action (part one) | action (timeline) | undo (part one) | undo (timeline) |
         | closures kept (max 5 frames) | capture checkpoint (us)

== Save (bench_guardado, unchanged scenarios) ==
rooms | size baseline (bench-antes.txt) | size v2 | save v2 (ms) | load all v2 (ms)
(only to show the 4-byte header change moves nothing; the timeline is not in the file)
```

Reference rows of the "before" baseline are in `specs/005-timeline/bench-antes.txt`. The query set
covers the whole game by seed, including the oldest and most recent instants; p99 is
`ordenados[int(n·0.99)]` as in `bench/bench_ciclo.py`; the worst is information, not a limit.
