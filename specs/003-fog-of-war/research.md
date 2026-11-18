# Research: Fog of War and Automatic Travel

Each entry: decision, rationale, alternatives considered. No open `NEEDS CLARIFICATION`; the five
points that need the spec are in `plan.md` ("Points for the spec").

## R1. Where the player's knowledge lives

**Decision**: Two integer fields on objects the model already owns (`Sala.conocimiento`,
`Salida.memoria`) plus a list of discovered rooms in `Partida`. All writes go through `Historial`.

**Rationale**: Rollback (FR-013) and timeline (FR-014) then come for free: the history already
restores every recorded write, in the same frame as the move that caused it. Reading a room's state
is O(1). The same pattern already holds `rastro` and the hunter's stamp fields. No `dict`/`set`
(Constitution I). The discovery list gives the known map in O(known rooms) without scanning the
crypt.

**Alternatives**: (a) A separate knowledge object keyed by room id: needs an index by id (a `dict`,
forbidden) or a search; and its own undo code. (b) Snapshotting knowledge before each action: copies
O(known rooms) per move, wasteful. (c) Recomputing knowledge from the log on demand: O(history) per
read.

## R2. The route search

**Decision**: Dijkstra **backwards from the destination** over incoming exits, restricted to
explored rooms and to exits remembered open, stopped when the player's room is extracted.

**Rationale**: Same shape as the hunter search (spec 002 R2), so the tie-break rule of FR-018 is the
same code path in spirit: `s.costo + dist(s.destino) == d`, lowest `(destino.id, direccion)`.
Searching from the destination makes the distance of **every neighbor of the player's room** available
at once. Costs are at least 1, so every neighbor on a cheapest route has a strictly smaller
distance and is final when the player's room comes out. A forward search would have to remember the
first step of each route and break ties by comparing routes. Stamps in the room fields avoid clearing
anything between searches (no `set`).

**Alternatives**: (a) Forward Dijkstra with the first step carried along: ties between equal-cost
routes need a comparison rule per queue entry; more state, same cost. (b) BFS: wrong, costs differ.
(c) Reusing `Busqueda.calcular` with a filter flag: adds a branch to the hot path of the hunters for
the sake of this feature; rejected, a separate class is a few lines.

## R3. Continuous door observation without a hook

**Decision**: The remembered state of a door that touches the player's room is **derived** from its
real state; it is stored only when the player leaves the room.

**Rationale**: Q2 says the map holds the real state while the player is in either room. Writing the
memory on every door change would need a hook in `_poner_cerrada` and in rollback. Deriving needs
none: a door touching the player's room reads live, and the player can only stop touching a room by
moving, which is a single place (`mover`) where the memory is written. Rollback restores the real
state, the player's room and the memory through the history, so the derived value is consistent
afterwards. Q1 falls out of the same rule: a torch-explored neighbor is not the player's room, so its
other doors stay `NO_OBSERVADA` until the player is in one of the two rooms each connects; only the
door joining the player's room to that neighbor is observed, because it touches the player's room.

**Alternatives**: (a) Hook on every door change that checks the player's room: more code and one more
place that must be kept in step with rollback. (b) Store on entering, ignore changes while inside:
contradicts Q2.

## R4. Where the trip lives

**Decision**: A `Viaje` object in the model with one `paso()` per step, driven by
`JuegoService.ir_a`, which passes in the service's own move function.

**Rationale**: A step must be exactly an ordinary move (FR-019), including the room-content download
that only the service performs (Constitution V, `poblar_sala`). Passing the move function keeps the
model free of the service and means a test can drive the trip one step at a time and read the scroll
between steps (acceptance scenarios 6 and US8). Stop checks after the step read only game state: life
before and after (covers trap, enemy attack and poison pulses that ran in the event cycle of that
step), alive enemies in the player's room (activated ones included, since entering already activates
the sleeping ones), game ended, player in the destination.

**Alternatives**: (a) The loop in the controller: puts game rules in the controller (Constitution
III). (b) One step per controller iteration with a persistent "trip in progress" flag: needs state
that must not survive a save, a rollback or a failed step, for no benefit in a synchronous console.

## R5. Log, saved games and replay

**Decision**: A trip writes a comment line for the order and one plain move line per step. The saved
command list stores the moves only. The log reader skips lines beginning with `#`.

**Rationale**: Saved games and logs are replayed by feeding their lines to `Controlador.ejecutar`
(`_reejecutar`, `reproducir`). If the order were stored too, the steps would run twice. Replaying
plain moves reproduces the trip exactly, because each step is the same move the service performs. The
format version stays 1: old logs have no comment lines, and an old reader fed a new log only prints
"Comando no reconocido" for the comment lines without touching state. Knowledge needs no storage of
its own, since it is a function of the replayed moves (FR-012).

**Alternatives**: (a) Bump the log version: breaks old logs for no gain. (b) Store the order and skip
the steps on replay: needs the trip to be deterministic across versions of the route code.

## R6. Keeping the hunters' cached search valid

**Decision**: Rule A of the spec 002 plan: the "ir a" search takes its stamp from
`Busqueda.nueva_estampa()` and writes the existing `busq_marca` / `busq_dist` fields.

**Rationale**: The spec 002 plan said a second search over the same room fields must either share the
stamp counter (so the shared hunter cache sees `ultima_estampa` change and recomputes) or use its own
fields. Rule A costs one extra hunter search after each "ir a" step, and only while hunters are
active. Rule B would add two integer fields per room for no better result. A test runs a trip step
between two hunter turns and checks the hunter decision against the oracle (FR-011 of spec 002).

**Alternatives**: Rule B (own fields): kept as the fallback if the baseline shows the extra hunter
search costing more than the 10% trigger.

## R7. What "the full known map of the reference crypt" is for the benchmark

**Decision**: Spec 002 (clarification of 2026-11-10) defines the reference crypt as the one the course
publishes and, until then, a seeded synthetic crypt of the size of the largest scenario of the existing
event-cycle benchmark (100 rooms). The largest published crypt (cripta-06) has 300 rooms, so the verdict of
`bench_ir_a` is measured with a seeded synthetic crypt of **300 rooms**, fully explored with every door
remembered open; 100, 500 and 1000 rooms are reported for information. Spec 002 is not edited; this is the
size this feature measures with. If the course publishes a different reference crypt, the measurement is
repeated with it and prevails.

## R8. Display order of the known map

**Decision**: The list of discovered rooms is copied and sorted by room id with the project's own
`ordenar` (`structures/ordenamientos.py`) when the map is shown.

**Rationale**: The command is rare and the list small; sorting at display time keeps the hot path
(each move) free of ordered insertion. The order is by id, never by insertion or iteration order
(Constitution II).
