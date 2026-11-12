# Contract: current-room view under fog (service → controller → view)

## Input

`VistaConsola.mostrar_estado(estado)` receives the `EstadoVistaDTO` built by
`JuegoService.estado_vista()`. Each entry of `estado.salidas` is a `SalidaVistaDTO`; its
`nombre_destino` is **`None`** when the destination room is not explored (FR-004, FR-010). The door
state (`cerrada`) is the real one: the exits belong to the player's own room, which the player
observes continuously.

## Output

Only the exit line changes, and only for an exit toward a room that is not explored:

```text
Salidas:
  N -> Pasillo (abierta, costo 100)
  E -> sin explorar (cerrada, costo 300)
```

- Direction, door state and cost are printed as in spec 001.
- An exit toward an explored room prints the room name as before.
- Nothing else in the view changes: enemies, traps and objects are those of the current room.
- With the lit torch the neighbors are explored, so their names are shown.
- `VistaSilenciosa.mostrar_estado` stays a no-op.
