# Contract: verification report (service → view and adapters)

## Input

A `ReporteVerificacionDTO` ([data-model.md](../data-model.md)). The text is built by
`adapters/salida_verificacion.lineas_reporte(reporte)` (a list of lines); `VistaConsola.mostrar_verificacion`
and `imprimir_reporte_verificacion` (used by `--verificar`) print those lines, so the game and `--verificar`
show the same report. The adapter imports nothing from `model/` or `view/`.

## Solvable crypt (FR-014)

```text
Verificación de cripta-02: se puede ganar.
Orden de llaves:
  1. itm_llave_bronce
  2. itm_llave_negra
```

## Non-solvable crypt (FR-012)

```text
Verificación de cripta-X: NO se puede ganar.
Llaves que no se pueden conseguir:
  itm_llave_negra (sala 4)
  itm_llave_hierro (sala 16, la lleva el enemigo e-cripta-X-8)
Puertas de la frontera bloqueada:
  sala 3, E -> sala 4: exige itm_llave_negra
Ciclo:
  itm_llave_negra (sala 4) está tras la puerta de la sala 3, E, que exige itm_llave_negra
```

- Keys, doors and cycles are listed in a fixed order: keys by id, doors by `(room id, direction)`, cycles by
  the lowest key id of each, each cycle starting at that key (FR-010).
- A key whose location is unknown reads `(sin ubicación)`; a door with no key reads `no tiene llave`.
- Without a cycle the `Ciclo` section does not appear.
- Exact wording is not fixed by the spec (it says the same language and style as the existing views).
