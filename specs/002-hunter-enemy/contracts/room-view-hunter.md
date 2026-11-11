# Contract: hunter mark in the room view (service → controller → view)

## Input

`VistaConsola.mostrar_estado(estado)` receives the `EstadoVistaDTO` built by
`JuegoService.estado_vista()`. Each entry of `estado.enemigos` is an `EnemigoVistaDTO` with a new
boolean `cazador` (default `False`). The view never receives an `Enemigo`
([data-model.md](../data-model.md)).

## Output

Only the enemy line of a hunter changes. The mark `(cazador)` goes right after the name:

```text
Enemigos en la sala:
  Rata [e1] (Vida: 12/15)
  Lobo (cazador) [e3] (Vida: 20/20) [veneno]
```

- Name, id, life and effects are printed exactly as in part one (FR-016).
- An enemy that is not a hunter is printed exactly as before; a room without hunters is printed exactly as before (US6-2).
- `VistaSilenciosa.mostrar_estado` stays a no-op. In `--replay` and `--bench` no view is created.
