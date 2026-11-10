# Contract: room view, exits block (output)

`VistaConsola.mostrar_estado` prints one line per exit of the current room:

```text
Salidas:
  N -> Pasillo inundado (abierta, costo 300)
  S -> Entrada (cerrada, costo 100)
```

- `costo` is always shown: the declared value, or 100 (FR-010).
- Closed exits show their cost too.
- `VistaSilenciosa` and `VistaReplay` are unchanged.
