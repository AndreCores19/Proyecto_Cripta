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

## Move and next action (FR-016; structures/agenda.py `Evento`, unchanged)

At the move's start time T the actor's room becomes `salida.destino` (traps, victory and trail
marks apply at T). Then the actor's next action is scheduled as an `Evento` with
`tiempo = T + intervalo(salida.costo, actor.velocidad)`, type `"accion"` and owner = actor.
When the actor's speed changes while that event is pending (FR-009):
`tiempo = nuevo_tiempo_por_velocidad(tiempo, reloj, vieja, nueva)`, through `reprogramar`.

## EstadoVistaDTO (dto/estado_vista_dto.py)

Built by `JuegoService.estado_vista()` from the game state; passed by `Controlador.jugar` to
`mostrar_estado`. The view never receives `Partida` for the room view. Plain lists, display only.

| Field | Type | From |
|---|---|---|
| id_sala, nombre_sala | int, str | `jugador.sala` |
| reloj | int | `partida.reloj` |
| jugador | `JugadorVistaDTO` | see below |
| salidas | list of `SalidaVistaDTO` | `jugador.sala.salidas`, in room order |
| enemigos | list of `EnemigoVistaDTO` | `partida.enemigos` where `enemigo.sala is sala` (same filter as today) |
| trampas | list of `TrampaVistaDTO` | `sala.trampas` |
| objetos | list of `ObjetoVistaDTO` | `sala.objetos` |
| bitacora | list of str | `partida.bitacora.obtener_todos()[-20:]` |

| DTO | Fields |
|---|---|
| JugadorVistaDTO | nombre, vida, vida_max, ataque, defensa, velocidad, arma (name or None), armadura (name or None), efectos (list of type str) |
| **SalidaVistaDTO** | direccion, nombre_destino, cerrada (bool), **costo** (int, already resolved: declared or 100) |
| EnemigoVistaDTO | nombre, id_enemigo, vida, vida_max, efectos (list of type str) |
| TrampaVistaDTO | nombre, dano, armada (bool) |
| ObjetoVistaDTO | id_instancia, nombre |

Later specs extend this DTO; this feature adds only `SalidaVistaDTO.costo` beyond today's output.

## Actors

Player and enemies (`errante`, `rastreador`, future hunters) all schedule moves through
`Partida._programar_movimiento(actor, salida)`.
