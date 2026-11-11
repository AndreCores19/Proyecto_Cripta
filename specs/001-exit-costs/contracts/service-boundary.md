# Contract: service boundary (service → controller, view, persistence)

`JuegoService` is the only class above the model that references `Partida` or any model object.
Everything it hands outward is a DTO from `dto/` or a plain value. Shapes are in
[data-model.md](../data-model.md).

| Caller | Call | Receives |
|---|---|---|
| Controlador.jugar | `servicio.terminada()` | bool |
| Controlador.jugar | `vista.mostrar_estado(servicio.estado_vista())` | `EstadoVistaDTO` |
| Controlador.jugar | `vista.mostrar_final(servicio.resumen_final())` | `ResumenFinalDTO` |
| Controlador.jugar | `persistencia.registrar_puntaje(resumen)` | `ResumenFinalDTO` |
| Controlador._cmd_guardar | `persistencia.guardar_partida(servicio.semilla(), comandos, nombre)` | int |
| Controlador._cmd_recoger | `servicio.objetos_en_sala()` | list of `ObjetoVistaDTO` |
| Controlador._elegir_enemigo | `servicio.enemigos_en_sala()`, then `servicio.atacar(id_enemigo)` | list of `EnemigoVistaDTO`, bool |
| Controlador._cmd_inventario | `vista.mostrar_inventario(servicio.inventario_vista())` | `InventarioVistaDTO` |
| Controlador._cmd_inventario | `vista.mostrar_inventario_ordenado(servicio.vista_ordenada(c), c)` | list of `ObjetoInventarioDTO` |
| Aplicacion._reejecutar | `servicio.terminada()` | bool |
| Aplicacion.reproducir (`--replay`) | `servicio.terminada()`, `imprimir_final_replay(servicio.resumen_final())` | bool, `ResumenFinalDTO` |

## Replay mode (`--replay`)

- No class from `view/` is instantiated. `reproducir` builds `Controlador(servicio, None, None, None, avisar=print)`.
- With `vista is None`, the controller sends `mostrar_mensaje` texts to `avisar` and skips every other display call.
- The end summary and the request report are printed by `imprimir_final_replay(resumen)` and `imprimir_reporte(solicitudes, presupuesto, aciertos, fallos)` in `adapters/salida_replay.py`.
- The text is identical to what `VistaReplay` printed in part one (golden files in `specs/001-exit-costs/salida-parte1/`).

Invariants (checked by `tests/test_frontera_servicio.py`):

- No value returned to the controller or passed to a view is an instance of a class from `model/`. DTO lists contain only DTOs.
- `controller/controlador.py` contains no `.partida` attribute access and imports nothing from `model/`.
- Printed output of `mostrar_final`, `mostrar_inventario` and `mostrar_inventario_ordenado` is identical to part one for the same state; `mostrar_estado` differs only by `, costo N` on exit lines.
- `view/vista_replay.py` no longer exists, and `VistaSilenciosa` inherits from nothing in `view/`.
