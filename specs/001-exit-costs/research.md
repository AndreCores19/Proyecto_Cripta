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

## R3. Mapping FR-016 to the engine

- **Decision**: no change to the order in `Partida.mover`. It already refreshes the origin trail, enters the destination room, runs traps and the victory check, and then schedules the next action. Only the scheduled cost changes, to `intervalo(salida.costo, velocidad)`.
- **Rationale**: FR-016 (added to the spec after analysis U1) makes this part-one behaviour a rule. Speed changes already rescale `actor.evento` through `nuevo_tiempo_por_velocidad` (`efectos_logica.py`), so FR-009 needs no new code.
- **Alternatives**: delay the room change until the end of the interval. It contradicts FR-016.

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

## R7. DTOs across the whole service boundary (analysis C1)

- **Decision**: the service returns DTOs or plain values for everything outside the model:
  - `EstadoVistaDTO` for the room view, including exit costs
  - `ResumenFinalDTO` for the end-of-game screens and the score table
  - `InventarioVistaDTO` / `ObjetoInventarioDTO` for the inventory views
  - `objetos_en_sala()` and `enemigos_en_sala()` for the controller
  - `atacar(id_enemigo)`, `terminada()` and `semilla()`
  
  The controller and `Aplicacion` (after construction) never read `Partida`.
- **Rationale**: Constitution III requires DTOs at every layer boundary and allows no exceptions. The second analysis found that the controller also reads the model (`servicio.partida`, room objects, `Enemigo` objects passed back to `atacar`), not just the views. The service already owns `Partida`, so it is the one place that can read it and hand out snapshots.
- **Alternatives**:
  - (a) Convert only the room view and record the rest as debt. Rejected: a recorded violation is still a violation (analysis C1, second pass).
  - (b) Have the controller build the DTOs. Rejected: the controller would still read the model.
  - (c) Keep `atacar(enemigo)` and hand the controller enemy objects wrapped in a DTO with a model reference. Rejected: a DTO holding a model reference leaks the model. The target is resolved by id inside the service instead.
  - (d) Amend the constitution to allow phased migration. Not needed, since the whole boundary is converted in this feature.

## R8. Replay without view classes (analysis C2)

- **Decision**:
  - `--replay` creates no class from `view/`. The controller runs with `vista=None` and an `avisar` function (`print`) for its messages.
  - The end summary and the request report are printed by plain functions in `adapters/salida_replay.py`, from `ResumenFinalDTO` and the four request counters.
  - `VistaReplay` is deleted, and `VistaSilenciosa` stops inheriting from it.
- **Rationale**: Constitution III forbids instantiating any view class in `--replay`. Plain functions outside `view/` are not view classes. Passing `print` keeps replay messages printed at the same moment as today, so the replay output is identical.
- **Alternatives**:
  - (a) Move `VistaReplay` to another folder. Rejected: it is still a view class under another name.
  - (b) Collect controller messages in a list and print them at the end. Rejected: the text would be the same, but the messages would no longer appear while the replay runs.
  - (c) Let the controller print directly. Rejected: the controller would take on view work.
  - (d) Keep `VistaSilenciosa` inheriting from `VistaReplay`. Rejected: that keeps `VistaReplay` alive only for inheritance, and `VistaSilenciosa` already overrides every method it uses.
