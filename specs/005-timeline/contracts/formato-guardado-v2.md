# Contract: save file, format version 2 (FR-017, FR-018)

Little-endian, written with `struct` as in version 1. The layout of version 1 (header, room
contents, commands, room index) is kept. **The only change is that the fixed header gains K.** The
timeline is not stored: the file holds the commands and the K in use, and loading re-executes the
commands, which rebuilds the action records, the checkpoints and the ledger of skipped effects
(decision of 2026-11-18).

```text
Prefix        "<4sH"   magic "CRPT", version            (read first, alone)   [new split]
Header v2     seed u64, n_salas u32, n_comandos u32, off_indice u64, off_comandos u64,
              k u32 (new)
              then strings: id_cripta, version_cripta, version_catalogo
Rooms / commands / room index   unchanged from v1
```

Load rules:

1. Read the 6-byte prefix. Not `CRPT` -> "No es un archivo de guardado de Cripta". Version != 2 ->
   "Formato de guardado incompatible: el archivo es v<n> y este programa usa v2" (the existing
   message, existing exception `ErrorGuardado`). This happens before the rest of the header is read,
   so a short v1 file is reported as incompatible. Fewer than 6 bytes or any later short read ->
   "El archivo está truncado" (unreadable).
2. Nothing is loaded, the running game is not changed, the file is not opened for writing, moved or
   deleted (FR-018). `Aplicacion.validar_guardado` already runs before any state change.
3. The live game is rebuilt by re-executing the saved commands, as in part one, with the timeline
   recording on. Every `historia` answer is then the same as before the save (same commands, same
   code, determinism).
4. The saved K is the K of the game. A different `--checkpoint-cada` -> notice (see the CLI
   contract). `k` in the file must be a positive integer, otherwise the file is unreadable.

Save rules: the file does not record queries or the notice; a save right after a scroll or a query
is identical to one taken without the query (FR-007, edge cases). `controller.comandos`, which is
what is saved, never contains `historia`.

Tests: v1 file written by the part-one code (kept as a fixture, also a v1 file shorter than the v2
header), empty file, truncated v2, random bytes, `k` = 0, v2 round trip (same `historia` answers
before and after, including a game saved after a scroll and K != default), saved K wins over the
option.
