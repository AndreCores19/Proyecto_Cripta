# Cripta Constitution

## Core Principles

### I. Own Data Structures (NON-NEGOTIABLE)

For the evaluated problems — hunter pathfinding, route invalidation, known map, solvability,
timeline, event agenda, and undo history — all data structures MUST be hand-written.

In those problems, the following are FORBIDDEN as an index or cache:
- `dict` and `set`
- `heapq`, `bisect`, `collections`
- Any graph or pathfinding library

A plan that proposes any of the forbidden constructs is incorrect. The violation MUST be caught
during `/speckit-plan` review and checked again in `/speckit-analyze` before implementation begins.

**Rationale**: The course grades our structures, not Python's.

### II. Determinism

The same crypt, the same seed, and the same sequence of actions MUST always produce the same game
state. Every tie-breaking decision MUST use a fixed, documented rule (e.g., lowest id first). No
tie MAY be resolved by data insertion order or iteration order of any Python collection.

**Rationale**: Reproducibility is required for `--replay`, `--bench`, and `--verificar` to work
correctly and for consistent grading.

### III. Layered Architecture

The project MUST maintain its five-layer architecture: data → logic → service → controller → view,
with DTOs at every layer boundary.

Non-negotiable constraints:
- The model layer MUST NOT import, print, or reference anything in `view/` or `controller/`.
- `--replay`, `--bench`, and `--verificar` MUST NOT instantiate any view class.

**Rationale**: Layer separation enables isolated testing of the model and correct headless operation.

### IV. No Hardcoded Data

No crypt-specific data (room ids, key ids, enemy ids, or any constant derived from a specific
crypt) MAY appear in source code. All such data MUST come from the web service, or from data
recorded or cached from it (`--offline` mode and the persistent cache).

**Rationale**: Hardcoded data produces brittle tests and breaks compatibility with any crypt served
by the API.

### V. Network Budget and Versions

Every HTTP request to the service, including `/llaves`, counts toward `presupuesto_solicitudes` and
MUST be tracked and respected at all times. Persisted data from part one MUST be invalidated only
through the existing version check mechanism; files MUST NOT be deleted by hand to force a
re-download.

**Rationale**: The budget is part of the assignment specification. Manual cache invalidation
bypasses the version check and can silently introduce stale data.

### VI. Evidence-Backed Performance

No performance claim (e.g., "this is O(log n)" or "this approach is faster") is accepted without a
reproducible `--bench` measurement. Synthetic benchmark crypts MUST be deterministic by seed so
that measurements can be reproduced on any machine.

**Rationale**: Unverified claims lead to incorrect design decisions and cannot be defended in
grading.

### VII. Spec Before Code

Each capability's specification MUST be committed to Git before any implementation code for that
capability. If a spec is later found to be incorrect, the spec MUST be corrected in a dedicated
commit first; the code correction follows in a separate commit.

**Rationale**: Spec-first prevents implementation from drifting from requirements and provides a
clear, auditable history.

### VIII. What Goes Where

`spec.md` MUST contain only: rules, acceptance scenarios, and numbered functional requirements
(FR-xxx). It MUST NOT name data structures, classes, or implementation choices.

`plan.md` MUST contain only: data structures, design alternatives, complexity analysis, and
measurements. It MUST NOT introduce new rules.

**Rationale**: Mixing concerns between spec and plan makes it impossible to verify requirements
independently of implementation decisions.

### IX. Traceability

Every task in `tasks.md` MUST cite the FR it addresses. Every acceptance scenario MUST have an
automated test that cites its FR. Every case in Appendix B of the assignment MUST appear as an
acceptance scenario in some `spec.md`.

**Rationale**: Traceability ensures full assignment coverage and allows graders to verify that
every case is tested.

## Enforcement Checklist

This checklist MUST be applied during `/speckit-plan` and again during `/speckit-analyze` before
any implementation begins. A failing item blocks the task until resolved.

### Structures Gate (applies to all evaluated problems)
- [ ] No `dict` or `set` used as an index or cache in an evaluated structure.
- [ ] No `heapq`, `bisect`, or `collections` module used in an evaluated structure.
- [ ] No external graph or pathfinding library used.
- [ ] Hand-written structures cover all evaluated problems: hunter pathfinding, route invalidation,
      known map, solvability, timeline, event agenda, and undo history.

### Architecture Gate
- [ ] No file under `model/` or `structures/` imports from `view/` or `controller/`.
- [ ] `--replay`, `--bench`, and `--verificar` execution paths do not instantiate any view class.
- [ ] DTOs are present at all layer boundaries.

### Process Gate
- [ ] `spec.md` committed before corresponding implementation code.
- [ ] Every task in `tasks.md` cites its FR.
- [ ] Every acceptance scenario has a matching automated test citing its FR.

## Technology Stack

- **Language**: Python 3.11+
- **Allowed external libraries**: `requests` (HTTP communication), `pytest` (automated testing).
  All other external libraries require explicit approval and MUST NOT be used in the model layer.
- **Forbidden in evaluated structures**: `dict`/`set` as index or cache; `heapq`, `bisect`,
  `collections`; any graph or pathfinding library.
- **Benchmarking utilities** (measurement instrumentation only — never in the model):
  `time`, `gc`, `tracemalloc`, `copy`, `json`, `tempfile`.

## Governance

This constitution supersedes all other documented practices and informal agreements for the Cripta
project. Any amendment requires:

1. A written rationale explaining why the change is necessary.
2. A version bump following the policy below.
3. A dedicated Git commit for the constitution update, separate from any code or spec change.

**Versioning policy**:
- **MAJOR**: Backward-incompatible removal or redefinition of a principle.
- **MINOR**: Addition of a new principle or material expansion of guidance.
- **PATCH**: Clarifications, wording fixes, or non-semantic refinements.

**Compliance review**: Every `/speckit-plan` and `/speckit-analyze` run MUST apply the Enforcement
Checklist before proceeding to implementation.

**Version**: 1.0.0 | **Ratified**: 2026-11-09 | **Last Amended**: 2026-11-09
