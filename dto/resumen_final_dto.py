class ResumenFinalDTO:
    """Resumen del final de la partida; solo valores simples (FR-010, FR-014)."""

    def __init__(self, nombre_jugador, reloj, victoria, terminada, acciones,
                 enemigos_derrotados, bitacora):
        self.nombre_jugador = nombre_jugador
        self.reloj = reloj
        self.victoria = victoria
        self.terminada = terminada
        self.acciones = acciones
        self.enemigos_derrotados = enemigos_derrotados
        self.bitacora = bitacora
