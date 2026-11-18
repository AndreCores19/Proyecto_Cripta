"""DTO de la consulta `historia` (spec 005, FR-004, FR-029). Clases simples; no importa nada de model/.

Reutiliza las clases de la vista viva: `JugadorVistaDTO`, `ObjetoInventarioDTO`, `EnemigoVistaDTO` y
`MapaVistaDTO`, que se construyen con las mismas funciones de lectura que la partida viva.
"""

MOTIVOS = (None, "despues_del_reloj", "accion_inexistente", "argumento_invalido")


class ResumenHistoriaDTO:
    def __init__(self, reloj, id_sala, nombre_sala, jugador, inventario, enemigos, mapa):
        self.reloj = reloj                  # el instante pedido (t) o el reloj de la decisión (#k)
        self.id_sala = id_sala
        self.nombre_sala = nombre_sala
        self.jugador = jugador              # JugadorVistaDTO
        self.inventario = inventario        # lista de ObjetoInventarioDTO, en orden
        self.enemigos = enemigos            # lista de EnemigoVistaDTO (los de la sala del jugador)
        self.mapa = mapa                    # MapaVistaDTO: lo que el jugador conocía en ese instante


class RespuestaHistoriaDTO:
    def __init__(self, aceptada, motivo, resumen, termino_antes=False, reloj_final=None):
        self.aceptada = aceptada
        self.motivo = motivo                # uno de MOTIVOS
        self.resumen = resumen              # ResumenHistoriaDTO, o None si se rechazó
        self.termino_antes = termino_antes  # --replay --hasta después del final (FR-015)
        self.reloj_final = reloj_final
