# Feature Specification: Crypt Solvability Verification

**Feature Branch**: `004-crypt-solvability`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Solvability verification of a crypt for the Cripta game. Why: the service publishes crypts that cannot be won. Before a game starts, the program must decide whether the crypt can be won and, if it cannot, explain exactly why, so the player is never sent into an impossible game without knowing it. What is checked: the verification uses the full crypt skeleton (rooms, exits, closed exits and the key each one requires) and the location of every key. The fog of war does not apply: this is infrastructure, not the player's knowledge. Key locations come from a new service query, which returns for each key the room where it is and, when an enemy carries it, the enemy; in that case the room is the one where that enemy starts and the key is in what that enemy drops. This query counts within the request budget of the crypt like every other request. Its answer is valid while the crypt version is the same, and a new version invalidates it. Assumptions of the verification: the player can cross any open exit, and any closed exit whose key the player already has; keys are never consumed; every enemy can be defeated, so a key an enemy drops is obtainable in the room where that enemy starts (also when the enemy wanders); traps and automatic door closings never block: a door that closes again can be opened again with the same key. Solvable: starting from the initial room, under those assumptions, the player can obtain the exit key and reach the exit room through a door that requires it. Result: if solvable, an order in which to obtain the keys such that every key appears after all the keys needed to reach it; if several orders are valid, any is accepted, but the result must be deterministic. If not solvable: the keys that cannot be obtained; the doors of the blocked frontier, each with the key it requires; where each of those keys is located; and, when a key is located behind doors that only it opens, directly or through a chain of keys, the concrete cycle, reported deterministically. The information for the report of a non-solvable crypt must come from the same pass over the crypt that decides solvability. Commands: before a game starts, the program runs the verification and the interface lets the player see the report; if the crypt is not solvable the game does not start, and the report is shown, unless the option --forzar is used. The option --verificar <crypt> runs only the verification and prints the report, without creating the view. Performance: verification of the largest published crypt takes at most 200 ms, measured locally without network or rendering; the verification must not repeat a full pass over the crypt each time a key is obtained, so its total cost grows approximately linearly with the number of rooms, exits and keys; synthetic crypts used for measuring are deterministic by seed, and --bench measures the naive alternative (a full pass per key) with synthetic crypts of many chained keys."

## Clarifications

### Session 2026-11-17

- Q: In `--offline` mode, where do the key locations come from, since the recorded offline package has no key locations? → A: The offline package is re-recorded to include the answer of the key query for each crypt, and the offline mode reads it like any other recorded answer (FR-006).
- Q: For a solvable crypt, is the order of keys shown at the start of a game, or only the verdict? → A: The verdict and the order of keys are always shown at the start of the game (FR-014).
- Q: Are the key locations saved between runs while the crypt version is unchanged, or is the query made again in every run? → A: They are saved on disk and reused while the version is the same; a new version discards them and the query is made again (FR-005).
- Q: When several keys can be obtained at the same moment, which one comes first in the order of keys? → A: The key with the lowest identifier, compared as text (FR-011).
- Q: What happens with a closed door whose key is not in the key list (or that names no key), and with an exit key that is not in the key list? → A: The crypt is not solvable for that reason: the door appears in the blocked frontier with the key it names (or none), and a key missing from the key list is listed as unobtainable with its location unknown; the same for the exit key (FR-012).
- Q: When a non-solvable crypt has more than one cycle of keys that block each other, does the report show all of them or only one? → A: All cycles, each starting at its lowest key id, sorted by that id (FR-012).
- Q: Must the report of a non-solvable crypt come from a single traversal with nothing afterwards, or may it use one extra linear sweep over only the part of the crypt the traversal did not reach? → A: One pass decides solvability, and one extra linear sweep over only the rooms that pass did not reach may produce the cycles; there is never a pass per key (FR-013).
- Q: What does the program do if the key query fails or the request budget is spent when the verification needs it? → A: It shows the usual communication error and neither starts the game nor gives a verdict; with `--forzar` it starts the game without a verdict (FR-022).
- Q: Which keys does the order of keys list in a solvable crypt: every key the player can obtain, or only the keys needed to reach the exit? → A: Every key the player can obtain, in the order they are taken (FR-009).

### Session 2026-11-17 (second round)

- Q: Do `--replay` and loading a saved game run the verification again, or only the first game of the program run? → A: Neither does: the verification runs once, when a game is started from the menu or the command line (FR-014).
- Q: What happens with the crypt of the offline package that the service no longer serves, when the package gets its key locations? → A: It is removed: the offline package holds only the crypts the service serves, each with its recorded key locations (FR-006).
- Q: If the key query lists the same key id twice, how is it treated? → A: Only one entry counts, the one with the lowest room id; the others are ignored (FR-002).
- Q: What exit status does `--verificar` give when it ends? → A: 0 when the crypt is solvable; 1 when it is not solvable or when a communication error ends the run (FR-017).

### Session 2026-11-17 (corrections after the analysis)

- Correction: FR-010 now says that the order and the report do not depend on the order in which the service lists the keys and the exits of each room; the rooms are taken sorted by id, as in part one, because the room vector of part one already refuses rooms that are not sorted.
- Correction: FR-012 (d) now says exactly what is reported when several unobtainable keys guard the same region: the lowest key id is the reported guard; the wording "doors that only it opens, directly or through a chain of keys" stays for the pure case.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The player is told before playing whether the crypt can be won (Priority: P1)

Before a game starts, the program decides whether the crypt can be won. A crypt that can be won
starts as always. A crypt that cannot be won does not start: the player sees the report that explains
why, so they are never sent into an impossible game without knowing it.

**Why this priority**: This is the reason for the feature; every other story refines the decision or
the report.

**Independent Test**: Build one solvable and one non-solvable crypt, start a game on each, and check
that the first starts and the second does not and shows the report.

**Acceptance Scenarios**:

1. **Given** a solvable crypt, **When** the player starts a game on it, **Then** the verification runs first, the verdict and the order of keys are shown, and the game starts. *(FR-014, FR-008)*
2. **Given** a non-solvable crypt and no `--forzar` option, **When** the player starts a game on it, **Then** the game does not start and the report is shown. *(FR-015)*
3. **Given** the player's fog of war, **When** the verification runs, **Then** it uses the whole crypt as downloaded, and what the player has or has not explored changes nothing. *(FR-001)*

---

### User Story 2 - A solvable crypt gives a valid and repeatable order of keys (Priority: P1)

For a crypt that can be won, the result is an order in which to obtain the keys. Every key appears
after all the keys needed to reach it. If several orders are valid, any is accepted, but the same
crypt always gives the same one.

**Why this priority**: The order is the proof that the crypt can be won, and a result that changed
from one run to the next could not be tested or compared.

**Independent Test**: Build a crypt with chained keys (the second key is behind a door that the first
opens, and so on), verify it, and check that the order respects every dependency; verify the same
crypt again with its keys and the exits of its rooms listed in a different order and check that the order is the same.

**Acceptance Scenarios**:

1. **Given** a solvable crypt with chained keys, **When** it is verified, **Then** the result is an order of keys in which every key appears after all the keys needed to reach it. *(FR-008, FR-009)*
2. **Given** a crypt with several valid orders of obtaining keys, **When** it is verified twice, **Then** both runs give the same order, and among keys obtainable at the same moment the one with the lowest identifier comes first. *(FR-010, FR-011)*
3. **Given** the same crypt delivered by the service with its keys and the exits of its rooms listed in a different order, **When** it is verified, **Then** the order of keys is the same. *(FR-010)*

---

### User Story 3 - A non-solvable crypt is explained exactly (Priority: P1)

For a crypt that cannot be won, the report says why: which keys cannot be obtained, which closed
doors block the region the player can reach and which key each one needs, where each of those keys is
located and, when a key is behind doors that only it opens, directly or through a chain of keys, the
concrete cycle.

**Why this priority**: Explicitly required; a bare "cannot be won" would leave the player with no way
to judge or report the problem.

**Independent Test**: Build a non-solvable crypt with a known blocked frontier and a known cycle and
check that the report lists exactly those keys, doors, locations and cycle, and that two runs print the
same report.

**Acceptance Scenarios**:

1. **Given** a crypt in which the exit key is behind the only door that it opens itself, **When** it is verified, **Then** the crypt is not solvable and the report points out the cycle. *(FR-012, FR-008)*
2. **Given** a non-solvable crypt, **When** it is verified, **Then** the report lists the keys that cannot be obtained, the closed doors adjacent to the region the player can reach, each with the key it requires, and where each of those keys is located. *(FR-012)*
3. **Given** a key located behind doors that only it opens through a chain of keys, **When** the crypt is verified, **Then** the report gives the concrete cycle (and every other cycle, each starting at its lowest key id and sorted by that id), and two runs give the same cycles. *(FR-012, FR-010)*
4. **Given** a non-solvable crypt, **When** the report is built, **Then** its information comes from the same pass that decided solvability (plus, for the cycles, one linear sweep over only the rooms that pass did not reach), without an extra pass per key. *(FR-013)*

---

### User Story 4 - Keys carried by enemies are placed where the enemy starts (Priority: P1)

A key that an enemy drops is obtainable in the room where that enemy starts, even if the enemy
wanders afterwards, because every enemy can be defeated.

**Why this priority**: Part of the definition of solvable; a wrong location would make the verdict
wrong in both directions.

**Independent Test**: Build a crypt where the key is in what a wandering enemy drops and check that
the verification treats the key as obtainable in the enemy's initial room.

**Acceptance Scenarios**:

1. **Given** a key in what a wandering enemy drops, **When** the crypt is verified, **Then** the verification places the key in the enemy's initial room. *(FR-003)*
2. **Given** a key carried by an enemy whose initial room the player cannot reach, **When** the crypt is verified, **Then** that key is not obtainable and is reported with its location. *(FR-003, FR-012)*

---

### User Story 5 - The player can start anyway with `--forzar` (Priority: P2)

A player who wants to play a non-solvable crypt can do so with the `--forzar` option. The report is
still produced.

**Why this priority**: The refusal is the default protection; the option gives the player the last
word and is simple once the verification exists.

**Independent Test**: Start a game on a non-solvable crypt with `--forzar` and check that it starts.

**Acceptance Scenarios**:

1. **Given** a non-solvable crypt and the `--forzar` option, **When** the player starts a game on it, **Then** the game starts. *(FR-016)*

---

### User Story 6 - The crypt can be verified without playing (Priority: P2)

With `--verificar <crypt>` the program runs only the verification and prints the report, without
creating the view and without starting a game.

**Why this priority**: Lets the course staff and the player check any published crypt at once.

**Independent Test**: Run `--verificar` on a solvable and on a non-solvable crypt and check that the
report is printed, no game is started and no class of the view is created.

**Acceptance Scenarios**:

1. **Given** a crypt, **When** the program is run with `--verificar <crypt>`, **Then** it runs only the verification, prints the report, and ends with status 0 if the crypt is solvable and 1 if it is not. *(FR-017)*
2. **Given** `--verificar`, **When** it runs, **Then** it creates no view. *(FR-017)*

---

### User Story 7 - Key locations come from the service within the request budget (Priority: P2)

The location of every key comes from a service query that counts within the request budget of the
crypt, like every other request. Its answer is kept, between runs, while the crypt version is the same, and a
new version invalidates it.

**Why this priority**: The budget is a standing rule of the project; the verification must not break it
or hide its cost.

**Independent Test**: Verify a crypt and check that the request count rises by the key query and stays
within the budget; change the crypt version and check that the answer is not reused.

**Acceptance Scenarios**:

1. **Given** a crypt with a request budget, **When** the key locations are obtained, **Then** the query is counted within that budget like any other request. *(FR-002, FR-004)*
2. **Given** a key-location answer obtained for one crypt version, **When** the crypt version changes, **Then** the answer is no longer valid and the query is made again. *(FR-005)*
3. **Given** a key-location answer saved from a previous run of the same crypt version, **When** the crypt is verified again, **Then** the saved answer is used and no key query is made. *(FR-005, FR-004)*
4. **Given** the key query fails or the request budget is spent, **When** the verification needs it, **Then** the communication error is shown, no verdict is given, and the game does not start unless `--forzar` is given. *(FR-022)*

---

### User Story 8 - Verification is fast and grows linearly (Priority: P2)

Verifying the largest published crypt takes at most 200 ms, and its cost grows approximately linearly
with the number of rooms, exits and keys, even when obtaining a key opens a whole region.

**Why this priority**: The behavior is correct without it, but a slow verification would delay every
game start.

**Independent Test**: Run the benchmark on synthetic crypts of many chained keys, with the verification
and with the naive alternative that makes a full pass per key, and compare.

**Acceptance Scenarios**:

1. **Given** the largest published crypt, **When** it is verified, locally and without network or rendering, **Then** the verification takes at most 200 ms. *(FR-018)*
2. **Given** synthetic crypts of many chained keys, **When** the benchmark runs, **Then** it reports the verification and the naive alternative (a full pass per key), and the verification grows approximately linearly. *(FR-019, FR-021)*
3. **Given** the same seed, **When** the synthetic crypts are built twice, **Then** they are identical. *(FR-020)*

---

### Edge Cases

- The exit key is behind the only door that it opens itself: not solvable, and the report points out the cycle (FR-012).
- A key is in what a wandering enemy drops: it is obtainable in the enemy's initial room, wherever the enemy goes afterwards (FR-003).
- A key opens a door that leads to a whole region with more keys: the verification does not repeat a full pass over the crypt for that key (FR-019).
- Several orders of keys are valid: the same crypt always gives the same one, whatever the order in which the service lists the keys and the exits of each room (FR-010, FR-011).
- A door closes again after the player passes: it can be opened again with the same key; it never blocks (FR-007).
- A trap lies on the way: it never blocks (FR-007).
- The crypt version changes: the key locations saved for the previous version are not used, and the query is made again (FR-005).
- A closed door names a key that the key list does not give, or names no key: it can never be opened; it is reported in the blocked frontier and the key, if named, as unobtainable with unknown location (FR-012).
- The key query fails or the budget is spent: the usual communication error is shown and there is no verdict; the game does not start unless `--forzar` is given (FR-022).
- The key query lists the same key id twice: only the entry with the lowest room id counts (FR-002).
- `--replay` or loading a saved game: the verification does not run again (FR-014).
- The crypt is not solvable and `--forzar` is given: the game starts (FR-016).
- The program is run with `--verificar`: no game starts and no view is created (FR-017).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The verification MUST use the full crypt as downloaded (rooms, exits, closed exits and the key each one requires) and the location of every key. The player's fog of war MUST NOT apply: this is infrastructure, not the player's knowledge.
- **FR-002**: The location of every key MUST come from a service query that returns, for each key, the room where it is and, when an enemy carries it, that enemy. If the same key id is listed more than once, only the entry with the lowest room id MUST count and the others MUST be ignored.
- **FR-003**: When an enemy carries a key, the location of that key MUST be the room where that enemy starts, and the key MUST be considered in what that enemy drops: it is obtainable in that room, also when the enemy wanders.
- **FR-004**: The key query MUST count within the request budget of the crypt like every other request.
- **FR-005**: The answer of the key query MUST be saved between runs and reused while the crypt version is the same, without making the query again; a new crypt version MUST invalidate it, and the query MUST then be made again.
- **FR-006**: In `--offline` mode the key locations MUST come from the recorded offline package, which MUST include the answer of the key query for each crypt, read like every other recorded answer; offline and online MUST give the same key locations for the same crypt version. The offline package MUST hold only crypts that the service serves, each with its recorded key locations; a crypt the service does not serve is not kept in it.
- **FR-007**: The verification MUST assume that: the player can cross any open exit, and any closed exit whose key the player already has; keys are never consumed; every enemy can be defeated, so a key an enemy drops is obtainable in the room where that enemy starts; and traps and automatic door closings never block, since a door that closes again can be opened again with the same key.
- **FR-008**: A crypt MUST be solvable if, starting from the initial room and under the assumptions of FR-007, the player can obtain the exit key and reach the exit room through a door that requires it. Otherwise it MUST be non-solvable.
- **FR-009**: For a solvable crypt the result MUST include an order in which to obtain the keys, listing every key the player can obtain, such that every key appears after all the keys needed to reach it.
- **FR-010**: The result MUST be deterministic: the same crypt MUST always give the same order of keys, and the same report, whatever the order in which the service lists the keys and the exits of each room. The rooms are taken sorted by id, as in part one. If several orders are valid, any is accepted.
- **FR-011**: When several keys can be obtained at the same moment, the order of keys MUST put first the key with the lowest identifier, compared as text.
- **FR-012**: For a non-solvable crypt the result MUST include: (a) the keys that cannot be obtained; (b) the doors of the blocked frontier, that is, the closed doors adjacent to the region the player can reach, each with the key it requires; (c) where each of those keys is located; and (d) when a key is located behind doors that only it opens, directly or through a chain of keys, every concrete cycle, reported deterministically: each cycle starting at its lowest key id, and the cycles sorted by that id. A cycle is made of keys each of which is located in a region that can only be entered through blocked frontier doors whose keys are themselves unobtainable; when several unobtainable keys guard the same region, the one with the lowest key id is the one reported as its guard. In the pure case, where a single key guards the region, the cycle is exactly a chain of keys located behind doors that only the next key opens. A closed door whose key is not in the key list, or that names no key, can never be opened: it MUST appear in the blocked frontier with the key it names (or none), and a key that the key list does not give MUST be reported as unobtainable with its location unknown; the same applies to the exit key.
- **FR-013**: The information for the report of a non-solvable crypt MUST come from the same pass over the crypt that decides solvability, not from extra passes per key. One additional linear sweep over only the part of the crypt that pass did not reach MAY be used to find the cycles; a pass per key MUST NOT be used.
- **FR-014**: Before a game starts, the program MUST run the verification, and the interface MUST let the player see the report. For a solvable crypt, the verdict and the order of keys MUST be shown at the start of the game. The verification MUST NOT run again for `--replay` or for loading a saved game inside a running session.
- **FR-015**: If the crypt is not solvable, the game MUST NOT start and the report MUST be shown, unless the `--forzar` option is used.
- **FR-016**: With the `--forzar` option, the game of a non-solvable crypt MUST start.
- **FR-017**: The option `--verificar <crypt>` MUST run only the verification and print the report, without creating the view and without starting a game. It MUST end with exit status 0 when the crypt is solvable, and with status 1 when it is not solvable or when a communication error ends the run.
- **FR-018**: Verifying the largest published crypt MUST take at most 200 ms, measured locally and without network or rendering.
- **FR-019**: The verification MUST NOT repeat a full pass over the crypt each time a key is obtained: its total cost MUST grow approximately linearly with the number of rooms, exits and keys.
- **FR-020**: Any synthetic crypt used for measuring MUST be deterministic by seed: the same seed gives the same crypt.
- **FR-021**: `--bench` MUST measure the naive alternative (a full pass per key) with synthetic crypts of many chained keys, and report it next to the verification.
- **FR-022**: If the key query fails or the request budget is spent when the verification needs it, the program MUST show the usual communication error and MUST NOT give a verdict. Without `--forzar` the game MUST NOT start; with `--forzar` the game MUST start without a verdict. `--verificar` MUST end with the error.

### Key Entities

- **Crypt skeleton**: The crypt structure downloaded in full at the start (spec 001): rooms, exits, closed exits and the key each one requires. Infrastructure, not the player's knowledge.
- **Key**: What opens one or more closed exits. Keys are never consumed.
- **Key location**: For each key, the room where it is and, when an enemy carries it, that enemy; in that case the room is the one where the enemy starts.
- **Order of keys**: A sequence in which to obtain the keys, where every key appears after all the keys needed to reach it.
- **Blocked frontier**: The closed doors adjacent to the region the player can reach, each with the key it requires.
- **Cycle**: A key located behind doors that only it opens, directly or through a chain of keys; when several keys guard the same region, the guard reported is the one with the lowest key id.
- **Verdict and report**: Solvable (with an order of keys) or non-solvable (with the unobtainable keys, the blocked frontier, the key locations and the cycle, if any).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the acceptance scenarios in this spec pass as automated tests, each citing its FR.
- **SC-002**: A non-solvable crypt never starts a game without `--forzar`, and the report is shown in 100% of those cases.
- **SC-003**: The same crypt gives the same order of keys and the same report in 100% of runs, whatever the order in which its keys and the exits of its rooms are listed.
- **SC-004**: In every non-solvable crypt of the tests, the report lists exactly the unobtainable keys, the blocked frontier, the key locations and, when it exists, the cycle: 0 omissions and 0 extra entries.
- **SC-005**: Verifying the largest published crypt takes at most 200 ms.
- **SC-006**: With synthetic crypts of many chained keys, the verification grows approximately linearly with the size of the crypt, and the benchmark reports it next to the naive alternative.
- **SC-007**: The key query is counted within the request budget of the crypt in 100% of runs that make it, and `--verificar` creates no view in 100% of runs.

## Assumptions

- Exits, closed exits and the key each one requires are those of the crypt skeleton defined in spec 001; this spec does not redefine them.
- The initial room and the exit room are those of the crypt (spec 001).
- The part-one rules for enemies and the items they drop apply as they are; this spec only uses where a key is.
- The report is shown by the interface in the same language and style as the existing views; its exact wording is not fixed by this spec.
- The largest published crypt is the one used for FR-018; until another is published, it is the largest of the crypts the service offers. Synthetic crypts replace it only in the benchmark (FR-020, FR-021).
- A non-solvable crypt is still a crypt the player may want to play; the verification warns and refuses by default (FR-015) but never changes the crypt.
