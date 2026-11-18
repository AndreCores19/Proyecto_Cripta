# Contract: in-game command `historia`

| Input | Result |
|---|---|
| `historia <t>` with integer 0 ≤ t ≤ current clock | summary of the state at instant t (FR-001, FR-002) |
| `historia #<k>` with 1 ≤ k ≤ actions taken | summary of the state just before action k (FR-003) |
| `historia` (no argument), `historia abc`, `historia -3`, `historia #0`, `historia #x`, `historia 1.5` | message with the accepted forms; nothing changes (FR-005) |
| `historia <t>` with t > current clock | rejected: "that instant has not happened" (FR-005) |
| `historia #<k>` with k = actions taken + 1, or a reverted action | rejected: "that action does not exist" (FR-003, FR-010) |

Guarantees (FR-006, FR-007, FR-008): no virtual time, no event executed, not a player action, not
added to `Controlador.comandos`, not written to `partida.log`, `Historial` untouched, no request to
the service. Accepted and rejected queries behave the same in all of these.

Flow: `Controlador.ejecutar` → returns before the command is appended to the log →
`JuegoService.historia_por_instante / historia_por_accion` → `RespuestaHistoriaDTO` →
`VistaConsola.mostrar_historia(dto)` (accepted) or `mostrar_mensaje(text)` (rejected).

Summary lines (wording not fixed by the spec; produced by `adapters/formato_historia.py` for both the
view and `--replay`): clock; room (id, name); player life / attack / defense / speed, weapon, armor;
active effects; inventory (one line per object, equipped marked); enemies in the room with
`vida/vida_max`; known map in the same layout as the `mapa` command.
