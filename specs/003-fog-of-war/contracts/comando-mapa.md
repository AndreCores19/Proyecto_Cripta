# Contract: command `mapa` (controller → service → view)

## Input

`mapa` typed in the console. No arguments.

## Service

`JuegoService.mapa_vista() -> MapaVistaDTO`. Reads only the player's knowledge: the explored rooms in
`Partida.conocidas`, sorted by id with the project's sort, each with its exits. For an exit, the
door state is `Partida.puerta_recordada(salida)`. Nothing is read from a room that is not explored.
It changes no state and consumes no time (FR-015).

## Output (`VistaConsola.mostrar_mapa`)

```text
Mapa conocido:
  Sala 1: Entrada  (tú estás aquí)
    N -> Sala 2: Pasillo (abierta, costo 100)
    E -> sin explorar (cerrada, costo 300)
  Sala 2: Pasillo
    S -> Sala 1: Entrada (abierta, costo 100)
    O -> sin explorar (sin observar, costo 100)
```

- Explored rooms are listed with their exits; an exit toward a sighted room reads `sin explorar` and
  shows no name or id.
- Unknown rooms do not appear at all (FR-005).
- A door state is `abierta`, `cerrada` or `sin observar`.
- `VistaSilenciosa.mostrar_mapa` is a no-op; with no view (`--replay`) the controller skips it.
