# Research: Terrain — Exit Costs

No NEEDS CLARIFICATION remained after `/speckit-clarify`. These notes record the design decisions taken while reading the existing code.

## R1. Where the cost lives

- **Decision**: `SalidaDTO.costo` (`None` when it isn't declared) → `Salida.costo_declarado` → property `Salida.costo` (declared value, or `COSTO_MOVER`).
- **Rationale**: the "not declared" vs "declared 100" distinction is needed for the one-sided rule (FR-005) and the conflict check (FR-013). Resolving the default in the model keeps the DTO a faithful copy of the JSON.
- **Alternatives**: resolve to 100 in the DTO. Rejected: a conflict between "declared 100" and "not declared" could no longer be told apart.

## R2. Sharing the cost across both sides

- **Decision**: `Salida.enlazar` copies a declared cost to the side that has none, in the same way it already shares `llave` and `cierre_automatico`. `RepositorioCripta.construir_salas` raises the existing "Puerta inconsistente" `ValueError` first if both sides declare different values.
- **Rationale**: it reuses the part-one door-linking point and its error, as the clarification asked.
- **Alternatives**: a separate validation pass. Rejected: it adds a new invalid-data rule, which the clarification excludes.

## R3. Which event represents "crossing"

- **Decision**: the engine moves the actor instantly and schedules its next action `intervalo(salida.costo, velocidad)` later. That pending event is the crossing.
- **Rationale**: this matches part one, where moves scheduled `COSTO_MOVER`. Speed changes already rescale `actor.evento` through `nuevo_tiempo_por_velocidad` (`efectos_logica.py`), so FR-009 needs no new code.
- **Alternatives**: delay the room change until the end of the interval. Rejected: it changes trap, victory and tracker-trail timing from part one, beyond what the spec asks.

## R4. Enemy moves

- **Decision**: in the enemy turn, schedule `intervalo(salida.costo, velocidad)` when `salida is not None`, and `COSTO_ESPERAR` otherwise.
- **Rationale**: today both cases schedule `COSTO_ESPERAR` (100), which is numerically the part-one move cost. The decision code (`_decidir_errante`, `_decidir_rastreador`) is untouched (FR-008). Hunters do not exist yet; the hunter feature must use the same `_programar_movimiento`.

## R5. Invalidating part-one data

- **Decision**: no new mechanism.
- **Rationale**: the skeleton is not persisted. It is re-read on every start through `pagina_esqueleto`, so costs are always fresh. Saves (`validar_guardado`) and logs (`_versiones_coinciden`) compare `version_cripta`, and part-two crypts have new versions. The catalog cache is keyed by the catalog version and holds no exits. Offline recordings store the raw skeleton JSON, so newly recorded crypts include `costo`.

## R6. Agenda under variable costs

- **Decision**: keep the binary heap, pending the §Measurements of plan.md.
- **Rationale**: heap operations are O(log n) whatever the intervals are. Section 5.6 asks only to repeat the part-one comparison under the new load, so no new candidate is introduced.
- **Alternatives**: unsorted list (O(n) extract) and sorted list (O(n) insert), which were already measured and rejected in part one; they are re-measured with variable move costs and many actors.
