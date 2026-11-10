# Feature Specification: Terrain — Exit Costs

**Feature Branch**: `001-exit-costs`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Terrain: exit costs. Each exit may declare a "costo" field, an integer >= 1. If it is not declared, its cost is 100. The cost is the same in both directions. Moving through an exit is an action whose base cost is that exit's cost, instead of the fixed value 100 from part one. The interval is still computed with the part-one formula: interval = max(1, exit_cost * 100 // speed). The rule applies to all actors (player, wanderers, trackers and hunters). The cost of attacking, waiting and every other action does not change. Wanderers and trackers keep their behavior; only the duration of their movement changes. Data: exit costs come from the crypt skeleton and are valid while the crypt version matches. Data persisted by part one must be invalidated through the existing version check. View: the view shows the cost of each exit of the current room. Required scenarios: A high-speed actor crosses an exit of cost 1: the interval is at least 1. An actor's speed changes while crossing an expensive exit: the remaining time is rescaled as remaining = max(1, (end_time - now) * old_speed // new_speed), and the action now ends at now + remaining."

## Clarifications

### Session 2026-11-10

- Q: If only one side of a connection declares `costo`, what is the cost in the other direction? → A: The declared value applies to both directions.
- Q: Should crypt data with `costo` < 1 or a non-integer `costo` be rejected? → A: No. The assignment does not define that rule; as in part one, `costo` is optional and defaults to 100 (like `cerrada` defaults to false). No new invalid-data rule is added.
- Q: What happens if the two sides of a connection declare different `costo` values? → A: The connection is an inconsistent door, reported by extending the existing part-one inconsistent-door validation (not a new invalid-data rule).
- Q: Does this spec define how hunters choose their route? → A: No; hunter route selection stays in the hunter spec. This spec only fixes the duration of hunter moves.
- Q: Is the existing version check enough to invalidate part-one persisted data? → A: Yes; the assignment states that part-two crypts have new versions.
- Correction (2026-11-10): Is the crypt skeleton persisted? → A: No. It is downloaded from the service every time a game starts; only catalog entries are cached, and saved games and replay logs store the crypt version. Exit costs are therefore read from the skeleton on every start, and a saved game or replay log from a different crypt version is rejected by the existing version check. The earlier scenario reusing persisted exit costs without a new request was removed.
- Correction (2026-11-10, analysis I1): Must a tracker choose the same sequence of exits as in part one when costs differ? → A: No. Trail freshness and random draws depend on time, so only the rule is preserved: given the same state (room, trails, clock, open exits), a tracker chooses the same exit as the part-one rule. The identical-sequence check holds only when every exit costs 100 (SC-004). US2-2 rewritten.
- Correction (2026-11-10, analysis U1): Where is an actor while crossing an exit? → A: The actor enters the destination room when the move starts (traps, victory and trail marks apply immediately), and its next action is scheduled at start + interval. Added as FR-016; scenarios now say "the actor's next action is at" instead of "the move ends at".
- Correction (2026-11-10, analysis G3): How is the hunter case of US2-3 covered? → A: The hunter spec must include a scenario equivalent to US2-3 (Assumptions).
- Correction (2026-11-10, analysis I3): Is the exit cost validated? → A: No. It is an integer, ≥ 1 per the assignment, and not validated (Key Entities aligned with FR-001).
- Correction (2026-11-10, analysis D1): US1-3 overlapped US1-7 → A: US1-3 is now the case where both sides declare 250; US1-7 remains the one-sided case.
- Correction (2026-11-10, analysis A1): What does offline mode read? → A: In `--offline` mode the skeleton, with its costs, is read from the recording of that crypt version.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Movement duration depends on the exit crossed (Priority: P1)

The player moves through an exit of the current room. The time the move takes is no longer the
fixed part-one value; it depends on the cost declared by that exit and on the player's speed.
Crossing a "cheap" passage is fast, crossing an "expensive" one (rubble, a flooded corridor) is
slow. Exits that declare no cost behave exactly as in part one.

**Why this priority**: This is the core rule of the feature; every other story depends on exit
costs actually affecting the timeline.

**Independent Test**: Load a crypt whose skeleton declares exits with different costs, move the
player through each one, and check the time of the player's next action after each move.

**Acceptance Scenarios**:

1. **Given** an exit with `costo` 300 and a player with speed 100, **When** the player moves through it at time T, **Then** the player is in the destination room at T and the player's next action is at T + 300 (interval = max(1, 300 × 100 // 100) = 300). *(FR-003, FR-004, FR-016)*
2. **Given** an exit that declares no `costo` and a player with speed 100, **When** the player moves through it at time T, **Then** the player's next action is at T + 100, identical to part one. *(FR-002, FR-004)*
3. **Given** a connection whose two sides, A→B and B→A, both declare `costo` 250, **When** an actor moves from A to B and later from B to A, **Then** both moves use cost 250. *(FR-005)*
4. **Given** an exit with `costo` 50 and a player with speed 150, **When** the player moves through it, **Then** the interval is 50 × 100 // 150 = 33. *(FR-004)*
5. **Given** an exit with `costo` 1 and an actor with a very high speed (e.g. 1000), **When** the actor crosses it, **Then** the interval is 1 (never 0): max(1, 1 × 100 // 1000) = max(1, 0) = 1. *(FR-004, FR-006)*
6. **Given** a connection whose two sides declare `costo` 100 and 200, **When** the crypt is loaded, **Then** the connection is reported as an inconsistent door by the same validation that reports part-one inconsistent doors. *(FR-013)*
7. **Given** a connection where only the exit A→B declares `costo` 300 and the exit B→A declares none, **When** an actor moves from B to A, **Then** the move uses cost 300. *(FR-005)*
8. **Given** a player standing in a room whose exits cost 500, **When** the player attacks or waits, **Then** the action takes the same time as in part one. *(FR-006)*

---

### User Story 2 - Enemies are subject to the same exit costs (Priority: P1)

Wanderers, trackers and hunters crossing an exit take a time that depends on that exit's cost and
on their own speed, with the same formula as the player. How wanderers and trackers choose where
to go does not change.

**Why this priority**: The rule must be uniform for all actors, otherwise the timeline and
determinism guarantees break.

**Independent Test**: Place a wanderer and a tracker in a crypt with costed exits, check that from a
given state they choose the exit the part-one rule chooses, and that the time of their next action
after moving follows the exit cost.

**Acceptance Scenarios**:

1. **Given** a wanderer with speed 100 that moves through an exit with `costo` 200 at time T, **When** its turn ends, **Then** the wanderer is in the destination room at T and its next action is at T + 200. *(FR-007, FR-016)*
2. **Given** a tracker in a given state (room, trail marks of the neighbouring rooms, clock, open exits) where the exits declare costs other than 100, **When** the tracker decides where to move, **Then** it chooses the same exit that the part-one rule chooses from that same state. *(FR-008)*
3. **Given** a hunter with speed 50 that moves through an exit with `costo` 120 at time T, **When** its turn ends, **Then** its next action is at T + 240. *(FR-007)*

---

### User Story 3 - Speed change while crossing an expensive exit (Priority: P1)

An actor has moved through an expensive exit and is waiting for its next action when its speed
changes (for example because an effect starts or ends). The remaining time until its next action
is rescaled to the new speed.

**Why this priority**: Explicitly required scenario; long crossings make speed changes mid-action
far more frequent than in part one.

**Independent Test**: Move an actor through an expensive exit, change its speed before its next
action, and check the new time of that next action.

**Acceptance Scenarios**:

1. **Given** an actor with speed 100 that moves through an exit with `costo` 500 at time 0 (next action at 500), **When** its speed changes to 200 at time 100, **Then** remaining = max(1, (500 − 100) × 100 // 200) = 200, and the actor's next action is now at 300. *(FR-009)*
2. **Given** an actor with speed 200 that moved through an exit and whose next action is at time 1000, **When** its speed changes to 50 at time 900, **Then** remaining = max(1, (1000 − 900) × 200 // 50) = 400, and the actor's next action is now at 1300. *(FR-009)*
3. **Given** an actor that moved through an exit and whose next action is at time 101, **When** its speed changes from 10 to 1000 at time 100, **Then** remaining = max(1, 1 × 10 // 1000) = max(1, 0) = 1, and the actor's next action is at 101 (never at the current time). *(FR-009, FR-006)*

---

### User Story 4 - The player sees the cost of each exit (Priority: P2)

When the player looks at the current room, each exit is listed together with its cost, so the
player can plan routes by how long they take.

**Why this priority**: Needed to make the mechanic understandable, but the game rule works without it.

**Independent Test**: Enter a room with exits of different costs (including one without a declared
cost) and check the room description.

**Acceptance Scenarios**:

1. **Given** a room with an exit `norte` of `costo` 300 and an exit `sur` with no declared cost, **When** the room is shown, **Then** `norte` is shown with cost 300 and `sur` with cost 100. *(FR-010)*
2. **Given** a room with a closed exit of `costo` 40, **When** the room is shown, **Then** the exit is shown as closed and with cost 40. *(FR-010)*

---

### User Story 5 - Exit costs are always current; old saves and logs are rejected by version (Priority: P2)

The crypt skeleton is never persisted: it is downloaded from the service every time a game starts,
so exit costs are always read fresh from it. Saved games and replay logs store the crypt version;
one recorded against a different crypt version (for example, from part one, without exit costs) is
rejected by the existing version check, so it can never be loaded or replayed against costs it was
not played with.

**Why this priority**: Without it, a part-one save or log could be loaded or replayed with
different move durations, producing a state that was never played.

**Independent Test**: Start a game and check that exit costs come from the skeleton downloaded at
start; then try to load a saved game and replay a log whose crypt version differs from the current
one and check that both are rejected.

**Acceptance Scenarios**:

1. **Given** a crypt whose skeleton declares exit costs, **When** a game starts, **Then** the skeleton is downloaded from the service and every exit has the cost it declares (or 100), with no exit data taken from saved games, replay logs or the catalog cache. *(FR-011)*
2. **Given** a saved game whose stored crypt version differs from the current crypt version (e.g. saved in part one), **When** the player tries to load it, **Then** it is rejected by the existing version check. *(FR-012)*
3. **Given** a replay log whose stored crypt version differs from the current crypt version, **When** it is replayed, **Then** it is rejected by the existing version check. *(FR-012)*
4. **Given** a saved game whose stored crypt version matches the current crypt version, **When** the player loads it, **Then** it loads and moves use the exit costs from the skeleton downloaded at start. *(FR-011, FR-012)*

---

### Edge Cases

- `costo` = 1 with a very high speed: interval is clamped to 1 (US1-5).
- Speed change that would make the remaining time 0: remaining is clamped to 1 (US3-3).
- A connection declares `costo` on only one of its two sides: that cost applies to both directions (FR-005, US1-7).
- A connection declares different `costo` values on its two sides: it is an inconsistent door, reported like part-one inconsistent doors (FR-013, US1-6).
- An exit with no opposite exit in the destination room: its own cost (declared or 100) applies (FR-002, FR-003).
- Attacking or waiting in a room whose exits are expensive: the cost of those actions is unchanged (FR-006).
- Replays, benchmarks and verification of a crypt with exit costs produce the same state every run (FR-014).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each exit in the crypt skeleton MAY declare an optional `costo` field (an integer ≥ 1 per the assignment). No additional validation of its value is performed.
- **FR-002**: An exit that does not declare `costo` (and whose opposite exit does not declare one either) MUST have cost 100.
- **FR-003**: Moving through an exit MUST be an action whose base cost is that exit's cost, replacing the fixed move cost of 100 from part one.
- **FR-004**: The interval of a move MUST be computed as `interval = max(1, exit_cost × 100 // speed)`, where `//` is integer division and `speed` is the actor's speed when the move starts.
- **FR-005**: The cost of an exit MUST be the same in both directions of the connection. If only one side of the connection declares `costo`, that value applies to both directions.
- **FR-006**: The cost of attacking, waiting and every action other than moving MUST remain as in part one; every action interval MUST be at least 1.
- **FR-007**: FR-003 and FR-004 MUST apply to every actor: the player, wanderers, trackers and hunters.
- **FR-008**: The decision rules of wanderers and trackers (which exit they choose) MUST remain as in part one; only the duration of their moves changes.
- **FR-009**: When an actor's speed changes while it is waiting for its next action after a move, the remaining time MUST be rescaled as `remaining = max(1, (end_time − now) × old_speed // new_speed)`, where `end_time` is the time of that next action, and the actor's next action MUST be at `now + remaining`.
- **FR-010**: The view of the current room MUST show the cost of each of its exits (the declared value, or 100 when not declared), for open and closed exits alike.
- **FR-011**: Exit costs MUST be read from the crypt skeleton, which is downloaded from the service every time a game starts (in `--offline` mode, read from the offline recording of the skeleton); exit costs MUST NOT be persisted or read from saved games, replay logs or the catalog cache.
- **FR-012**: A saved game or replay log whose stored crypt version differs from the current crypt version (for example, one from part one) MUST be rejected by the existing version check; no other invalidation mechanism (such as deleting files by hand) is introduced.
- **FR-013**: The existing part-one inconsistent-door validation MUST be extended so that a connection whose two sides both declare `costo` with different values is reported as an inconsistent door, in the same way as part-one inconsistent doors. No other new invalid-data rule is introduced.
- **FR-014**: With the same crypt, seed and sequence of actions, games with exit costs MUST always produce the same state, including in replay, benchmark and verification modes.
- **FR-015**: Exit costs MUST NOT be hardcoded for any particular crypt; they come only from the crypt skeleton served by the service (or its offline recording).
- **FR-016**: An actor that moves through an exit MUST enter the destination room when the move starts; traps, victory and trail marks MUST apply at that moment. The actor's next action MUST be scheduled at the move's start time + interval (FR-004).

### Key Entities

- **Exit**: A connection from one room to another in a given direction. Attributes relevant here: destination room, closed/open state, required key, and cost (an integer, ≥ 1 per the assignment and not validated; default 100; shared by both directions of the connection).
- **Actor**: Player, wanderer, tracker or hunter. Has a speed that determines how long each action takes.
- **Move action**: An action in the timeline. At its start time the actor enters the destination room; its base cost is the cost of the exit crossed, and the actor's next action is at start time + interval.
- **Crypt skeleton**: The crypt structure (rooms and exits, including exit costs) tied to a crypt version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the acceptance scenarios in this spec pass as automated tests, each citing its FR.
- **SC-002**: For every move by every actor type, the actor's next action is at the move's start time plus `max(1, exit_cost × 100 // speed)` (unless a speed change rescales it per FR-009), with 0 discrepancies across a full replayed game.
- **SC-003**: No action in any game ever has a duration of 0 (verified over all recorded games and benchmark crypts).
- **SC-004**: A crypt where no exit declares `costo` produces exactly the same game state as in part one for the same seed and actions.
- **SC-005**: Running the same crypt, seed and actions twice produces identical states in 100% of runs.
- **SC-006**: The player can read the cost of every exit of the current room directly from the room view, without any extra command.
- **SC-007**: Every game start shows the exit costs declared by the current skeleton, and 100% of saved games and replay logs from a different crypt version are rejected, with no manual deletion of files.

## Assumptions

- "Speed" in FR-004 is the actor's speed at the moment the move starts; later changes are handled only by FR-009.
- How hunters choose their route (e.g. whether they prefer cheaper exits) is defined by the hunter spec, not by this spec; this spec only fixes the duration of their moves (confirmed 2026-11-10). The hunter spec MUST include an acceptance scenario equivalent to US2-3 (a hunter's next action after a move is at T + `max(1, costo × 100 // speed)`), tested against the real hunter behaviour.
- Wanderers and trackers ignore exit costs when choosing an exit (FR-008).
- Part-two crypts have new versions (stated by the assignment), so the existing version check is sufficient to reject part-one saved games and replay logs (confirmed 2026-11-10). The skeleton itself is never persisted.
- `costo` values are supplied by the service as the assignment describes them; the game does not validate their range or type (FR-001).
- Closed exits keep their cost; the cost applies once the exit can be crossed.
- In `--offline` mode the skeleton, with its costs, is read from the recording of that crypt version.
