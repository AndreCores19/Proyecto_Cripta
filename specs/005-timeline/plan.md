# Implementation Plan: Timeline (consult the game at any past instant)

**Branch**: `005-timeline` | **Date**: 2026-11-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-timeline/spec.md`

## Summary

The player can ask "historia <t>" or "historia #k" and see the state of the game at that moment
without touching the game. The timeline keeps, for every player action that survives in the game as
it ended up, a small **action record** (its number, the clock of the decision, and the resolved
action: kind + target). Every **K player actions** it also keeps a **checkpoint**: a full state
record of the mutable game state, including the random generator and the known map. A query finds
the checkpoint by index (`boundary // K`), or the action for an instant with our own binary search
over the stored clocks, builds a **scratch world** (a fresh room graph from the crypt skeleton plus
the checkpoint), and **re-simulates forward** at most K player actions, stopping by the instant-t
rule. The scratch world is a separate object graph: the query never touches the live game, its undo
history, `partida.log`, the clock, the network or the request budget.

Decisions the group has to know about (all argued in [research.md](./research.md)):

1. **Forward re-simulation, not backward inversion** (R1). The part-one undo history keeps closures,
   bounded to 5 actions, not serializable and not trimmable per action; using it for thousands of
   actions would need one closure list per action (the baseline shows 48 to 1 200 closures per action).
2. **Checkpoints are hand-written state records, not copies** (R2). `copy.deepcopy` is forbidden in the
   model (constitution, technology stack) and would also copy the history closures, the catalog
   cache and the HTTP client through `creador_objetos`. A record holds only mutable fields, by stable
   ids, and is applied to a fresh graph.
3. **A scroll records the effects the undo skips** (R6). The part-one history deliberately leaves
   some effects outside the undo (consumed scroll, scroll objects moved by the reverted actions,
   the factory's instance counter, rooms populated by the reverted moves), so re-playing the
   surviving actions would not give the live state after a scroll. A scroll trims from the end only
   and **no checkpoint is added** (at most one every K actions, as the assignment says). Instead,
   the skipped effects are kept in a small **ledger of skipped effects** tagged with the rewind
   point and applied when a re-simulation passes that point.
4. **Saving writes the commands and K, not the timeline** (R9). Format v1 → v2: only K is added to the
   header; a v1 file is reported as incompatible by the existing check, which is moved ahead of the
   header read so a short v1 file cannot be reported as "truncated". Load re-executes the commands
   (as in part one) and that rebuilds the whole timeline: actions, checkpoints and ledger.
5. **The default K is provisional (K = 50) until measured.** The code carries `K_POR_DEFECTO = 50`
   marked PROVISIONAL so a game starts without `--checkpoint-cada` from the first phase. It is
   replaced by the value chosen from `--bench` numbers (FR-026) in task T068 and recorded in
   "Default K" below.

## Technical Context

**Language/Version**: Python 3.11+ (measured on 3.14.6 locally)

**Primary Dependencies**: none new. `array` (stdlib typed arrays) for the random-generator state; the
benchmark may use `time`, `gc`, `tracemalloc`, `tempfile` (constitution, benchmarking utilities).

**Storage**: the existing `saves/*.sav` binary file, version 2 (see
[contracts/formato-guardado-v2.md](./contracts/formato-guardado-v2.md)). `partida.log` is unchanged.

**Testing**: pytest (`tests/`), one test per acceptance scenario citing its FR; an independent oracle
(the live summary recorded at every decision of a seeded game) is compared with every query answer.
No test uses the network (fake clients, offline pack).

**Target Platform**: desktop console (Windows/Linux); `--replay` and `--bench` headless.

**Project Type**: CLI game, five-layer architecture (data → logic → service → controller → view).

**Performance Goals**: FR-024: `historia` p99 ≤ 50 ms on a synthetic game of ≥ 5 000 player actions
with the default K (max reported). The reference world for the verdict is the spec 002 reference
world (cripta-06 skeleton, 30 hunters); `grande` (100 rooms, 100 enemies) is run as a stress case and
`extremo` is reported for information (R11).

**Constraints**: Constitution I (no `dict`/`set`/`heapq`/`bisect`/`collections`; no `copy` in the
model), II (fixed ties), III (layers, DTOs, no view in `--replay`/`--bench`), IV (nothing
crypt-specific in code), V (re-simulation: zero requests), VI (every claim from `--bench`, synthetic
games deterministic by seed), VIII (this plan adds no rule).

**Scale/Scope**: ≥ 5 000 player actions per game; K ∈ {10, 50, 200} + "no checkpoint" measured;
crypts up to 300 rooms (cripta-06), synthetic up to 100 rooms with 300 enemies.

## Constitution Check

*GATE: checked before Phase 0 and re-checked after Phase 1 — PASS (no violation to justify).*

### Structures Gate

| Item | Status | Notes |
|---|---|---|
| No `dict`/`set` as index or cache in an evaluated structure | PASS | Action table, clocks and checkpoints are parallel lists/arrays. Checkpoint by index `boundary // K`. Entity lookup while restoring (room, enemy, object, trap by id) uses sorted vectors with the existing binary search (`structures/vector_busqueda.py`), built with `structures/ordenamientos.py`. Frozen ficha store is a `VectorBusqueda`. |
| No `heapq`, `bisect`, `collections` | PASS | The search over clocks is our own `ultimo_menor_o_igual` in `structures/linea_tiempo.py`. The agenda in the scratch world is the existing hand-written heap. |
| No `copy` in the model | PASS | Capture/restore are hand-written (`model/registro_estado.py`); `copy` appears only in `bench/`. |
| No external graph or pathfinding library | PASS | None used. |
| Hand-written structures cover the timeline | PASS | `LineaTiempo` (vectors + binary search + trim), `RegistroEstado`, the ledger of skipped effects (a chronological list), frozen ficha store. |

### Architecture Gate

| Item | Status | Notes |
|---|---|---|
| `model/` and `structures/` import nothing from `view/` or `controller/` | PASS | New model files import only `structures/` and other `model/` files. |
| `--replay` and `--bench` create no view class | PASS | `--replay ... --hasta` prints through `adapters/salida_replay.py`; `bench/bench_linea_tiempo.py` builds worlds directly. A test makes every class in `view/` raise on construction and runs both paths. |
| DTOs at every boundary | PASS | `RespuestaHistoriaDTO` / `ResumenHistoriaDTO` between service and controller/view/adapters; the state record is internal to model + the binary adapter (it is converted to plain values, see data-model). |

### Process Gate

| Item | Status | Notes |
|---|---|---|
| `spec.md` committed before code | PASS | Commit `0b0663a`. |
| Every task cites its FR; every scenario has a test citing its FR | To check in `/speckit-tasks` and `/speckit-analyze` | |

## Project Structure

### Documentation (this feature)

```text
specs/005-timeline/
├── plan.md              # This file
├── research.md          # Phase 0: decisions R1–R12 with alternatives and evidence plan
├── data-model.md        # Phase 1: entities, fields, invariants, state transitions
├── quickstart.md        # Phase 1: runnable validation scenarios
├── bench-antes.txt      # "Before" baseline (bench_historial + bench_guardado), saved before any code change
├── contracts/
│   ├── comando-historia.md
│   ├── cli-replay-hasta-checkpoint.md
│   ├── dto-historia.md
│   ├── formato-guardado-v2.md
│   └── reporte-bench-linea-tiempo.md
└── tasks.md             # Phase 2 (/speckit-tasks, not created here)
```

### Source Code (repository root)

```text
structures/
└── linea_tiempo.py            # NEW  LineaTiempo: action vectors, checkpoint slots, ledger of skipped effects,
                               #      ultimo_menor_o_igual (binary search), recortar (trim from the end)
model/
├── registro_estado.py         # NEW  capturar(partida) / restaurar(registro, mundo): state record
├── efectos_omitidos.py        # NEW  EfectoOmitido (ledger entry) + aplicar(entrada, mundo)
├── reproduccion_logica.py     # NEW  Reproductor: scratch world + forward re-simulation + stop rule
├── linea_tiempo_logica.py     # NEW  LineaTiempoPartida: iniciar, registrar_accion, tras_retroceso
│                              #      (retags the ledger), anotar_poblacion,
│                              #      K_POR_DEFECTO (provisional 50; fixed by T068)
└── partida_logica.py          # EDIT avanzar_hasta_jugador(limite=None) stop bound; Partida.desde_registro;
                               #      `diario_omitidos` appended at the exempt points (scroll on floor,
                               #      scroll picked up / dropped / consumed)
data/
├── fabrica_modelo.py          # EDIT observer hook on _ficha (feeds the frozen ficha store);
│                              #      poblar_sala returns the instance counter it started from
│                              #      (or none if already populated)
├── fabrica_reproduccion.py    # NEW  populate rooms in the scratch world from stored contents and
│                              #      frozen fichas only (raises instead of asking the network)
└── repositorio_cripta.py      # EDIT pure skeleton builder (no write to repo.salas)
service/
├── juego_service.py           # EDIT record hooks after each successful action; scroll → tras_retroceso;
│                              #      historia_por_instante / historia_por_accion
└── historia_service.py        # NEW  builds ResumenHistoriaDTO from a scratch partida (read-only)
dto/
└── resumen_historia_dto.py    # NEW  ResumenHistoriaDTO, RespuestaHistoriaDTO
controller/
└── controlador.py             # EDIT "historia" command; excluded from comandos and from the log
adapters/
├── guardado_binario.py        # EDIT version 2 (header gains K), version check before header read
├── formato_historia.py        # NEW  pure text formatter shared by the view and the replay output
└── salida_replay.py           # EDIT imprimir_historia(dto), imprimir_termino_antes(...)
view/
└── vista_consola.py           # EDIT mostrar_historia(dto) (calls the shared formatter)
aplicacion.py                  # EDIT --checkpoint-cada wiring, K on load (saved K wins + notice),
                               #      reproducir(lector, hasta)
main.py                        # EDIT --checkpoint-cada K, --hasta T, bench registration
bench/
├── juego_sintetico.py         # NEW  deterministic-by-seed game generator (world + action mix + scrolls)
├── bench_linea_tiempo.py      # NEW  memory + query time for K = 10, 50, 200 and no-checkpoint
└── bench_historial.py         # EDIT same scenarios with the timeline active, next to part-one values
tests/
└── test_linea_tiempo_*.py     # NEW  one test per acceptance scenario, each citing its FR
```

**Structure Decision**: the existing five layers. The timeline structure is in `structures/`, the
rules about *what a state is* and *how to re-simulate* in `model/`, the question "what does the
player see" in `service/` (DTO out), the command in `controller/`, the text in `adapters/` + `view/`.
Recording hooks are in `JuegoService` because it is the only place that knows the resolved target of
an action (the object under the inventory cursor, the enemy chosen by default) and it is used by the
game, by `--replay` and by load alike, so a replayed or loaded game builds the same timeline.

## Data Structures and Complexity

Notation: A = surviving player actions, K = checkpoint spacing, R = rooms, S = size of the mutable
state (touched rooms + entities + agenda), c = cost of one player action (measured: 84 µs to 3.2 ms in
`bench-antes.txt`, "acción" column), r = actions reverted by one scroll.

| Operation | Cost | Notes |
|---|---|---|
| record an action | O(1) amortized | append to three parallel vectors |
| take a checkpoint | O(S) every K actions | capture only touched rooms; the random state is an `array('I')` of 625 words |
| checkpoint for boundary b | O(1) | slot `b // K` |
| action for instant t | O(log A) | own binary search over the clock vector |
| scroll trim | O(r + checkpoints dropped + ledger entries retagged) | `del vector[n:]` on each vector; the ledger entries retagged are those of the reverted window and of earlier scrolls above n; independent of A (FR-011) |
| apply ledger in a query | O(entries with the tag being crossed) | only entries tagged with a boundary the re-simulation crosses |
| query | O(R + E) scratch graph + O(S) restore + ≤ K·c re-simulation | FR-020: at most K player actions applied |
| memory | A·(action record) + (A/K)·S + ledger (the last 5 actions' skipped effects + those kept by scroll reads) | FR-021: never A·S; at most one checkpoint every K actions (FR-019) |

Why the scratch graph is O(R + E) per query, and what is done if the measurement says it is too
much, is in R5.

## Default K

**Status: provisional K = 50, pending measurement (T068).** Rule fixed now so the choice is not made after seeing the numbers:
the default K is the **largest** K in the measured set (10, 50, 200, plus any added value) whose
p99 on the reference world is ≤ 25 ms (half the FR-024 limit, to leave room for slower machines);
the memory of every measured K is reported next to it, not used to choose. If no K meets the
p99 condition, the group decides with the table in front of it. The chosen value, the table and the date are
copied here by task T068 and into `docs/DECISIONES.md` §5.6.

## Decisions on the points for the spec

Taken by the group on 2026-11-18. After the analysis, `spec.md` states decision 1 explicitly (FR-001 and scenario US1-9); nothing else in it changed.

1. **Instant with a player decision (FR-001, FR-009): "the decision wins"**, as the second sentence of
   assignment 3.6 says. When the agenda hands the turn to the player at instant t, the state at t is
   the state just before the decision; events of that instant that come later in agenda order
   `(tiempo, num_sec)` are not shown. The Appendix B case "several events at the same instant" is
   tested with an instant that has **no** player decision (research R7, R12).
2. **Scroll: no extra checkpoint (FR-019).** At the rewind point the plan records the effects the undo
   deliberately skips and applies them when a re-simulation passes that point (research R6, data
   model "EfectoOmitido"). The effects found in part one's code are listed in R6, including two the
   first draft of this plan had missed (rooms populated by reverted moves; scroll objects moved by
   reverted actions).
3. **Checkpoints are not stored in the save file.** The v2 file stores the commands and the K in use;
   load re-executes the commands and rebuilds the timeline (research R9). No `bench_guardado`
   comparison of both designs.

Still informational, no decision asked: the action record stores the *resolved* action instead of the
raw log line (research R3), because the log line alone cannot be repeated (inventory cursor, default
targets).

## Complexity Tracking

No constitution violation. Nothing to justify.
