# Contract: command `ir a <id>` (controller → service → model)

## Input

`ir a <id_sala>` typed in the console. The words `ir` and `a` are required; `<id_sala>` is a room
id as shown by the known-map view (compared like enemy ids: text, case-insensitive).

## Service

`JuegoService.ir_a(id_sala) -> ViajeResultadoDTO`

1. Look the room up among `Partida.conocidas`. Not found, or `conocimiento != 2`: return
   `aceptado = False`, `motivo = "no_explorada"`, `pasos = 0`. No state is changed and no time is
   consumed (FR-016).
2. Otherwise build a `Viaje` and call `paso()` until it returns a reason. Each step is
   `JuegoService.mover(direccion)` (FR-019).
3. Return `aceptado = True`, the reason and the number of steps taken.

## Reasons (FR-022, FR-023)

| `motivo` | Meaning | Time consumed by the stop itself |
|---|---|---|
| `fin_partida` | The step ended the game (victory or death), even in the destination room | none |
| `llegada` | The player is in the destination (also when already there at the start) | none |
| `enemigos` | After the step there are living enemies in the player's room, active or asleep, whoever arrived there | none |
| `dano` | The player lost life during the step | none |
| `sin_ruta` | No known route exists before a step | none |
| `retroceso` | A scroll was read; the trip does not continue (FR-022, FR-025) | none |

When several reasons hold after the same step, the first in the order of this table is reported
(spec FR-022, clarification 2026-11-12).

## Controller

- Writes `# ir a <id>` to the game log before anything else (accepted or rejected, FR-024, Q3).
- For each step taken, writes the direction (`w`, `a`, `s`, `d`) as an individual move to the log and
  to the saved command list. The order itself is not added to the saved command list.
- Shows the reason with one message line (`Viaje detenido: <texto>`), or the rejection message.

## Guarantees

- Never opens a door (FR-021).
- The route is recomputed before every step (FR-020); nothing is kept between steps.
- Each step is one history frame, so a scroll read after the trip reverts only the last step (FR-025).
