# Contract: comment lines in the game log (controller → adapters)

## Format

After the `---` line of the log, any line whose first character is `#` is a **comment**. Format
version stays `CRIPTA-LOG 1`: logs written before this feature contain no such lines.

```text
# ir a 7
w
w
d
```

## Writing

`BitacoraPartida.comentar(texto)` writes `# <texto>` and flushes, like `anotar`. The controller calls
it for every `ir a` order, accepted or rejected (FR-024, clarification Q3). A rejected order leaves
only the comment: no move line follows.

## Reading

`LectorBitacora.leer` ignores comment lines: they never reach `Controlador.ejecutar`, so replay
re-executes only the moves. A comment line is also never stored in a saved game's command list.

## Compatibility

- Old logs read exactly as before.
- A log with comments read by the old reader would print "Comando no reconocido." for each comment
  line and reach the same final state.
