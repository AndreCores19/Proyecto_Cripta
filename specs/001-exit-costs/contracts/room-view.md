# Contract: room view (service → controller → view)

## Input

`VistaConsola.mostrar_estado(estado)` receives an `EstadoVistaDTO` built by
`JuegoService.estado_vista()` ([data-model.md](../data-model.md)). It never receives `Partida`.
`VistaSilenciosa.mostrar_estado(estado)` stays a no-op. In `--replay` there is no view: the controller has `vista=None` and skips `mostrar_estado` ([service-boundary.md](./service-boundary.md)).

## Output

Everything printed today stays identical. Only the exit lines gain the cost:

```text
Salidas:
  N -> Pasillo inundado (abierta, costo 300)
  S -> Entrada (cerrada, costo 100)
```

- `costo` is always shown: the declared value, or 100 (FR-010).
- Closed exits show their cost too.
