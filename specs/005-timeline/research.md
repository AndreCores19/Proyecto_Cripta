# Research: Timeline

Each entry: **Decision**, **Rationale**, **Alternatives considered**, and **Evidence** (what is already
measured in `bench-antes.txt`, and what `--bench` must still measure; no claim without a number,
constitution VI). Numbers marked *to measure* were not known when this was written; the ones measured
since are noted in place (*Measured afterwards*, R1 and R5).

## R1 — Forward re-simulation from checkpoints vs backward inversion with the part-one history

**Decision.** Rebuild a past state by copying nothing from the live game: take the checkpoint at or
before the target and re-simulate forward (≤ K player actions).

**Rationale.**

- The part-one `Historial` (`structures/historial.py`) stores **closures** in a ring of 5 frames. To
  invert backwards over A actions it would have to keep A frames. The baseline shows how many
  closures one action leaves: 240 closures in 5 frames (48/action) for 10 enemies, 2 040 (408/action)
  for 100 enemies and 6 040 (1 208/action) for 300 enemies. For 5 000 actions in the "extremo"
  scenario that is about 6 million closures; a Python closure with its cell is on the order of
  100–200 bytes, so about 1 GB (*to measure* with `tracemalloc`). It grows with actions × activity,
  which is what FR-021 forbids.
  *Measured afterwards (T066/T068):* on `referencia` one action leaves 83.0 closures in `Historial`,
  extrapolated to 178 115 KB at 5 000 actions; that figure is the shallow `sys.getsizeof` size of the
  closures and their cells, not a `tracemalloc` total. Re-simulating forward costs 635.7 µs per action and
  inverting backward 157.9 µs. Numbers: `specs/005-timeline/bench-linea-tiempo.txt` ("Forward vs
  backward") and `docs/DECISIONES.md` §5.6.2.
- Closures cannot be written to the save file (FR-017) and cannot be dropped from the middle; a
  scroll must trim from the end (FR-011) and the part-one history already does so by popping frames.
- Inversion depends on a *perfect* inverse for every mutation; the undo of part one is deliberately
  incomplete for scroll objects (§2.11), so inverting thousands of actions would accumulate that gap.
  Forward re-simulation uses the real rules, so it cannot disagree with the game by construction.

**Alternatives considered.**

1. *Backward inversion with `Historial` extended to A frames.* Rejected for memory and persistence
   as above. Kept as a **measured** comparison in `--bench` (section "adelante vs atrás"): cost per
   action of re-simulating forward (≈ the "acción" column) vs inverting (≈ the "deshacer" column),
   from `bench_historial` under the new load. The baseline already shows the two are of the same
   order (84 vs 56 µs, 865 vs 609 µs, 3 159 vs 2 328 µs), so **time does not separate them; memory
   and persistence do** — the report must say so with its own numbers, not with these.
2. *A full copy at every action.* Forbidden by FR-021; the baseline column "copiar todo" is 0.6 ms
   to 12.7 ms per copy, which times 5 000 actions is seconds and gigabytes.
3. *Checkpoint + inversion backward from the next checkpoint.* Halves the average distance but needs
   both mechanisms; rejected as more code for the same K bound.

**Evidence still to produce.** `bench_linea_tiempo`: bytes per action record, bytes per checkpoint,
cost per re-simulated action, closures per action in `Historial` extended to 5 000 frames (one
synthetic measurement, not a design).

## R2 — What a checkpoint is: a hand-written state record, not a copy

**Decision.** `model/registro_estado.py` has `capturar(partida) -> RegistroEstado` and
`restaurar(registro, mundo) -> Partida`. The record holds **only mutable fields**, referring to
entities by stable ids:

- partida: clock, agenda sequence number, random state, actions taken, enemies defeated, ended /
  victory flags, exit door opened, scroll reads counter, decisor mode, instance counter of the factory;
- player: room id, life, speed, equipped items, effects, inventory in order with the cursor;
- active enemies: id, room id, life, speed, effects, event;
- per touched room: knowledge level, trace time, floor objects, inactive enemies, traps (armed, event),
  per exit: `cerrada`, `memoria`;
- the discovery order of known rooms (`conocidas`);
- the agenda events (time, sequence number, type, owner reference, data reference).

Untouched rooms are not stored: they are the skeleton.

**Rationale.**

- `copy` is allowed only in benchmarks (constitution, technology stack). `copy.deepcopy(partida)`
  would also be wrong, not only forbidden: `Partida.historial` holds lambdas (deepcopy keeps
  functions by reference, so a copied game would undo the *live* game), `creador_objetos` is a bound
  method of the factory (the copy would drag the catalog, the cache and the HTTP client), and the
  room graph is shared with the repository.
- The record is plain ints, strings and lists, so the ledger of skipped effects (R6) and the tests can compare it with no object graph.
- The `random.Random` state is a 625-word tuple of ints; kept as `array('I')` it is 2.5 KB instead of
  about 22 KB of Python int objects, which matters at K = 10 (500 checkpoints per 5 000 actions).
  *To measure:* bytes per checkpoint with tuple vs `array`.

**Alternatives considered.** `deepcopy` (above); `pickle` of the world (same graph problem, and
writes executable-by-default data into a save file); a copy of the room graph written by hand with
an identity map (needs an id → copy index, which would be a `dict` in disguise, or a second sorted
vector — the record with ids is the same work and is also serializable).

## R3 — The action record: resolved, not raw

**Decision.** `AccionGrabada(numero, reloj, tipo, argumento)` with `tipo` in
{`mover`, `esperar`, `atacar`, `recoger`, `soltar`, `equipar`, `usar`, `abrir`} and `argumento` the
direction, the enemy id, or the object instance id (none for `esperar`). `reloj` is the clock **at the
decision**, before the action. It is written by `JuegoService` right after a successful action,
using the same values it already resolved.

**Rationale.** The log line `usar` or `atacar` (no argument) depends on the inventory cursor and on
who is in the room; `sig`/`ant` move the cursor but are not actions. Re-simulating from the raw
lines would require replaying every cursor command in between. A resolved action is
self-contained and has the same information the log has after resolution. `ir a` already produces
one `mover` per step, so it needs nothing special. A failed command (wall, no key, full inventory) is
not an action and is not recorded (assumption: a player action is a command that changes the game
and takes time; the test is "`acciones_jugador` went up by one").

**Alternatives considered.** Store the raw lines since the previous action (faithful to "the same
data as the log", but needs the cursor commands and ignores state-dependent defaults; larger).

## R4 — Finding things without `dict`, `bisect` or a linear walk

**Decision.**

- Checkpoint for boundary b (actions already taken): slot `b // K`, O(1). Boundary b is the state
  "just before action b+1"; so "historia #k" uses b = k−1. (The brief's `k // K` is this index with
  `k` counting actions already taken.)
- Action for instant t: `LineaTiempo.ultimo_menor_o_igual(t)` over the clock vector, our own
  iterative binary search, O(log A): the last decision number whose clock is ≤ t. Clocks are
  strictly increasing: a player's interval is at least 1 (`tiempo_logica.intervalo`).

**Rationale.** FR-022. The clock vector is a plain list of ints, so the search is a dozen lines and
carries a comparison counter like `VectorBusqueda`, so the bench can show O(log A) with counts.

## R5 — The scratch world and its cost

**Decision.** `Reproductor` builds, per query, a fresh room graph from the crypt skeleton (a pure
builder extracted from `RepositorioCripta.construir_salas`, which today also writes `repo.salas`),
creates a `Partida` from the record (`Partida.desde_registro`, no constructor side effects: no
event scheduled, no room entered), and re-simulates with the real `Partida` methods.

**Rationale.** It is the only way for a query to be guaranteed not to touch the live game. Cost
per query is O(R + E) for the graph. For cripta-06 (300 rooms) this is *to measure*; if it exceeds
a third of the budget, the fallback (not the plan) is a pooled scratch graph reset only on the rooms
the previous query touched. The bench reports graph-build time separately so the choice is made from
numbers.

*Measured afterwards (T068):* building the graph was 50.9 % of a K = 10 query on `referencia` (p99
23.88 ms), more than a third, so the fallback was adopted: `data/grafo_reutilizable.py` keeps one scratch
graph per service and resets it between queries (graph share 6.3 %, p99 16.54 ms). The final reset does
not track which rooms the previous query touched: it restores the changeable fields of **every** room
(knowledge, trail, floor objects, inactive enemies, traps, search marks) and exit (closed, memory), still
O(R + E) but only assignments, and moves `Salida.epoca_puertas` once as a fresh build did. Numbers and
reasoning: `plan.md` ("Default K"), `docs/DECISIONES.md` §5.5.1, `specs/005-timeline/bench-linea-tiempo.txt`;
equivalence with a fresh graph: `tests/test_grafo_reutilizable.py`.

**Side effects checked and accepted.**

- `Salida.epoca_puertas` and the search stamp counter are class-level and monotonic; a scratch world
  only makes the live hunters' cached search recompute (same result, a little time). Test: hunter
  decisions in a game with queries equal those in a game without (SC-011).
- The scratch `Bitacora` (message buffer) is empty and is not shown; FR-004 does not require it.
- `DecisorCazador` is created with the saved mode; its cache is derived data, so a fresh one gives
  the same decisions (spec 002 equivalence tests are the oracle).

## R6 — Scroll: trim from the end and keep the effects the undo skips

**Decision.** After a scroll read, `LineaTiempoPartida.tras_retroceso(partida)` sets n =
`acciones_jugador` (already reverted by the history) and:

1. deletes action records with number > n and checkpoints with boundary > n, from the end only,
   O(r + dropped). A checkpoint with boundary <= n is kept untouched. **No checkpoint is taken or
   replaced** (assignment: at most one every K player actions; FR-019 stays literal);
2. retags the **ledger of skipped effects** (below): every entry of the reverted window, and every
   entry kept by an earlier scroll whose tag is > n, gets tag n and is marked "re-apply";
3. appends one entry `contador(value)` with the factory's instance counter as it is now.

A query applies ledger entries tagged b, in order, when its scratch world is **at the decision point with b
actions taken** (the state just before action b+1): right after loading a checkpoint of boundary b, or after
replaying action b and running the events up to the player's turn. An instant t with `c_b ≤ t < c_{b+1}` stops
before that point and does not see them: the skipped effects happened at or after the turn, not right after
action b. Entries tagged below the checkpoint's boundary are never applied (that checkpoint was captured later and
already contains them). A checkpoint of boundary b taken before the scroll is never refreshed, so entries tagged b
are applied on top of it.

**What the undo skips - the full list found by reading part one** (`partida_logica.py`,
`inventario_logica.py`, `efectos_logica.py`, `fabrica_modelo.py`, `juego_service.py`). Each one is
either a ledger entry or shown not to matter:

| # | Skipped by the undo | Where | Ledger entry |
|---|---|---|---|
| 1 | Scroll consumed after it is read | `Partida.usar_pergamino`: `inv.quitar_nodo` runs after the frame is closed | `inv_quitar(id_instancia)` |
| 2 | Scroll taken from / put on the floor | `_quitar_del_suelo`, `_poner_en_suelo` (§2.11) | `suelo_quitar(id_sala, id)` / `suelo_poner(id_sala, objeto)` |
| 3 | Scroll added to / removed from the inventory by `recoger` / `soltar` | `Inventario._grabar` does not register scroll objects | `inv_agregar(objeto)` / `inv_quitar(id)` |
| 4 | Factory instance counter (`siguiente_instancia`) | not part of any frame; loot of reverted kills and populated rooms advance it | `contador(value)`; and each `poblar` below carries its starting value |
| 5 | **Rooms populated by reverted moves** (found while checking the list) | `JuegoService.mover` calls `FabricaModelo.poblar_sala` *before* `Partida.mover` opens a frame; the lists it fills (`objetos`, `inactivos`, `trampas`) and `pobladas` are never undone | `poblar(id_sala, contador_inicial)` |
| 6 | Scroll objects created by that population | same as 5 | included in `poblar` (same ids, because the counter starts where it started) |
| 7 | `retrocesos` counter | "fuera del historial a propósito" | not needed: only the travel command reads it, and re-simulation never travels |
| 8 | Message buffer (`Bitacora`), the hunter's search cache, `Salida.epoca_puertas`, search stamps | not undone, derived or only cosmetic | not needed: not in FR-004, and the cache gives the same decision (R5) |
| 9 | Inventory cursor (`sig`/`ant`) | not an action, not recorded | not needed: actions record the resolved target (R3); the cursor is not in FR-004 (the oracle compares summaries without it) |
| 10 | `terminada` / `victoria` | assigned without the history | not needed: `retroceder` is refused once the game has ended |

If task work finds an eleventh, it is added to this table and to the ledger before the task is
closed; the oracle test (R12) is what would show it.

**Where a scroll read is detected.** `JuegoService` compares `partida.retrocesos` before and after **every**
service call that can read a scroll (`retroceder`, and `usar_objeto` when the object under the cursor is a
scroll, because `Partida.usar` hands it to `usar_pergamino`); if it changed, a scroll was read and
`tras_retroceso` runs, and the call is **not** recorded as an action (`acciones_jugador` went down, not up).

**Where entries come from.** `Partida.diario_omitidos` (a list, `None` when no timeline is active) is
appended at the exempt points of rows 1-3 (all inside `Partida`, no change to `Inventario`).
`JuegoService.mover` calls `LineaTiempoPartida.anotar_poblacion(id_sala, contador_inicial)` when
`poblar_sala` actually populated a room. Each entry is tagged with the number of the action in
progress. Entries that are not marked "re-apply" and are older than the history capacity (5 actions)
are dropped after each recorded action: a scroll can only revert inside that window, and the actions
that survive are replayed by the re-simulation itself, so re-applying their entries would duplicate
them. What stays forever is only what a scroll kept, so the ledger is bounded by the scroll reads in
the game.

**Consecutive scrolls.** The ledger is chronological. A second scroll to boundary n2 < n retags the
entries above n2 (earlier-kept ones first, then the new window), so order of occurrence is preserved.

**Rationale.** The alternative that takes a fresh checkpoint at the rewind point is exact by
construction but adds a copy off the K grid, which the assignment does not allow. The ledger keeps
the grid and keeps FR-020: the re-simulation distance is unchanged.

**Residual risk, stated.** Position inside a floor list (`lista_quitar` undo inserts by index) can
differ from the live order when an unrecorded scroll operation shifted that list. Floor contents are
not in FR-004 and `recoger` addresses objects by id, so it does not change an answer; the oracle
compares inventory order, which the ledger preserves (`inv_agregar` appends at the tail, as
`Inventario.agregar` does).

**Alternatives considered.** *Extra checkpoint at the rewind point* (the first draft): rejected by
the group because of FR-019. *Making the part-one undo cover scroll objects*: changes part-one
behavior, forbidden by FR-012.

## R7 — Stop rule for "historia t" (FR-001, FR-009)

**Decision.** Let `c_k` be the clock of decision k (k = 1 … n+1; decision n+1 is the pending one, or
absent if the game ended). For t: k = last decision with `c_k ≤ t`.

- If `c_k == t`: the answer is the state just before action k: checkpoint of boundary k−1, then
  re-play actions up to k−1. Events of instant t that come after the player's decision in agenda
  order `(tiempo, num_sec)` are **not** executed (the decision wins; plan, "Decisions on the points for the spec" 1).
- If `c_k < t`: play action k and then run agenda events while the next event has `tiempo ≤ t` (all
  events at t are executed, any sequence number), then stop.

`Partida.avanzar_hasta_jugador(limite=None)` gets the bound: before extracting, it looks at
`agenda.proximo()` and stops if its time is greater than `limite`. The reported clock is `t` (or
`c_k` for `#k`). Ties inside the agenda are the agenda's own `(tiempo, num_sec)` order, already a
fixed rule.

At most K actions are applied: from boundary `s·K` to boundary ≤ `s·K + K − 1`, plus action k
itself.

The Appendix B case "several events at the same instant" is tested at an instant that has **no**
player decision (a decision at that instant would make the decision-wins rule apply, which is a
different case, tested separately). Player decisions are never two at one instant (the interval is at
least 1), so no test needs two decisions at t.

## R8 — Re-simulation never touches the network

**Decision.** The scratch world populates a room (a move into a room the checkpoint has not
populated) through `data/fabrica_reproduccion.py`, which reads the contents already stored in
`repo_cripta.contenidos` and the fichas from a **frozen ficha store** (a `VectorBusqueda` by id) fed
by a one-line observer in `FabricaModelo._ficha` whenever the live factory resolves a ficha. A
missing ficha raises `ErrorReproduccion`; it never calls `repo_catalogo.resolver`. Loot creation in
the scratch world uses the same store and the instance counter from the record.

**Rationale.** The catalog cache is an LRU of 25 fichas by default, so a ficha seen 3 000 actions
ago may have been evicted; going back to the disk store or the service would break FR-006/V.
**Test:** a client that raises on any call, a budget counter that must not move, and `partida.log`
compared byte for byte. After a load the store is refilled by the same re-execution that rebuilds
the live game.

## R9 — Save format v2: commands and K, nothing else

**Decision.** `VERSION_FORMATO = 2`. The only change to the layout is that the fixed header gains
**K** (u32). The file still stores the seed, the room contents, the commands and the room index. The
timeline is **not** stored: load re-executes the commands, exactly as part one does, and that
rebuilds the live game, the undo history, the action vectors, the checkpoints and the ledger of
skipped effects (recording is on during load). Details in
[contracts/formato-guardado-v2.md](./contracts/formato-guardado-v2.md).

- `leer_cabecera` first reads magic and version (6 bytes) and compares the version, then reads the
  rest of the header according to the version. A v1 file therefore always yields the existing
  incompatibility message, also when it is shorter than the v2 header; empty or truncated files give
  "truncado", a non-save file "No es un archivo de guardado de Cripta" (FR-018, existing mechanism).
- Nothing is loaded, no file is modified, the running game is untouched: `validar_guardado` already
  runs before any state changes.
- Every `historia` answer after a load equals the answer before the save because the same commands
  run through the same code (determinism, constitution II); the save-and-load test compares them
  (SC-005), including a game saved after a scroll.
- The saved K wins; an explicit `--checkpoint-cada` that differs gets the notice. The option's
  default is "absent", so the notice appears only when the player typed a different value.

**Rationale (the group's decision).** The timeline is a function of the commands, so storing it
would duplicate what load already recomputes, and would need a codec for the state record. FR-017's
requirement ("loading restores it, every query gives the same answer") is met by re-execution.

**Alternatives considered.** *Store the action table and the checkpoints in the file*: rejected by
the group (decision 3). *Load from the last checkpoint and re-simulate the tail instead of
re-executing everything*: faster, but the undo history after load would hold only the tail, changing
part-one behavior (FR-012); rejected.

**Consequence to measure.** Load re-executes N commands with recording on, so load time includes the
recording cost; it is visible in `bench_historial` (action cost with and without the timeline). No
separate comparison is made.

## R10 — Query path, DTOs and the views

**Decision.** `JuegoService.historia_por_instante(t)` / `historia_por_accion(k)` return a
`RespuestaHistoriaDTO` (accepted or reason, `ResumenHistoriaDTO`, flag "ended earlier"). The summary
is built by `service/historia_service.py` from the scratch partida with read-only code that reuses
`mapa_vista`/`estado_vista` logic (factored so both services share it). Text is produced by one pure
function, `adapters/formato_historia.py`, used by `VistaConsola.mostrar_historia` and by
`salida_replay.imprimir_historia`, so FR-014 (same summary in the game and in `--replay`) holds by
construction and a test compares both outputs.

`--replay ... --hasta T`: replays commands through the same `Controlador` with no view, stops once
the clock is ≥ T or the commands end, then answers T from the timeline; T greater than the final
clock prints the final state and the "ended earlier" notice (FR-015). The replay already needs the
catalog and the budget exactly as before; the query itself adds nothing.

The command is excluded from `Controlador.comandos` and from `partida.log` *before* dispatch
(today every command except `salir/guardar/cargar/ir` is appended first), so a rejected query is not
logged either (FR-007).

## R11 — Measurement plan (FR-024, FR-025, FR-026, FR-027)

1. **Before** (done): `bench-antes.txt` with `bench_historial` and `bench_guardado`, Python 3.14.6,
   before any code change.
2. **Synthetic game** (`bench/juego_sintetico.py`): given world, seed and length, produces the same
   command sequence every time: moves chosen with a seeded generator among open exits, waits,
   attacks when an enemy is in the room, pick-ups/drops when objects exist, and a few scroll reads
   (so trimming and the ledger of skipped effects are in the measured games, including a scroll read right after a move into a new room). Worlds: *referencia* (cripta-06
   skeleton from the offline pack + 30 hunters, as in spec 002), *grande* (100 rooms, 100 enemies),
   *extremo* (100 rooms, 300 enemies, information only). ≥ 5 000 player actions each.
3. **Query set** (spec clarification): instants spread over the whole game by seed, including the
   oldest and the most recent; p99 by the same convention as `bench_ciclo` (`ordenados[int(n·0.99)]`);
   mean and worst reported.
4. **K** = 10, 50, 200 and the **no-checkpoint** alternative (only checkpoint 0; re-simulate from the
   start). Per row: checkpoint memory, action-record memory, query p99 / mean / worst, graph-build
   share of the query, maximum actions re-simulated (must be ≤ K; "no-checkpoint" shows the whole game).
   Memory with `tracemalloc` on the timeline alone, game excluded.
5. **Linearity** (SC-007): the same seed at A and 2A actions; memory must grow ~2× at fixed K, not
   with A·S.
6. **Part-one under the new load** (FR-027, §5.6): `bench_historial` scenarios run twice, without and
   with the timeline active, printed side by side: action, undo, closures kept; the "copiar todo"
   column is replaced by "capturar checkpoint".
7. **Forward vs backward** (R1): cost per action of each and closures per action.
8. **Save** (`bench_guardado`): rerun unchanged after the v2 change and compared with
   `bench-antes.txt` only to show that the 4-byte header addition changed nothing. There is no
   timeline section to measure.
9. Every table is copied into `docs/DECISIONES.md` with the date and machine, and the default K is
   derived from it by the rule in `plan.md` ("Default K").

## R12 — Testing oracle

The oracle is the game itself: a test plays a seeded game and records the live summary at every
decision; afterwards every instant and every `#k` is queried and compared (SC-002). It runs for K = 1,
3, 7 and larger than the game (edge cases), with hunters, effects (poison, speed), traps, doors with
automatic closing, deaths, and with scroll reads (SC-004), a scroll read right after entering a room for the first time, a scroll
reverting a pick-up or drop of a scroll, consecutive scrolls, a save/load in the
middle (SC-005), and queries interleaved (SC-003, SC-011: final state, log bytes and undo allowance
identical with and without queries).

Specific tests for the ledger (R6): one per row 1-6 of the table (consumed scroll; scroll picked up
and dropped by reverted actions; counter after reverted loot; room populated by a reverted move and
re-entered later), plus "a checkpoint of boundary n kept by the trim and a query that starts from it",
and a test that fails if a checkpoint is ever taken off the K grid (`len(puntos) <= floor(A/K) + 1`).
