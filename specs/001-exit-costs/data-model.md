# Data Model: Terrain — Exit Costs

## SalidaDTO (dto/salida_dto.py)

| Field | Type | Source | Notes |
|---|---|---|---|
| direccion | str | JSON key | unchanged |
| id_destino | int | `sala` | unchanged |
| cerrada | bool | `cerrada`, default False | unchanged |
| llave | str or None | `llave` | unchanged |
| cierre_automatico | int or None | `cierre_automatico` | unchanged |
| **costo** | int or None | `costo` | **new**; `None` = not declared. No range check (FR-001). |

## Salida (model/sala_logica.py)

| Field | Type | Notes |
|---|---|---|
| **costo_declarado** | int or None | new; copied from the DTO, possibly filled in by `enlazar` |
| **costo** (read-only) | int | new; `costo_declarado`, or `COSTO_MOVER` (100) when it is `None` (FR-002) |
| opuesta | Salida or None | unchanged; both sides end up with the same `costo` (FR-005) |

**Linking rules** (in `RepositorioCripta.construir_salas` → `Salida.enlazar`):

| Side A declared | Side B declared | Result |
|---|---|---|
| None | None | both 100 |
| x | None | both x |
| None | y | both y |
| x | x | both x |
| x | y, x ≠ y | `ValueError("Puerta inconsistente: …")`, the part-one error extended with the costs (FR-013) |

## Move event (structures/agenda.py `Evento`, unchanged)

`tiempo = reloj + intervalo(salida.costo, actor.velocidad)`, with type `"accion"` and owner = actor.
When the actor's speed changes while the event is pending:
`tiempo = nuevo_tiempo_por_velocidad(tiempo, reloj, vieja, nueva)`, through `reprogramar`.

## Actors

Player and enemies (`errante`, `rastreador`, future hunters) all schedule moves through
`Partida._programar_movimiento(actor, salida)`.
