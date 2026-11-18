# Contract: DTOs of the timeline (FR-029)

Plain classes, simple values and lists, no import from `model/`; they follow the style of
`dto/estado_vista_dto.py` and `dto/mapa_vista_dto.py`, whose classes they reuse.

```text
ResumenHistoriaDTO(reloj, id_sala, nombre_sala, jugador, inventario, enemigos, mapa)
    jugador     : JugadorVistaDTO        (dto/estado_vista_dto.py)
    inventario  : [ObjetoInventarioDTO]  (dto/inventario_vista_dto.py)
    enemigos    : [EnemigoVistaDTO]      (enemies in the player's room, with life)
    mapa        : MapaVistaDTO           (dto/mapa_vista_dto.py)

RespuestaHistoriaDTO(aceptada, motivo, resumen, termino_antes=False, reloj_final=None)
    motivo in {None, "despues_del_reloj", "accion_inexistente", "argumento_invalido"}
```

Boundaries:

| From → to | Carries |
|---|---|
| `HistoriaService` → `JuegoService` → `Controlador` | `RespuestaHistoriaDTO` |
| `Controlador` → `VistaConsola.mostrar_historia` | `ResumenHistoriaDTO` |
| `Aplicacion.reproducir` → `salida_replay.imprimir_historia` | `RespuestaHistoriaDTO` |

Rule: the summary contains nothing the player did not know at that instant (FR-004): the map is the
scratch world's own `conocimiento`/`memoria`, never the live game's.
