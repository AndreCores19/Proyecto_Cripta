# Feature Specification: Hunter Enemy

**Feature Branch**: `002-hunter-enemy`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Hunter enemy. A new enemy behavior, "hunter" ("comportamiento": "cazador" in the catalog), whose catalog entry includes a "rango" field (an integer in cost units). On its turn, a hunter applies these rules in order: 1. If it shares a room with the player, it attacks (same attack rule as part one). 2. Otherwise, it considers d, the minimum total cost to reach the player's current room, summing the cost of each exit traversed and using only exits that are open at that moment. 3. If no route exists, or d > rango, it waits (cost 100). 4. Otherwise, it moves one step along a route of cost d. The cost of that action is the cost of the exit it traverses. The hunter's movement takes time with the same rule as any other actor (spec 001): interval = max(1, exit_cost * 100 // speed). Tie-break: let u be the hunter's room. Among neighbors v where cost(u, v) + dist(v, player) = d, the hunter moves to the one with the lowest id. Knowledge: the hunter knows the full map skeleton and the current state of every door. It is not affected by the player's fog of war, and it never opens closed doors. Its decision depends only on the skeleton (downloaded in full at start, including exit costs) and the current state of the doors; never on whether a room's content has been downloaded. Observable equivalence: the hunter's decision each turn must be identical to computing the route from scratch at that moment, even if doors open or close, the player moves, or other actors die between turns. Wanderers and trackers keep their part-one behavior."

## Clarifications

### Session 2026-11-10

- Q: Does a hunter that has not been activated yet (part-one activation rule) chase the player or stay inactive? → A: It stays inactive: it does nothing until the part-one activation rule activates it (the player enters its room); from then on FR-002 to FR-005 apply.
- Q: What happens if a catalog entry has `"comportamiento": "cazador"` but no `rango`? → A: It is treated as `rango` 0: the hunter only attacks when it shares a room with the player and otherwise waits. No new invalid-data rule is added (same precedent as `costo` in spec 001).
- Q: Which crypt is the "reference crypt" of FR-017, since the course will publish it later? → A: The one the course publishes. Until it exists, a synthetic crypt, deterministic by seed, of the size of the largest scenario of the existing event-cycle benchmark. When the official crypt is published, the measurement is repeated with it and that measurement prevails.
- Q: Does FR-019 need the split between frequently changing and almost never changing doors for every comparison, or only for reusing vs always recomputing? → A: For two comparisons: reusing earlier computations vs always computing from scratch, and one computation per hunter vs one computation shared by all hunters. The other two (one hunter vs many; small `rango` vs large `rango`) are measured in a single fixed door scenario in which doors almost never change.
- Q: What exactly must stay within 20 ms in FR-017 and SC-007: every event cycle, or a percentile? → A: The same convention as the existing event-cycle benchmark: the 99th percentile of the measured event cycles is at most 20 ms. The benchmark also reports the maximum cycle time, for information (it is not a limit). This replaces the earlier wording that required every cycle to take at most 20 ms.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The hunter chases the player when within range (Priority: P1)

A hunter pursues the player through the crypt, but only when the player is "close enough" in
travel cost. Each turn it either attacks (same room), waits (player out of reach), or steps toward
the player along the cheapest route. Distance is measured in exit cost, not in number of rooms.

**Why this priority**: This is the core behavior of the hunter; every other story refines it.

**Independent Test**: Build a small crypt with exits of known costs, place a hunter and the player
in chosen rooms, run one hunter turn for each case below, and check whether it attacks, waits or
moves, and through which exit.

**Acceptance Scenarios**:

1. **Given** a hunter and the player in the same room, **When** the hunter's turn comes, **Then** the hunter attacks with the same attack rule as part one and does not move. *(FR-002)*
2. **Given** a hunter in room A with `rango` 300, the player in room C, and a route A→B (cost 100) and B→C (cost 150), **When** the hunter's turn comes, **Then** d = 250 ≤ 300 and the hunter moves to B. *(FR-003, FR-005)*
3. **Given** the same crypt and a hunter with `rango` 250, **When** the hunter's turn comes, **Then** d = 250 is not greater than `rango`, so the hunter moves to B. *(FR-004, FR-005)*
4. **Given** the same crypt and a hunter with `rango` 200 and speed 100, **When** the hunter's turn comes at time T, **Then** d = 250 > 200, the hunter stays in A and its next action is at T + 100 (the waiting cost of 100). *(FR-004)*
5. **Given** a hunter whose only routes to the player's room go through a closed door, **When** the hunter's turn comes at time T, **Then** no route exists, the hunter waits (next action at T + 100 with speed 100), and the door stays closed. *(FR-004, FR-009)*
6. **Given** a hunter in A, the player in C, a direct exit A→C of cost 500 and a route A→B (cost 100) →C (cost 100), and `rango` 300, **When** the hunter's turn comes, **Then** d = 200 (the cheapest route, not the one with fewer exits) and the hunter moves to B. *(FR-003, FR-005)*
7. **Given** a hunter with speed 50 that moves through an exit with `costo` 120 at time T, **When** the move starts, **Then** the hunter is in the destination room at T and its next action is at T + 240 (= max(1, 120 × 100 // 50)). *(FR-006)*

---

### User Story 2 - Ties between routes are broken by room id (Priority: P1)

When several neighbors lie on a cheapest route, the hunter's choice must be predictable and
identical in every run.

**Why this priority**: Without a fixed tie-break the hunter's path (and so the whole game) would not
be reproducible, which replay depends on.

**Independent Test**: Build a crypt where two neighbors of the hunter's room give the same total
cost to the player, run one hunter turn, and check which neighbor it enters.

**Acceptance Scenarios**:

1. **Given** a hunter in room u (id 5) with two open exits, to neighbor B (id 7) with cost(u, B) = 100 and dist(B, player) = 200, and to neighbor D (id 3) with cost(u, D) = 200 and dist(D, player) = 100, and `rango` ≥ 300, **When** the hunter's turn comes, **Then** d = 300 for both and the hunter moves to D (the lowest id). *(FR-007)*
2. **Given** a hunter in room u with a neighbor of id 1 whose cost(u, v) + dist(v, player) is 400 and a neighbor of id 7 whose total is 300 (= d), **When** the hunter's turn comes, **Then** the hunter moves to the neighbor of id 7: the lowest id is chosen only among neighbors on a route of cost d. *(FR-007)*
3. **Given** a grid-shaped crypt where every exit costs 100, a hunter in the top-left room, the player in the bottom-right room, and therefore many different routes with the same minimum cost d, **When** the hunter's turn comes, **Then** the hunter moves to the neighbor with the lowest id among the neighbors that lie on some route of cost d, whatever the number of equally cheap routes. *(FR-007)*

---

### User Story 3 - The hunter always decides from the current state (Priority: P1)

Doors open and close, the player moves, and other actors die while the hunter waits for its turn.
At its turn the hunter's decision is exactly what a fresh computation from that moment would give;
nothing it worked out on an earlier turn can make it follow a stale route.

**Why this priority**: Explicitly required; a hunter that follows an outdated route would be
observably wrong and would break replay determinism.

**Independent Test**: Run a hunter turn, change the crypt state (open or close a door, move the
player, kill another actor), run the next hunter turn, and compare its decision with the decision of
an identical hunter placed in the new state with no history.

**Acceptance Scenarios**:

1. **Given** a hunter that on its previous turn moved along a route through door X, **When** door X closes before its next turn and an alternative route of cost d' ≤ `rango` exists, **Then** the hunter takes the alternative route; if there is none, it waits. *(FR-011, FR-012)*
2. **Given** a hunter that waited because every route went through a closed door, **When** that door opens before its next turn and the player is now within `rango`, **Then** the hunter moves along the route that uses the open door. *(FR-011, FR-012)*
3. **Given** a hunter that moved toward the player's room, **When** the player moves to another room before the hunter's next turn, **Then** the hunter decides using the player's room at the moment of its turn. *(FR-011, FR-012)*
4. **Given** a hunter and other actors in the crypt, **When** one of those actors dies between two hunter turns, **Then** the hunter's decision is the same as that of an identical hunter placed in the new state with no history. *(FR-011)*
5. **Given** a door that closes automatically and a hunter whose route uses it, **When** the door closes between two hunter turns, **Then** the hunter's next decision treats it as closed. *(FR-011, FR-012)*

---

### User Story 4 - The hunter knows the whole map, regardless of what the player has seen (Priority: P1)

The hunter's knowledge is the full crypt skeleton plus the current state of every door. It is not
limited by the player's fog of war, nor by which rooms' contents the game has downloaded so far.

**Why this priority**: Explicitly required; otherwise the hunter's behavior would change with the
order in which rooms were visited and with data-loading details the player cannot control.

**Independent Test**: Run the same sequence of actions on the same crypt and seed twice, once with
no room content downloaded in advance and once with all room contents already downloaded, and
compare every hunter decision.

**Acceptance Scenarios**:

1. **Given** a hunter whose cheapest route to the player crosses rooms that the player has never visited, **When** the hunter's turn comes, **Then** it moves along that route as if the player knew the whole map. *(FR-008)*
2. **Given** a hunter whose cheapest route crosses rooms whose content has not been downloaded, **When** the hunter's turn comes, **Then** its decision is the same as if every room's content had been downloaded. *(FR-010)*
3. **Given** the same crypt, seed and actions run twice, once with all room contents already downloaded and once with none, **When** the games are compared, **Then** every hunter decision and the final state are identical. *(FR-010, FR-014)*
4. **Given** a hunter whose cheapest route uses exits with different costs, **When** the hunter decides, **Then** it uses the exit costs from the skeleton downloaded at start (spec 001). *(FR-008)*

---

### User Story 5 - Hunters come from the catalog and other enemies do not change (Priority: P2)

A hunter is defined by a catalog entry with `"comportamiento": "cazador"` and a `rango`. Wanderers and
trackers keep exactly the behavior they had in part one.

**Why this priority**: Needed to introduce hunters into games, but the chase rules work as soon as a
hunter exists.

**Independent Test**: Load a crypt with a catalog entry whose behavior is `cazador` and check that
its hunter has that `rango`; run a crypt with no hunters and compare it with the spec 001 result.

**Acceptance Scenarios**:

1. **Given** a catalog entry with `"comportamiento": "cazador"` and `"rango": 400`, **When** an enemy of that entry is created, **Then** it behaves as a hunter with `rango` 400. *(FR-001)*
2. **Given** a crypt whose enemies are all wanderers and trackers, **When** the same seed and actions are run, **Then** the game state is identical to the state before this feature. *(FR-013)*
3. **Given** a crypt with a hunter, a wanderer and a tracker, **When** they take turns, **Then** the wanderer and the tracker choose their exits with the part-one rules and the hunter with the hunter rules. *(FR-013)*
4. **Given** a hunter that the part-one activation rule has not activated yet and a player within its `rango`, **When** time passes, **Then** the hunter does not attack, wait or move; once the player enters its room and the rule activates it, it decides from its next turn on as in User Story 1. *(FR-022)*
5. **Given** a catalog entry with `"comportamiento": "cazador"` and no `rango`, **When** its hunter is in a different room from the player, **Then** it waits (next action at T + 100 with speed 100) even if the player is one exit away; **and when** it shares a room with the player it attacks. *(FR-001, FR-002, FR-004)*

---

### User Story 6 - The player can tell hunters apart (Priority: P2)

When the player looks at the current room, hunters are shown in a way that sets them apart from
the other enemies, so the player knows which enemies will chase them from afar.

**Why this priority**: Helps the player understand the new threat, but the chase rules work
without it.

**Independent Test**: Show a room that holds a hunter and another kind of enemy, and a room that
holds only wanderers and trackers, and check the room description.

**Acceptance Scenarios**:

1. **Given** a room with a hunter and a wanderer, **When** the room is shown, **Then** both are listed with the same information as in part one (name, id and life) and the hunter carries a visible mark that the wanderer does not. *(FR-016)*
2. **Given** a room whose enemies are all wanderers and trackers, **When** the room is shown, **Then** it looks exactly as in part one. *(FR-016, FR-013)*

---

### User Story 7 - Hunters do not slow the game down (Priority: P2)

A crypt can hold dozens of active hunters, and each one needs a decision every turn. The game must
stay as responsive as in part one, a hunter that is only interested in its surroundings must cost
little however large the crypt is, and the benchmark must show the evidence for the choices made.

**Why this priority**: The behavior is correct without it, but a hunter that makes the game
sluggish would make the feature unusable, and performance claims need measurements.

**Independent Test**: Run the benchmark on the reference crypt with dozens of active hunters, and
on synthetic crypts of different sizes, and read the measurements it reports.

**Acceptance Scenarios**:

1. **Given** the reference crypt with dozens of active hunters, **When** the benchmark measures the event cycle between two player decisions, locally and without network or rendering, **Then** the 99th percentile of the measured cycles is at most 20 ms, and the benchmark also reports the maximum cycle time. *(FR-017)*
2. **Given** two crypts in which the region within a small `rango` of a hunter is identical, and one crypt is many times larger than the other, **When** the benchmark measures that hunter's decision, **Then** the time is practically the same in both. *(FR-018)*
3. **Given** the benchmark is run, **When** it finishes, **Then** it reports these comparisons: one hunter against many, and small `rango` against large `rango`, in a scenario where doors almost never change; and one computation per hunter against one computation shared by all hunters, and reusing earlier computations against always computing from scratch, each both for doors that change often and for doors that almost never change. *(FR-019)*
4. **Given** the ways of working out decisions compared by the benchmark, **When** the same crypt, seed and actions are run with each of them, **Then** every hunter decision is identical across all of them. *(FR-019, FR-011)*
5. **Given** the benchmark is run twice with the same seed, **When** the synthetic crypts are compared, **Then** they are identical. *(FR-020)*
6. **Given** the benchmark is run, **When** it measures hunters, **Then** it does not create or use any view. *(FR-021)*

---

### Edge Cases

- Hunter and player in the same room: the hunter attacks even if its `rango` is 0 (FR-002).
- A catalog entry for a hunter with no `rango`: `rango` is 0 (FR-001).
- A hunter not yet activated: it takes no turns, even if the player is within its `rango` (FR-022).
- d exactly equal to `rango`: the hunter moves (US1-3, FR-004).
- A route exists but costs more than `rango`: the hunter waits (US1-4).
- The player's room is reachable only through closed doors: no route, the hunter waits and never opens or unlocks anything (US1-5, FR-009).
- A cheaper route with more exits beats a dearer route with fewer exits (US1-6).
- Several neighbors on a route of cost d: the lowest room id wins (US2, FR-007).
- Two exits of the hunter's room lead to the same chosen neighbor with the same total: the exit with the lowest direction name is used (Assumptions).
- Doors change state, the player moves or other actors die between two hunter turns: the decision follows the state at the moment of the turn (US3).
- Rooms whose content has not been downloaded may lie on the hunter's route: they count as part of the skeleton (US4, FR-010).
- Speed changes while the hunter is crossing an expensive exit: the remaining time is rescaled as in spec 001 (FR-006).
- Replays and benchmarks of a crypt with hunters produce the same state every run (FR-014).
- A room with hunters and other enemies: all are listed, and only hunters carry the mark (FR-016).
- A hunter with a very large `rango`: its decision may reach the whole crypt, and the 20 ms limit for the event cycle still applies (FR-017).
- Doors that change very often, or almost never: the benchmark reports both situations for the two comparisons that depend on them (FR-019).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An enemy whose catalog entry has `"comportamiento": "cazador"` MUST behave as a hunter. Its catalog entry includes `rango`, an integer in cost units. If the entry has no `rango`, it MUST be treated as 0. No additional validation of `rango` is performed.
- **FR-002**: On its turn, if the hunter is in the same room as the player, it MUST attack with the same attack rule as part one, and MUST NOT move. This rule is evaluated before any other.
- **FR-003**: Otherwise, the hunter MUST consider d, the minimum total cost to reach the player's current room, where the cost of a route is the sum of the costs of the exits traversed (exit costs as defined in spec 001) and only exits that are open at that moment are used.
- **FR-004**: If no route exists, or d > `rango`, the hunter MUST wait, with the waiting cost of part one (100).
- **FR-005**: Otherwise (a route exists and d ≤ `rango`), the hunter MUST move one step along a route of cost d, crossing one exit.
- **FR-006**: The cost of the hunter's move MUST be the cost of the exit it crosses, and its duration MUST follow spec 001: `interval = max(1, exit_cost × 100 // speed)`, with the destination room entered when the move starts (spec 001 FR-016) and a speed change rescaled as in spec 001 FR-009.
- **FR-007**: Let u be the hunter's room. Among the neighbors v of u reachable by an open exit with cost(u, v) + dist(v, player) = d, the hunter MUST move to the one with the lowest room id, where dist is the minimum total cost computed under FR-003.
- **FR-008**: The hunter MUST know the full crypt skeleton (rooms and exits, including exit costs) and the current open or closed state of every door, independently of the player's fog of war (what the player has explored or seen).
- **FR-009**: The hunter MUST NOT open closed doors, and MUST NOT use a route through a closed door.
- **FR-010**: The hunter's decision MUST depend only on the skeleton downloaded in full at the start of the game (including exit costs), the current state of the doors, the hunter's room, the player's room and the hunter's `rango`; it MUST NOT depend on whether the content of any room has been downloaded.
- **FR-011**: On every turn, the hunter's decision (attack, wait, or move and through which exit) MUST be identical to the decision obtained by computing it from scratch from the state at that moment, whatever has changed since its previous turn: doors opened or closed, the player moved, or other actors dead.
- **FR-012**: The decision MUST be made at the moment of the hunter's turn, with the player's room and the state of the doors at that moment.
- **FR-013**: Wanderers and trackers MUST keep their part-one behavior: their decision rules are not changed by this feature.
- **FR-014**: With the same crypt, seed and sequence of actions, games with hunters MUST always produce the same state, including in replay and benchmark modes and regardless of which room contents have already been downloaded.
- **FR-015**: Hunter data (which enemies are hunters and their `rango`) MUST come only from the catalog served by the service (or its offline recording or cache); the game MUST NOT hardcode anything about a particular crypt or catalog entry.
- **FR-016**: The view of the current room MUST show hunters in a way that visibly distinguishes them from other enemies, while keeping the information shown for every enemy in part one. A room with no hunters MUST be shown exactly as in part one.
- **FR-017**: With the reference crypt and dozens of active hunters (at least 24), the 99th percentile of the measured event cycles between two player decisions MUST be at most 20 ms, measured locally with `--bench`, without network and without rendering, with the same measurement convention as the existing event-cycle benchmark. `--bench` MUST also report the maximum cycle time; the maximum is reported for information and is not a limit. The reference crypt is the one published by the course; until it is published, it is a synthetic crypt generated by `--bench`, deterministic by seed, of the size of the largest scenario of the existing event-cycle benchmark (FR-020). Once the official crypt is published, FR-017 MUST be measured with it, and that measurement prevails.
- **FR-018**: The cost of the decision of a hunter with a small `rango` MUST grow with the size of the region within its `rango`, not with the size of the crypt.
- **FR-019**: `--bench` MUST measure: one hunter against many hunters, and a small `rango` against a large `rango`, in a single scenario where doors almost never change; and one computation per hunter against one computation shared by all hunters, and reusing earlier computations against always computing from scratch, each both with doors that change often and with doors that almost never change. Every way of working out decisions that it compares MUST give the decisions required by FR-011.
- **FR-020**: The synthetic crypts that `--bench` generates MUST be deterministic by seed: the same seed gives the same crypt.
- **FR-021**: `--bench` MUST NOT create or use any view.
- **FR-022**: A hunter MUST follow the part-one activation rule like every other enemy: until it is activated it takes no turns (it does not attack, wait or move), and once activated it decides on every turn as FR-002 to FR-005 state.

### Key Entities

- **Hunter**: An enemy whose catalog behavior is `cazador`. Has a speed, a `rango` (integer in cost units) and a room.
- **Route cost (d)**: The minimum total cost of the exits traversed to go from the hunter's room to the player's room, using only open exits at that moment. Its value for the player's own room is 0.
- **Crypt skeleton**: The crypt structure (rooms and exits, including exit costs) downloaded in full at the start of the game, tied to a crypt version (spec 001).
- **Door state**: Whether each exit is currently open or closed; it can change during the game.
- **Event cycle**: Everything the game does between one player decision and the next, including the turns of every active enemy.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the acceptance scenarios in this spec pass as automated tests, each citing its FR.
- **SC-002**: In every hunter turn of every replayed game and benchmark crypt, the hunter's decision equals the one obtained by computing it from scratch from the state at that moment, with 0 discrepancies.
- **SC-003**: Across all recorded games and benchmark crypts, a hunter never moves when d > `rango`, never moves when no route exists, and never opens a door: 0 occurrences.
- **SC-004**: Running the same crypt, seed and actions with no room content downloaded in advance and with all of it downloaded produces identical hunter decisions and identical final state in 100% of runs.
- **SC-005**: Running the same crypt, seed and actions twice produces identical states in 100% of runs.
- **SC-006**: A crypt with no hunters produces exactly the same game state as before this feature for the same seed and actions.
- **SC-007**: On the reference crypt with at least 24 active hunters, the 99th percentile of the measured event cycles is at most 20 ms, and the maximum cycle time is reported.
- **SC-008**: For a hunter with a small `rango`, the decision time measured in a crypt many times larger than another, with an identical region within its `rango`, is no more than twice the time measured in the smaller crypt.
- **SC-009**: A single `--bench` run reports all the comparisons of FR-019, with both door situations where FR-019 requires them, and every compared way of working out decisions gives the same hunter decisions in 100% of runs.
- **SC-010**: Running `--bench` twice with the same seed generates identical synthetic crypts in 100% of runs, and no run creates a view.

## Assumptions

- Exit costs, the duration formula and the destination-room-entered-at-start rule are those of spec 001; this spec does not redefine them.
- Distances are computed with the exit costs of spec 001, which are the same in both directions; a door's open or closed state is shared by both sides of the connection.
- The hunter's `rango` is supplied by the service as the assignment describes it; as with `costo` in spec 001, the game does not validate its range or type (FR-001); only a missing `rango` is given a value (0). A hunter with `rango` 0 only attacks when it shares a room with the player.
- Waiting and attacking cost what they cost in part one (100 each); only moves use exit costs (spec 001 FR-006).
- Other actors, alive or dead, do not block a route and do not change its cost.
- If two exits of the hunter's room lead to the same chosen neighbor with the same total, the exit with the lowest direction name is used. The tie-break by room id in FR-007 does not distinguish them, and a fixed rule is needed for determinism (FR-014).
- The turn order among actors, the activation of enemies (FR-022), and how wanderers and trackers decide are those of part one and spec 001.
- Which room contents the game downloads, and when, is decided by the part-one rules; this spec only requires that no hunter decision depends on it (FR-010).
- The spec 001 Assumptions require this spec to include an acceptance scenario equivalent to US2-3 of spec 001, tested against the real hunter behavior: that is US1-7.
- How hunters are marked in the room view (FR-016) is left open: any visible mark that other enemies do not carry is enough.
- "Dozens" of hunters in FR-017 is read as at least 24, so that the limit can be tested; "many times larger" in US7-2 and SC-008 is read as at least 10 times larger, and "small `rango`" as one whose region within reach is a small fraction of the crypt.
- The 20 ms limit (on the 99th percentile) and its measurement convention are those of the existing event-cycle benchmark. The reference crypt is defined in FR-017: the course's crypt once published, a synthetic stand-in before that.
- The doors that "change often" or "almost never change" in the benchmark are doors opened or closed by the game's own rules (for example, doors that close automatically), generated deterministically by seed. The single door scenario used by the other two comparisons is the one in which doors almost never change.
