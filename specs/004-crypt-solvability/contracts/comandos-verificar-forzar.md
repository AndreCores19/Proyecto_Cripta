# Contract: `--verificar` and `--forzar` (main → aplicacion)

## `--verificar <cripta>`

`python main.py --verificar cripta-03` (also with `--offline`).

1. Builds the client (HTTP, or offline with `--offline`) and calls `verificar_cripta(url, id_cripta, cliente)`.
2. `verificar_cripta` loads the crypt data and skeleton, loads the key locations (saved file or one query),
   runs the verification and prints the report with `imprimir_reporte_verificacion`, then one line with the
   requests made and the budget. It builds no catalog, no game and no view (FR-017, Constitution III).
3. The program ends. Exit status 0 when the crypt is solvable and 1 when it is not, so scripts can use it.
   (FR-017, clarification 2026-11-17)

A missing crypt id, or an id the service does not know, shows the usual communication error and ends with
status 1.

## Before a game (FR-014, FR-015, FR-016)

`python main.py [<cripta>] [--forzar]`:

1. After the crypt is loaded and before the name is asked, `Aplicacion.jugar(ruta_carga, forzar)` verifies and
   shows the verdict with the order of keys, or the report.
2. Solvable: the game starts as always.
3. Not solvable and no `--forzar`: the report is shown, the game does not start and the program ends.
4. Not solvable and `--forzar`: the report is shown, then the game starts.

## Key query fails or the budget is spent (FR-022)

The usual communication error is shown and there is no verdict. `Aplicacion.jugar` then ends without starting the
game, unless `--forzar` is given: then the game starts without a verdict. `--verificar` ends with the error and
status 1.

`--forzar` without `--verificar` and `--replay` has no effect on solvable crypts. `--replay` does not verify
(plan, point 6).
