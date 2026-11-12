# Feature Specification: Fog of War and Automatic Travel

**Feature Branch**: `003-fog-of-war`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Fog of war and automatic travel ("ir a") for the Cripta game. Why: until now the player sees the whole map. We want the player to know only what they have explored, for the game to remember what they saw, and for them to be able to travel automatically within that knowledge without cheating. Room states from the player's point of view: Explored: the player has entered it at least once (the starting room is explored from time 0). The player knows its name, its exits, the cost of each exit, and the state of its doors as of the last observation. Sighted: not explored, but it is the destination of an exit of an explored room. The player only knows that a room exists behind that exit. Unknown: none of the above. The player knows nothing. Rules: Door memory: the player observes a door when they are in either of the two rooms it connects. The player's map remembers each door's state as it was at the last observation, even if it has changed since (for example, a door with automatic closing may appear open on the map while actually being closed). Lit torch (antorcha): while it is lit, entering a room also explores all of its neighbors, through any exit, open or closed. Exploring a neighbor this way reveals its name and exits, not its contents, and does not activate its enemies or traps. Everything the view shows and everything the "ir a" command uses must be derived only from the player's knowledge. Downloading the full skeleton is infrastructure and does not count as knowledge. The player's knowledge is game state: it is saved in the save file, it is reverted by the rollback scroll (pergamino de retroceso), and it is part of the timeline. The interface offers a command to view the known map: explored rooms, their exits, and sighted rooms. Command "ir a <room>": Takes the player to an explored room through ordinary moves. If the room is not explored, the command is rejected and consumes no time. The route uses only explored rooms and only exits the map remembers as open. It minimizes the sum of costs; ties are broken the same way as the hunter (first step toward the neighbor with the lowest id), as defined in spec 002. Each step is a complete player action: it consumes time according to the exit cost (spec 001), and clock events happen normally between steps. The route is recomputed before every step with the current knowledge. It never opens doors, even if the player has the key. The trip stops when: the player reaches the destination; enters a room containing enemies (active or asleep); takes damage; or no known route exists anymore. The view shows the reason. In the game log (partida.log) each step is recorded as an individual move, and the "ir a" order is also recorded as a comment. The rollback scroll reverts only the last step, and the trip does not continue. Performance requirement: computing one step of "ir a" with the full known map of the reference crypt takes at most 5 ms."

## Clarifications

### Session 2026-11-11

- Q: When the lit torch explores a neighbor, does the player also observe the doors of that neighbor? → A: No. Only the door joining the room entered to each neighbor is observed. The neighbor's other doors are unobserved: the map holds no state for them, and "ir a" does not use them until the player is in one of the two rooms each connects.
- Q: Is a door observed only at the moment the player enters a room, or also when it changes state while the player stays in one of the two rooms it connects? → A: Continuously. While the player is in one of the two rooms a door connects, the map always holds that door's real current state, so a change is seen at the moment it happens.
- Q: Is an "ir a" order that is rejected (unexplored destination) recorded in the game log? → A: Yes. A rejected order is recorded in the game log as a comment, so the log shows every "ir a" order; it is not a move and does not change the game state.

### Session 2026-11-12

- Q: When a step meets more than one reason to stop at once, which single reason is shown? → A: The first that applies in the order of FR-022: arrival, enemies in the room, damage, end of the game, no route.
- Q: Is a trip stopped by the rollback scroll given its own stop reason? → A: Yes. The trip stops with its own reason (rolled back by a scroll), added to the reasons of FR-022 and shown to the player.
- Q: How does the player name the room in "ir a"? → A: By its id only, as shown in the known map.
- Q: Does the 5 ms limit of FR-026 apply to every computation or to a percentile? → A: To the 99th percentile of the measured computations; the maximum is reported for information and is not a limit (same convention as spec 002).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The player only knows what they have explored (Priority: P1)

The player starts knowing only the starting room and the existence of the rooms behind its exits.
Each time they enter a room, that room becomes known in full (name, exits, exit costs, doors) and
the rooms behind its exits become sighted. Everything the player is shown about the crypt comes
from this knowledge and nothing else.

**Why this priority**: This is the core rule of the feature; the rest (door memory, torch, travel)
builds on the three room states.

**Independent Test**: Start a game on a crypt with a known layout, check what the player knows at
time 0, move through one exit, and check which rooms are explored, sighted and unknown.

**Acceptance Scenarios**:

1. **Given** a new game, **When** it starts at time 0, **Then** the starting room is explored, the destinations of its exits are sighted and every other room is unknown. *(FR-001, FR-002, FR-003, FR-004)*
2. **Given** a sighted room R, **When** the player enters R for the first time, **Then** R becomes explored, and the destinations of its exits that are not explored become sighted. *(FR-001, FR-003, FR-004)*
3. **Given** an explored room, **When** it is shown, **Then** the player sees its name, its exits, the cost of each exit and the state of each door as of the last observation. *(FR-003, FR-010)*
4. **Given** a sighted room, **When** the known map is shown, **Then** the player only learns that a room exists behind that exit: no name, no exits, no contents. *(FR-004, FR-010)*
5. **Given** a room that is neither explored nor sighted, **When** the known map is shown, **Then** it does not appear at all. *(FR-005, FR-010)*
6. **Given** the full crypt skeleton downloaded at the start, **When** the view is built, **Then** nothing that is not in the player's knowledge is shown, whatever the skeleton holds. *(FR-010, FR-011)*
7. **Given** a room that is already explored, **When** the player enters it again, **Then** it stays explored and nothing about its state is lost. *(FR-001)*
8. **Given** the player in a room with an exit toward a sighted room, **When** the current room is shown, **Then** the exit is listed with its direction, its cost and its door state, but without the name of the destination, which the player does not know. An exit toward an explored room is listed with the destination's name. *(FR-004, FR-010)*

---

### User Story 2 - The map remembers doors as last observed (Priority: P1)

The player's map keeps each door's state as it was the last time the player observed it, even
when the real door has changed since. A door that closes automatically may therefore appear open
on the map while it is closed. The map is corrected only by observing the door again.

**Why this priority**: Explicitly required; it is what makes automatic travel able to fail
honestly instead of cheating with real-time information the player does not have.

**Independent Test**: Observe an automatically closing door open, move away, let it close, and check
that the map still shows it open until the player is again in one of the two rooms it connects.

**Acceptance Scenarios**:

1. **Given** the player in a room with a door that is open, **When** the player observes it, **Then** the map records it as open. *(FR-006)*
2. **Given** a door recorded as open on the map that closes while the player is in a room that does not touch it, **When** the map is shown, **Then** it still shows the door as open. *(FR-007)*
3. **Given** a door recorded as open on the map that is really closed, **When** the player enters one of the two rooms it connects, **Then** the map is updated and shows the door as closed. *(FR-006, FR-007)*
4. **Given** a door observed from the room on one side, **When** the player is later in the room on the other side, **Then** the door is observed again from there, and the map keeps the state of the latest observation. *(FR-006)*
5. **Given** the player stays in a room whose door closes automatically, **When** the door closes, **Then** the map shows it as closed at that moment. *(FR-006)*

---

### User Story 3 - The lit torch explores the neighbors (Priority: P1)

While the player's torch is lit, entering a room also explores every neighbor of that room,
through open and closed exits alike. This reveals the neighbors' names and exits only. It never
activates enemies or traps, and it does not reveal contents.

**Why this priority**: Explicitly required; it changes how much the player knows after each step
and interacts with rollback.

**Independent Test**: Light the torch, enter a room that has a closed exit to a room with an
enemy and a trap, and check what the player knows afterwards and that nothing activated.

**Acceptance Scenarios**:

1. **Given** a lit torch, **When** the player enters a room, **Then** every neighbor of that room, through open or closed exits, becomes explored. *(FR-008)*
2. **Given** a lit torch and a neighbor that holds enemies and traps, **When** the player enters the room next to it, **Then** the neighbor is explored with its name and exits, its contents are not revealed, and its enemies and traps are not activated. *(FR-009)*
3. **Given** an unlit torch, **When** the player enters a room, **Then** only that room becomes explored. *(FR-001, FR-008)*
4. **Given** a lit torch and a neighbor reached only through a closed door, **When** the player enters the room, **Then** the neighbor is explored although the player cannot go through the door. *(FR-008)*
5. **Given** a lit torch and a neighbor with doors other than the one joining it to the room entered, **When** the player enters the room, **Then** those other doors are unobserved: the map holds no state for them and "ir a" does not use them. *(FR-009, FR-017)*
6. **Given** a scroll that reverts an entry made with the torch lit, **When** the scroll is read, **Then** the rooms explored by the torch return to their previous state (sighted or unknown, as they were). *(FR-013, FR-014)*

---

### User Story 4 - Knowledge is part of the game state (Priority: P1)

What the player knows is saved with the game, reverted by the rollback scroll and part of the
timeline: the same crypt, seed and actions always give the same knowledge.

**Why this priority**: Without it, loading a game or reading a scroll would give the player back
the whole map or lose what they had seen, and replays would diverge.

**Independent Test**: Explore some rooms, save and load, and compare the knowledge; read a scroll
and compare with the knowledge before the reverted action.

**Acceptance Scenarios**:

1. **Given** a game in which the player has explored several rooms and seen some doors, **When** it is saved and loaded, **Then** the explored and sighted rooms and the remembered door states are the same. *(FR-012)*
2. **Given** a scroll that reverts the player's last action, **When** that action had made the player explore a new room, **Then** the room returns to the state it had before (sighted or unknown). *(FR-013)*
3. **Given** a door observation made by the reverted action, **When** the scroll is read, **Then** the map returns to the state of that door before the action. *(FR-013)*
4. **Given** the same crypt, seed and sequence of actions run twice, **When** the games are compared, **Then** the knowledge is identical at every moment. *(FR-014)*

---

### User Story 5 - The player can view the known map (Priority: P2)

The interface offers a command that shows the known map: the explored rooms, their exits and the
sighted rooms.

**Why this priority**: Needed so that the player can choose where to go; the rules above work
without it.

**Independent Test**: Explore some rooms and run the command, then check that it lists exactly
what is known.

**Acceptance Scenarios**:

1. **Given** a game with explored and sighted rooms, **When** the player asks for the known map, **Then** it shows each explored room with its id (the one used by "ir a") and its exits (and their costs and remembered door states) and each sighted room as an existing but unexplored room. *(FR-015)*
2. **Given** unknown rooms, **When** the known map is shown, **Then** they do not appear. *(FR-005, FR-015)*
3. **Given** the command is run, **When** it finishes, **Then** it consumes no time. *(FR-015)*

---

### User Story 6 - "ir a" takes the player to an explored room (Priority: P1)

The player orders "ir a" followed by a room. The game moves the player there through ordinary
moves, using only what the player knows: explored rooms and exits the map remembers as open. The
trip never opens doors and stops when something relevant happens.

**Why this priority**: It is the main user-facing function of the feature.

**Independent Test**: Build a crypt with known and unknown parts, order trips to different
rooms, and check the route, the time consumed and the reason the trip stops.

**Acceptance Scenarios**:

1. **Given** a room that is not explored (including an id that matches no room the player knows), **When** the player orders "ir a" toward it, **Then** the order is rejected and consumes no time. *(FR-016)*
2. **Given** an explored destination and a route of explored rooms joined by exits the map remembers as open, **When** the player orders "ir a", **Then** the player moves step by step along the cheapest route and the trip stops on arrival, with that reason shown. *(FR-017, FR-018, FR-019, FR-022, FR-023)*
3. **Given** two routes, one with more exits and lower total cost and one with fewer exits and higher total cost, **When** the player orders "ir a", **Then** the player takes the cheaper one. *(FR-018)*
4. **Given** several first steps on routes of the same minimum cost, **When** the player orders "ir a", **Then** the first step is toward the neighbor with the lowest id, as the hunter does in spec 002. *(FR-018)*
5. **Given** a route whose shortest path crosses a sighted but unexplored room, **When** the player orders "ir a", **Then** that room is not used. *(FR-017)*
6. **Given** a route whose only connection is a door that the map remembers as closed, and the player has its key, **When** the player orders "ir a", **Then** the door is not opened and no route exists. *(FR-017, FR-021)*
7. **Given** a trip of three steps with exits of cost 100, 300 and 50 and a player with speed 100, **When** the trip runs from time T, **Then** the steps take 100, 300 and 50 time units, and clock events (enemy turns, doors closing) happen between steps as in an ordinary game. *(FR-019)*
8. **Given** a trip, **When** the game log is written, **Then** each step appears as an individual move and the "ir a" order appears as a comment. *(FR-024)*
9. **Given** an order rejected because the destination is unexplored, **When** the game log is written, **Then** the order appears as a comment and no move is recorded. *(FR-016, FR-024)*
10. **Given** the player already in the destination room, **When** the player orders "ir a" toward it, **Then** the trip ends at once as arrived and consumes no time. *(FR-022)*

---

### User Story 7 - The trip is recomputed and stops when it should (Priority: P1)

Before every step the route is recomputed with the knowledge at that moment. The trip stops when
the player reaches the destination, enters a room with enemies, takes damage, or no known route
remains, and the view says which of these happened.

**Why this priority**: Explicitly required; these rules are what keep the trip safe and honest.

**Independent Test**: Run trips in which a door was remembered open but is closed, a room has
sleeping enemies, and the player is damaged, and check that each trip stops for the right reason.

**Acceptance Scenarios**:

1. **Given** the map remembers a door as open but it is closed, **When** the player observes it during the trip, **Then** the map is updated, the route is recomputed, and if no route remains the trip stops without consuming extra time. *(FR-006, FR-020, FR-022)*
2. **Given** the map remembers a door as open but it is closed and an alternative known route exists, **When** the player observes it, **Then** the route is recomputed and the trip continues along the alternative. *(FR-020)*
3. **Given** a route that enters a room with sleeping enemies, **When** the player enters it, **Then** the enemies activate according to the part-one rules and the trip stops, with that reason shown. *(FR-022, FR-023)*
4. **Given** a room with active enemies, **When** the player enters it during a trip, **Then** the trip stops. *(FR-022)*
5. **Given** a trap, an enemy or an effect (such as poison) that damages the player during a step or between two steps, **When** the damage is taken, **Then** the trip stops with that reason shown. *(FR-022, FR-023)*
6. **Given** a step that ends the game (the player reaches the exit and wins, or dies), **When** the step finishes, **Then** the trip stops and no further step is taken, with that reason shown. *(FR-022, FR-023)*
7. **Given** a step that arrives at the destination in a room with enemies, or a step in which the player dies, **When** the step finishes, **Then** the reason shown is the first that applies in the order of FR-022 (arrival, then enemies in the room, then damage, then end of the game). *(FR-022, FR-023)*
8. **Given** a trip whose next step has no known route, **When** the route is recomputed, **Then** the trip stops with that reason shown. *(FR-022, FR-023)*
9. **Given** a trip during which the clock events change the state of the doors, **When** the next step is about to start, **Then** the route used is the one computed with the knowledge at that moment. *(FR-020)*

---

### User Story 8 - The scroll reverts only the last step (Priority: P1)

When the player reads a rollback scroll during or after a trip, only the last step is reverted
and the trip does not continue.

**Why this priority**: Explicitly required; otherwise a scroll could revert a whole trip or resume
it behind the player's back.

**Independent Test**: Start a trip of several steps, read the scroll in the middle, and check the
state and that no further step is taken.

**Acceptance Scenarios**:

1. **Given** a trip in progress, **When** the player reads a scroll, **Then** only the last step is reverted, the trip does not continue and it stops with the reason "rolled back by a scroll". *(FR-022, FR-023, FR-025)*
2. **Given** a trip whose last step explored new rooms, **When** the scroll reverts that step, **Then** those rooms and the door observations of that step return to their previous state. *(FR-013, FR-025)*
3. **Given** a trip that has ended, **When** the player reads a scroll, **Then** it reverts the last step of the trip and nothing else. *(FR-025)*

---

### User Story 9 - "ir a" is fast (Priority: P2)

Working out one step of a trip must not slow the game down, even with the full known map of the
reference crypt.

**Why this priority**: The behavior is correct without it, but a slow step would make the command
unusable.

**Independent Test**: Measure one step of "ir a" with the full known map of the reference crypt.

**Acceptance Scenarios**:

1. **Given** the full known map of the reference crypt, **When** one step of "ir a" is computed, **Then** the 99th percentile of the measured computations is at most 5 ms, and the maximum is also reported. *(FR-026)*
2. **Given** the benchmark is run twice with the same seed, **When** the synthetic crypts are compared, **Then** they are identical. *(FR-027)*

---

### Edge Cases

- The starting room is explored from time 0 (FR-002).
- A room reached by the torch is explored without being entered: it does not activate enemies or traps and does not reveal contents (FR-009).
- A room is sighted only through an exit of an explored room; a room that stops being the destination of any explored room's exit cannot happen, because exploration is never lost except by rollback (FR-004, FR-013).
- The torch is lit while the player is already in a room: only rooms entered afterwards trigger torch exploration (Assumptions).
- A door that closes automatically while the player is far away stays open on the map until observed again (FR-007).
- "ir a" toward the room the player is already in: the trip ends as arrived, with no time consumed (US6-10).
- "ir a" toward an unexplored room: rejected, no time consumed, recorded in the log only as a comment, never as a move (FR-016, FR-024).
- The player has the key of a door the map remembers as closed: the trip does not open it (FR-021).
- The route becomes unavailable after the first step: the trip stops, and the time already consumed by the steps taken stays consumed (FR-022).
- A scroll read after a trip reverts only its last step (FR-025).
- The game is saved and loaded in the middle of the fog: knowledge is restored exactly (FR-012).
- Replays and benchmarks with the same seed produce the same knowledge (FR-014).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: From the player's point of view every room MUST be in exactly one of three states: explored, sighted or unknown. A room becomes explored when the player enters it at least once.
- **FR-002**: The starting room MUST be explored from time 0.
- **FR-003**: For an explored room the player MUST know its name, its exits, the cost of each exit (spec 001) and the state of its doors as of the last observation (FR-006, FR-007); a door never observed is unobserved, and the map holds no state for it.
- **FR-004**: A room that is not explored and is the destination of an exit of an explored room MUST be sighted. For a sighted room the player MUST know only that a room exists behind that exit.
- **FR-005**: A room that is neither explored nor sighted MUST be unknown: the player MUST know nothing about it.
- **FR-006**: The player MUST observe a door when they are in either of the two rooms it connects. The observation MUST be continuous: while the player is in one of those rooms, the map MUST hold the door's real current state, including a change that happens while the player stays there.
- **FR-007**: The player's map MUST remember the state of each door as it was at the last observation, even if the real door has changed since, until the player observes it again.
- **FR-008**: While the torch is lit, entering a room MUST also explore all of its neighbors, through any exit, open or closed.
- **FR-009**: Exploring a neighbor through the torch MUST reveal its name and its exits only; it MUST NOT reveal its contents and MUST NOT activate its enemies or traps. The player MUST NOT observe the other doors of such a neighbor: they stay unobserved until FR-006 applies to them. Only the door that joins the room entered to that neighbor is observed.
- **FR-010**: Everything the view shows about the crypt and everything the "ir a" command uses MUST be derived only from the player's knowledge (FR-001 to FR-009).
- **FR-011**: The full crypt skeleton downloaded by the game is infrastructure and MUST NOT count as the player's knowledge.
- **FR-012**: The player's knowledge MUST be game state: it MUST be saved in the save file and restored when the game is loaded.
- **FR-013**: The rollback scroll MUST revert the player's knowledge together with the rest of the game state: rooms explored, rooms sighted and door observations made by the reverted action, including those made by the lit torch, return to their previous state.
- **FR-014**: The player's knowledge MUST be part of the timeline: with the same crypt, seed and sequence of actions, games MUST always produce the same knowledge at every moment, including in replay and benchmark modes.
- **FR-015**: The interface MUST offer a command that shows the known map: the explored rooms, their exits and the sighted rooms. Unknown rooms MUST NOT appear. The command MUST consume no time.
- **FR-016**: The "ir a" command MUST take the player to an explored room, named by its id as shown in the known map (FR-015). An id that matches no explored room is a room that is not explored. If the given room is not explored, the command MUST be rejected and MUST consume no time. A rejected order MUST be recorded in the game log as a comment (FR-024).
- **FR-017**: The route of "ir a" MUST use only explored rooms and only exits that the map remembers as open (never closed or unobserved ones).
- **FR-018**: The route MUST minimize the sum of the costs of the exits crossed (spec 001). Ties MUST be broken as for the hunter in spec 002 (FR-007 of that spec): the first step goes toward the neighbor with the lowest id among those on a route of minimum cost.
- **FR-019**: Each step of the trip MUST be a complete player action: it MUST consume time according to the cost of the exit crossed and the player's speed (spec 001), and the clock events MUST happen normally between steps.
- **FR-020**: The route MUST be recomputed before every step, with the knowledge at that moment, including door observations made during previous steps.
- **FR-021**: "ir a" MUST NOT open doors, even if the player has the key.
- **FR-022**: The trip MUST stop when: the player reaches the destination; the player enters a room containing enemies, active or asleep; the player takes damage; or the game ends (victory or death); or no known route exists any more; or the player reads a rollback scroll (FR-025). A recomputation that finds no route MUST stop the trip without consuming extra time. When a step meets more than one of these reasons at once, the view MUST show only the first that applies in the order given here (arrival, enemies in the room, damage, end of the game, no route, scroll).
- **FR-023**: The view MUST show the reason why the trip stopped.
- **FR-024**: In the game log each step of the trip MUST be recorded as an individual move, and the "ir a" order MUST also be recorded as a comment. A rejected order (FR-016) MUST be recorded as a comment too, with no move.
- **FR-025**: The rollback scroll MUST revert only the last step of the trip, and the trip MUST NOT continue after it: it stops with its own reason, rolled back by a scroll (FR-022, FR-023).
- **FR-026**: Computing one step of "ir a" with the full known map of the reference crypt MUST take at most 5 ms at the 99th percentile of the measured computations, measured locally and without network or rendering; the maximum MUST also be reported, for information, and is not a limit. The reference crypt is the one defined in spec 002 FR-017.
- **FR-027**: Any synthetic crypt used to measure FR-026 MUST be deterministic by seed: the same seed gives the same crypt.

### Key Entities

- **Room state (player's view)**: One of explored, sighted or unknown, as defined by FR-001, FR-004 and FR-005.
- **Player's knowledge**: The set of room states and remembered door states that the player has built up; it is game state (FR-012 to FR-014).
- **Remembered door state**: Whether a door was open or closed at its last observation, or unobserved if it never was; it may differ from the real state.
- **Torch**: An item that, while lit, makes entering a room also explore its neighbors.
- **Trip ("ir a")**: A sequence of ordinary player moves toward an explored destination, recomputed before every step and stopped by the conditions of FR-022.
- **Stop reason**: The cause shown to the player when a trip ends (arrival, enemies in the room, damage, end of the game, no known route, rolled back by a scroll).
- **Crypt skeleton**: The crypt structure downloaded in full at the start (spec 001); infrastructure, not knowledge.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the acceptance scenarios in this spec pass as automated tests, each citing its FR.
- **SC-002**: In every view of every replayed game, the information shown about the crypt is contained in the player's knowledge: 0 discrepancies.
- **SC-003**: No "ir a" trip in any replayed game uses an unexplored room, an exit the map remembers as closed, or opens a door: 0 occurrences.
- **SC-004**: An order of "ir a" toward an unexplored room consumes no time in 100% of cases.
- **SC-005**: Saving and loading a game gives identical knowledge in 100% of runs, and reading a scroll restores the knowledge to the state before the reverted action in 100% of runs, including after entries made with the torch lit.
- **SC-006**: Running the same crypt, seed and actions twice produces identical knowledge and identical game state in 100% of runs.
- **SC-007**: Computing one step of "ir a" with the full known map of the reference crypt takes at most 5 ms at the 99th percentile of the measured computations, and the maximum is reported.
- **SC-008**: Every trip that stops reports one of the reasons of FR-022 in the view in 100% of cases.
- **SC-009**: The lit torch never activates an enemy or a trap of a room that it only explores: 0 occurrences.

## Assumptions

- Exit costs, the duration formula and the destination-room-entered-at-start rule are those of spec 001; the hunter's route tie-break and the reference crypt are those of spec 002; this spec does not redefine them.
- The torch exploration of FR-008 happens when the player enters a room while the torch is lit; lighting the torch does not by itself explore the neighbors of the room the player is already in.
- Rooms explored by the torch count as explored for every purpose (FR-001, FR-003, FR-016, FR-017), and the destinations of their exits that are not explored become sighted.
- A trip that ends because the player is already in the destination consumes no time.
- The route and the trip use the player's speed and the exit costs known for the explored rooms (FR-003).
- A door is observed continuously while the player is in either room it connects (FR-006), so a door that changes while the player waits is seen at once.
- "Takes damage" in FR-022 covers any loss of life of the player during a step, whatever its cause (enemy attacks, traps).
- The view of the current room, the known map and the stop reason are shown by the interface in the same language and style as the existing views; their exact wording is not fixed by this spec.
- Reading the known map (FR-015) does not change the game state and is not recorded in the game log as a move.
- Hunters keep the whole-map knowledge defined in spec 002; the fog of war applies only to the player.
- The part-one rules for the activation of enemies, damage, traps and the rollback scroll apply as they are; this spec only adds what the scroll reverts (FR-013) and its effect on trips (FR-025).
