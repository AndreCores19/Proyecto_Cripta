# Feature Specification: Timeline (consult the game at any past instant)

**Feature Branch**: `005-timeline`

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Timeline. The undo scroll of part one stays limited to 5 actions. The timeline is independent: it lets the player consult, without modifying the game, the state at any instant since the start. State at instant t: the state after executing every event with time <= t. If a player decision corresponds to t, it is the state just before taking it. In-game query: "historia <t>" or "historia #k" (the state just before player action number k) shows at least: clock, player's room, life and stats, inventory, active effects, the enemies in that room with their life, and the known map (spec 003) at that moment. The query consumes no virtual time, is not an action, is not written to partida.log, and changes neither the game state nor the undo history. A query for an instant after the current clock is rejected. Non-interactive query: "--replay partida.log --hasta <t>" replays the game up to t and prints the same summary without creating the view. If t is after the end of the game, it prints the final state and says the game ended earlier. Undo: actions reverted with a scroll stop existing in the timeline; the timeline describes the game as it ended up. Using a scroll trims the timeline without walking the whole history. Memory: full copies of the state (checkpoints) are allowed, but at most one every K player actions. K is set with --checkpoint-cada K; the default is chosen by the group and justified with measurements. A query may not need to apply or undo the changes of more than K player actions. Outside checkpoints, only the information needed to rebuild the changes is stored: total memory grows with the number of changes plus one checkpoint every K actions, never with actions times state size. Finding the checkpoint nearest to a requested instant must stay cheap in long games. If reconstruction re-simulates, the checkpoint includes the state of the random generator. Persistence: saving and loading a game keeps the full timeline. The binary save format changes; a part-one save file is reported as incompatible, never loaded silently. Performance: a historia query takes at most 50 ms on a game of at least 5000 player actions with the default K, measured locally with --bench, without network or rendering, using the same percentile convention as the existing event-cycle benchmark. --bench measures memory and query time for at least three values of K and for the alternative with no checkpoints, and repeats the part-one undo-history measurements under the new load. Synthetic games are deterministic by seed. --bench and --replay do not create the view."

## Clarifications

### Session 2026-11-18

- Q: What does the "5 actions" limit of the undo scroll mean for the timeline? → A: The scroll of part one keeps reverting at most the last 5 player actions. The timeline is a separate feature: it is not limited to 5 actions and covers every instant since the start of the game as it ended up. Consulting the timeline never uses up or changes the scroll's allowance.
- Q: What does "historia #k" show when k is the number of an action that has not happened yet, or that was reverted? → A: It is rejected, like an instant after the current clock. Player actions are numbered from 1 in the order they remain in the game as it ended up; a reverted action no longer has a number, and the numbers of the actions taken afterwards continue from the last surviving one.
- Q: Which instants can "historia <t>" ask for? → A: Any non-negative whole instant from 0 up to and including the current clock. A malformed or negative argument is rejected with a message and changes nothing.
- Q: Which percentile applies to the 50 ms limit? → A: The same convention as the existing event-cycle benchmark (spec 002): the 99th percentile of the measured queries is at most 50 ms, and the maximum is reported for information, not as a limit.
- Q: When a saved game is loaded with a `--checkpoint-cada K` value different from the K it was saved with, which K applies? → A: The saved K wins; the different option is ignored and the game says so with a notice. The K used by the game is part of what is saved.
- Q: Which queries are measured for the 50 ms limit? → A: Queries spread over the whole game, at instants chosen deterministically by seed, including the oldest and the most recent instants.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consult the state at a past instant (Priority: P1)

While playing, the player types "historia <t>" to see what the game looked like at instant t, or
"historia #k" to see the state just before their k-th action. The summary shows the clock, the
player's room, life and stats, inventory, active effects, the enemies in that room with their
life, and the known map (spec 003) as the player knew it at that moment. The game itself is not
touched.

**Why this priority**: It is the whole purpose of the feature; everything else supports or
protects it.

**Independent Test**: Play a short game with a few moves and fights, ask for several past
instants, and compare each summary with the state recorded when the game was at that instant.

**Acceptance Scenarios**:

1. **Given** a game in progress at clock T, **When** the player asks "historia t" with 0 <= t <= T, **Then** the summary shows the state after executing every event with time <= t. *(FR-001, FR-002, FR-004)*
2. **Given** a game in which an action number k has been taken, **When** the player asks "historia #k", **Then** the summary shows the state just before that action was taken. *(FR-003, FR-004)*
3. **Given** a game in progress, **When** the player asks "historia t" with t greater than the current clock, **Then** the query is rejected with a message and nothing changes. *(FR-005)*
4. **Given** several events scheduled at the same instant t, **When** the player asks "historia t", **Then** the summary shows the state after all of them have been executed. *(FR-001)*
5. **Given** a player decision that corresponds to instant t, **When** the player asks "historia t", **Then** the summary shows the state just before that decision is taken. *(FR-001)*
6. **Given** any past instant, **When** the summary is shown, **Then** it contains the clock, the player's room, life and stats, inventory, active effects, the enemies in that room with their life, and the known map as the player knew it at that moment. *(FR-004)*
7. **Given** a game, **When** the player asks "historia 0", **Then** the summary shows the initial state of the game. *(FR-002, FR-004)*
8. **Given** a malformed, negative or missing argument, **When** the player types "historia", **Then** a message explains the accepted forms and nothing changes. *(FR-005)*
9. **Given** a player decision that corresponds to instant t and other events scheduled at t that come after that decision in agenda order, **When** the player asks "historia t", **Then** the summary shows the state just before the decision and none of the effects of those later events. *(FR-001)*

---

### User Story 2 - Consulting never changes the game (Priority: P1)

A "historia" query is read-only. It takes no virtual time, is not a player action, is not
written to the game log (partida.log), and changes neither the game state nor the undo history.

**Why this priority**: A consultation that alters the game would break determinism, replay and
the undo scroll; the rule protects everything else.

**Independent Test**: Take a game, record its full state, its log and its undo allowance, run
several queries (accepted and rejected), and verify that all three are identical afterwards.

**Acceptance Scenarios**:

1. **Given** a game at clock T, **When** the player runs any "historia" query, **Then** the clock is still T and no event has been executed. *(FR-006)*
2. **Given** a game with a game log, **When** the player runs "historia" queries, **Then** partida.log is byte-for-byte the same as before. *(FR-007)*
3. **Given** a game in which the scroll can still revert N actions, **When** the player runs "historia" queries, **Then** the scroll can still revert the same N actions, in the same order. *(FR-008)*
4. **Given** a rejected query, **When** it ends, **Then** the game state, the log and the undo history are also unchanged. *(FR-005, FR-006, FR-007, FR-008)*
5. **Given** two games with the same crypt, seed and actions, one of them with "historia" queries in the middle, **When** both end, **Then** their final states are identical. *(FR-006, FR-009)*

---

### User Story 3 - The timeline follows the game as it ended up (Priority: P1)

When the player reads the scroll and reverts actions, those actions stop existing in the
timeline. A query after a scroll shows the game as it ended up, never the reverted actions. The
scroll of part one stays limited to 5 actions; the timeline is independent of that limit.

**Why this priority**: A timeline that showed reverted actions would describe a game that never
happened.

**Independent Test**: Take several actions, read a scroll, then query instants that fall in and
after the reverted span and check that none of the reverted actions appears.

**Acceptance Scenarios**:

1. **Given** a game in which the player took actions and then read a scroll that reverted some of them, **When** the player asks "historia" for any instant, **Then** the summary does not show any effect of the reverted actions. *(FR-010)*
2. **Given** the same game, **When** the player asks "historia t" for an instant later than the clock after the scroll, **Then** the query is rejected. *(FR-005, FR-010)*
3. **Given** the same game, **When** the player takes new actions after the scroll and then asks about the instants they cover, **Then** the summary shows the new actions, not the reverted ones. *(FR-010)*
4. **Given** a reverted action, **When** the player asks "historia #k" with k beyond the number of surviving actions, **Then** the query is rejected. *(FR-003, FR-010)*
5. **Given** a long game with thousands of actions, **When** the player reads a scroll, **Then** the timeline is trimmed without walking the whole history: the work done depends on what the scroll reverts, not on the length of the game. *(FR-011)*
6. **Given** the scroll limit of 5 actions of part one, **When** the timeline is in use, **Then** the scroll still reverts at most 5 actions and the timeline can be asked about any instant since the start. *(FR-012)*

---

### User Story 4 - Replay up to an instant without the view (Priority: P2)

From the command line, "--replay partida.log --hasta <t>" replays a recorded game up to instant
t and prints the same summary, without creating the view. If t is after the end of the game, it
prints the final state and says that the game ended earlier.

**Why this priority**: It lets the group and the graders check the timeline on recorded games,
headless and repeatable.

**Independent Test**: Replay a recorded game with a value of t inside the game and with a value
after its end; check the summary of the first against the in-game query and that the second shows
the final state with the notice.

**Acceptance Scenarios**:

1. **Given** a recorded game, **When** it is replayed with "--hasta t" and t is inside the game, **Then** the summary printed is the same as the one "historia t" shows in the game. *(FR-013, FR-014)*
2. **Given** a recorded game that ended at instant E, **When** it is replayed with "--hasta t" and t > E, **Then** the final state is printed and the output says that the game ended earlier. *(FR-015)*
3. **Given** the "--replay ... --hasta" execution, **When** it runs, **Then** no view is created. *(FR-016)*
4. **Given** "--hasta" with a malformed or negative value, **When** the command runs, **Then** it reports the error and prints no state. *(FR-013)*
5. **Given** a recorded game with scroll readings, **When** it is replayed with "--hasta t", **Then** the summary matches the game as it ended up, not the reverted actions. *(FR-010, FR-014)*

---

### User Story 5 - The timeline is saved and loaded (Priority: P1)

Saving a game keeps the full timeline, so a loaded game answers every query exactly as before the
save. The binary save format changes with this feature: a part-one save file is reported as
incompatible and is never loaded silently.

**Why this priority**: Without persistence, the timeline would be lost at every load, and loading
old files as if they were valid would corrupt the game.

**Independent Test**: Play, save, load, and compare the answers to the same queries; then try to
load a part-one save file and check that it is refused with a clear message.

**Acceptance Scenarios**:

1. **Given** a game with a long timeline, **When** it is saved and loaded, **Then** every "historia" query gives the same summary as before saving. *(FR-017)*
2. **Given** a game saved after reading a scroll, **When** it is loaded, **Then** the timeline still excludes the reverted actions. *(FR-010, FR-017)*
3. **Given** a save file written by part one, **When** the player tries to load it, **Then** the game reports that the file is incompatible and does not load it. *(FR-018)*
4. **Given** a part-one save file, **When** the load is refused, **Then** nothing is loaded partially, the current game (if any) is unchanged and the file is not modified or deleted. *(FR-018)*
5. **Given** a file that is damaged or is not a save file at all, **When** the player tries to load it, **Then** it is reported as unreadable and never loaded silently. *(FR-018)*

---

### User Story 6 - Memory stays proportional to the changes (Priority: P1)

The timeline stores full copies of the state (checkpoints) at most once every K player actions;
K is chosen with "--checkpoint-cada K" and has a default justified with measurements. Between
checkpoints only what is needed to rebuild the changes is kept. Memory grows with the number of
changes plus one checkpoint every K actions, never with actions times state size.

**Why this priority**: It is the trade-off the feature exists to demonstrate: long games stay
consultable without copying the whole state at every action.

**Independent Test**: Run synthetic games of different lengths, with a fixed K, and check that
memory grows linearly with the number of changes plus the checkpoints; check that no query needs
more than K actions of changes.

**Acceptance Scenarios**:

1. **Given** a game, **When** it runs with "--checkpoint-cada K", **Then** at most one full copy of the state is kept per K player actions. *(FR-019)*
2. **Given** any past instant, **When** it is queried, **Then** the reconstruction applies or undoes the changes of at most K player actions starting from a stored full copy. *(FR-020)*
3. **Given** two synthetic games with the same crypt and seed, one twice as long as the other, **When** their memory is measured, **Then** it grows with the number of changes plus one checkpoint every K actions, not with actions times state size. *(FR-021)*
4. **Given** a game of thousands of actions, **When** a query asks for a distant instant, **Then** finding the nearest stored full copy stays cheap: it does not walk the history action by action. *(FR-022)*
5. **Given** that reconstruction needs to re-simulate part of the game, **When** a full copy is taken, **Then** it includes the state of the random generator, so the re-simulation gives the same result as the original game. *(FR-023)*
6. **Given** "--checkpoint-cada" without a value, with zero or with a negative or non-numeric value, **When** the game starts, **Then** it is refused with a message and nothing runs. *(FR-019)*
7. **Given** no "--checkpoint-cada" option, **When** the game starts, **Then** the default K is used, and that default is justified with the measurements of "--bench". *(FR-019, FR-026)*
8. **Given** a game saved with K1, **When** it is loaded with "--checkpoint-cada K2" and K2 differs from K1, **Then** the game keeps K1 and shows a notice that the option was ignored. *(FR-017, FR-019)*

---

### User Story 7 - A query is fast on long games (Priority: P2)

On a game of at least 5000 player actions with the default K, a "historia" query takes at most
50 ms at the 99th percentile of the measured queries, locally, with no network and no rendering.

**Why this priority**: Consulting must feel immediate even on very long games.

**Independent Test**: Run the benchmark on a deterministic synthetic game of at least 5000
actions and read the 99th percentile and the maximum of the query time.

**Acceptance Scenarios**:

1. **Given** a synthetic game of at least 5000 player actions and the default K, **When** the benchmark measures "historia" queries spread over the whole game, **Then** the 99th percentile is at most 50 ms and the maximum is reported. *(FR-024)*
2. **Given** the benchmark, **When** it runs, **Then** no network request is made and no view is created. *(FR-016, FR-024)*
3. **Given** the same seed, **When** the synthetic game is generated twice, **Then** both games are identical. *(FR-025)*

---

### User Story 8 - The benchmark compares K and justifies the default (Priority: P2)

"--bench" measures memory and query time for at least three values of K and for the alternative
with no checkpoints, and repeats the part-one undo-history measurements under the new load. The
default K is justified with these numbers.

**Why this priority**: The assignment grades the justification of the design decision, not only
that it works.

**Independent Test**: Run "--bench" and check that its report contains memory and query time for
three or more values of K and for the no-checkpoint alternative, plus the undo-history figures.

**Acceptance Scenarios**:

1. **Given** "--bench", **When** it finishes, **Then** the report shows memory and query time for at least three values of K. *(FR-026)*
2. **Given** "--bench", **When** it finishes, **Then** the report also shows memory and query time for the alternative with no checkpoints. *(FR-026)*
3. **Given** "--bench", **When** it finishes, **Then** the part-one undo-history measurements are repeated with the timeline active, and reported next to their part-one values. *(FR-027)*
4. **Given** the report, **When** it is read, **Then** the default K can be traced to the figures that justify it. *(FR-026)*
5. **Given** the same seed, **When** "--bench" is run twice, **Then** the synthetic games it uses are the same. *(FR-025)*

---

### Edge Cases

- "historia t" with t equal to the current clock shows the current state; it is accepted. (FR-001, FR-005)
- "historia #k" for the action about to be taken next (k one past the last taken) is rejected: that action has not happened. (FR-003)
- Two actions that resolve at the same instant: "historia t" at that instant shows the state after the events, and "historia #k" for the second of them shows the state just before it, which includes the effects of the first. (FR-001, FR-003)
- A game with no actions yet: only "historia 0" is meaningful; any later instant is rejected. (FR-005)
- A query on a game that has ended (player dead or won): it is accepted for any instant up to the end. (FR-002)
- A scroll read at the very start of the timeline, with fewer than 5 actions taken: the timeline is trimmed by only the actions actually reverted. (FR-010)
- Consecutive scrolls: each trims the timeline in turn, and the timeline always describes the game as it ended up. (FR-010, FR-011)
- A query for an instant that falls exactly on a checkpoint, and one that falls K actions after it: both give the same answer as a reconstruction from the start. (FR-020)
- K larger than the number of actions in the game, and K = 1: both work; the answers are the same, only memory and time change. (FR-019, FR-020)
- A save taken just after a scroll, or just after a query: the file does not record the query and the timeline is the same as in memory. (FR-007, FR-017)
- A part-one save file that happens to be empty or truncated: it is reported as unreadable or incompatible, never loaded. (FR-018)
- "--replay" of a log that the game itself did not write correctly: it reports the error as in earlier specs and prints no state. (FR-013)
- Queries do not appear in a replayed log, so "--replay" never has to re-execute them. (FR-007)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The state at instant t MUST be the state after executing every event with time <= t. When several events share the instant t, the state MUST include all of them. When a player decision corresponds to t, the state MUST be the one just before that decision is taken, so the events at t that come after that decision in agenda order are not included.
- **FR-002**: The timeline MUST be able to answer for every instant from 0 up to and including the current clock, since the start of the game.
- **FR-003**: Player actions MUST be numbered from 1 in the order they remain in the game as it ended up. "historia #k" MUST show the state just before player action number k. A k that does not correspond to an action that exists (zero, negative, not yet taken, or reverted) MUST be rejected.
- **FR-004**: Every summary MUST show at least: the clock; the player's room; the player's life and stats; the inventory; the active effects; the enemies in the player's room with their life; and the known map (spec 003) as the player knew it at that moment. The summary of a past instant MUST NOT show anything the player did not know at that instant.
- **FR-005**: The interface MUST offer the command "historia <t>" and "historia #k". A query for an instant after the current clock, or with a malformed or negative argument, MUST be rejected with a message explaining why, and MUST change nothing.
- **FR-006**: A "historia" query MUST NOT consume virtual time, MUST NOT be a player action, MUST NOT execute any event, and MUST NOT change the game state.
- **FR-007**: A "historia" query, accepted or rejected, MUST NOT be written to partida.log.
- **FR-008**: A "historia" query MUST NOT change the undo history of part one: the scroll MUST revert exactly the same actions as if the query had not been made.
- **FR-009**: The same crypt, seed and sequence of actions MUST always give the same timeline and the same answer to every query (constitution, principle II). Ties MUST be resolved by a fixed, documented rule.
- **FR-010**: Actions reverted with a scroll MUST stop existing in the timeline. After a scroll, every query MUST describe the game as it ended up and MUST NOT show any effect of the reverted actions. The numbering of FR-003 MUST continue from the last surviving action.
- **FR-011**: Reading a scroll MUST trim the timeline without walking the whole history: the work MUST depend on what the scroll reverts and not on the length of the game.
- **FR-012**: The scroll of part one MUST remain limited to the last 5 actions. The timeline MUST NOT be limited by that value, and its existence MUST NOT change what the scroll does.
- **FR-013**: The command line MUST accept "--replay partida.log --hasta <t>": it replays the game up to instant t and prints the same summary as FR-004. A malformed or negative t MUST be reported as an error and no state printed.
- **FR-014**: The summary printed by "--replay ... --hasta t" MUST be identical to the one "historia t" shows in a game with the same crypt, seed and actions.
- **FR-015**: If t is after the end of the replayed game, "--replay ... --hasta t" MUST print the final state and MUST say that the game ended earlier.
- **FR-016**: "--replay" and "--bench" MUST NOT create the view (constitution, principle III).
- **FR-017**: Saving a game MUST keep the full timeline, and loading it MUST restore it, so that every query gives the same answer as before saving. The K in use MUST be saved with the game; on loading, the saved K MUST apply and a different "--checkpoint-cada" value MUST be ignored with a notice to the player.
- **FR-018**: The binary save format MUST change with this feature. Loading a save file written by part one MUST be refused with a message saying that it is incompatible; nothing MUST be loaded, the current game MUST NOT change and the file MUST NOT be modified. A damaged or unrecognizable file MUST be reported as unreadable, never loaded silently.
- **FR-019**: The timeline MUST store full copies of the state (checkpoints) at most once every K player actions. K MUST be set with "--checkpoint-cada K" (a positive whole number; any other value MUST be refused) and MUST have a default chosen by the group and justified with the measurements of FR-026.
- **FR-020**: Answering any query MUST NOT require applying or undoing the changes of more than K player actions starting from a stored full copy.
- **FR-021**: Outside checkpoints, the timeline MUST store only the information needed to rebuild the changes. Total memory MUST grow with the number of changes plus one checkpoint every K actions, and MUST NOT grow with actions times state size.
- **FR-022**: Finding the stored full copy nearest to a requested instant MUST stay cheap in long games: the cost MUST NOT grow linearly with the number of actions.
- **FR-023**: If the reconstruction of a state re-simulates the game, each checkpoint MUST include the state of the random generator so that the re-simulation gives the same result as the original game.
- **FR-024**: A "historia" query MUST take at most 50 ms at the 99th percentile of the measured queries, on a game of at least 5000 player actions with the default K, measured locally with "--bench", without network and without rendering, using the same percentile convention as the existing event-cycle benchmark (spec 002, FR-017). The maximum MUST be reported for information.
- **FR-025**: Every synthetic game used by the measurements MUST be deterministic by seed: the same seed MUST give the same game (constitution, principle VI).
- **FR-026**: "--bench" MUST measure memory and query time for at least three values of K and for the alternative with no checkpoints, and MUST report them so that the default K of FR-019 can be justified from them.
- **FR-027**: "--bench" MUST repeat the part-one undo-history measurements with the timeline active and MUST report them next to the part-one values.
- **FR-028**: The data structures used for the timeline, its checkpoints and its lookups MUST comply with the constitution (principle I); this is checked in the plan and again in the analysis, not stated here.
- **FR-029**: The model MUST NOT depend on the view or the controller, and every layer boundary MUST use DTOs (constitution, principle III).

### Key Entities

- **Instant**: A point of virtual time, a non-negative whole number, from 0 up to the current clock.
- **Player action number**: The position (from 1) of a player action among those that remain in the game as it ended up.
- **State summary**: The set of facts shown for an instant: clock, room, life and stats, inventory, active effects, enemies in the room with their life, known map (FR-004).
- **Timeline**: The record of the game as it ended up, from which the state at any instant since the start can be rebuilt (FR-001, FR-002).
- **Checkpoint**: A full copy of the state taken at most once every K player actions (FR-019), with the state of the random generator when reconstruction re-simulates (FR-023).
- **Change**: The minimal information needed to rebuild the difference between two consecutive states, kept between checkpoints (FR-021).
- **Undo history**: The part-one record that lets the scroll revert up to 5 actions (FR-012); it is independent of the timeline.
- **Save file**: The binary file of a game, in the new format that includes the timeline; the part-one format is incompatible (FR-018).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the acceptance scenarios in this spec pass as automated tests, each citing its FR.
- **SC-002**: For every instant of every replayed test game, the summary of a query equals the state recorded when the game was at that instant: 0 discrepancies.
- **SC-003**: After any number of "historia" queries, accepted or rejected, the game state, partida.log and the undo history are identical to those of the same game without queries in 100% of runs.
- **SC-004**: After a scroll, no query shows any effect of a reverted action in 100% of runs.
- **SC-005**: Saving and loading a game gives the same answer to every query in 100% of runs; a part-one save file is refused with an incompatibility message in 100% of attempts and never loaded.
- **SC-006**: A "historia" query on a game of at least 5000 player actions, with the default K, takes at most 50 ms at the 99th percentile, and the maximum is reported.
- **SC-007**: Between two synthetic games of the same seed that differ only in length, memory grows with the number of changes plus one checkpoint every K actions, with no growth proportional to actions times state size, as shown by "--bench".
- **SC-008**: No query needs to apply or undo the changes of more than K player actions: 0 violations in the measured queries.
- **SC-009**: "--bench" reports memory and query time for at least three values of K, for the alternative with no checkpoints, and the part-one undo-history figures under the new load, and the default K is traceable to these figures.
- **SC-010**: "--replay ... --hasta t" with t after the end of the game prints the final state and the "ended earlier" notice in 100% of runs, with no view created.
- **SC-011**: Running the same crypt, seed and actions twice gives identical timelines and identical query answers in 100% of runs.

## Assumptions

- Virtual time, events, the event cycle and the 99th-percentile convention are those of specs 001 and 002; the known map is that of spec 003; the part-one rules of the scroll, saving and the game log apply as they are. This spec does not redefine them and only adds the timeline.
- The reference crypt and the way synthetic games are generated by seed are those of the existing benchmarks; synthetic games of at least 5000 player actions are generated for the measurements of FR-024 and FR-026.
- "Player action" means one command that changes the game and takes time; consulting commands (such as "historia", "mapa" and "inv") are not player actions and do not receive a number.
- The summary is shown in the same language and style as the existing views; its exact wording is not fixed by this spec.
- The "ended earlier" notice of FR-015 is also shown when t equals no event of the game but exceeds its last instant; a t inside the game is never reported as ended earlier.
- The part-one undo history may be re-measured with its existing benchmark scenarios; "the new load" means the same scenarios run with the timeline active (FR-027).
- Hunters, the fog of war and solvability keep the behavior defined in specs 002, 003 and 004; the timeline only observes them.
- The default K is decided by the group after the measurements of FR-026 and is recorded with its justification in the plan, not in this spec.
