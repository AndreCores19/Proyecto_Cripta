from model.ruta_conocida import RutaConocida

#motivos por los que un viaje se detiene
LLEGADA = "llegada"
ENEMIGOS = "enemigos"
DANO = "dano"
FIN_PARTIDA = "fin_partida"
SIN_RUTA = "sin_ruta"
RETROCESO = "retroceso"


class Viaje:
    """Un viaje de «ir a»: un movimiento normal del jugador por paso, con la ruta recalculada en cada uno.

    `mover` es la función de movimiento del servicio, de modo que cada paso hace lo mismo que
    w/a/s/d (también baja el contenido de la sala en la que entra). `paso()` devuelve None mientras
    el viaje sigue, o el motivo por el que se detiene. Nada se guarda entre pasos.
    """

    def __init__(self, partida, destino, mover):
        self.partida = partida
        self.destino = destino
        self.mover = mover
        self.ruta = RutaConocida()
        self.direcciones = []                #las salidas que se cruzaron, en orden

    def paso(self):
        partida = self.partida
        if partida.terminada:
            return FIN_PARTIDA
        if partida.jugador.sala is self.destino:
            return LLEGADA
        salida, _ = self.ruta.siguiente_paso(partida, self.destino)
        if salida is None:
            return SIN_RUTA
        vida = partida.jugador.vida
        if not self.mover(salida.direccion):
            return SIN_RUTA                  #no debería pasar: la ruta solo usa salidas abiertas
        self.direcciones.append(salida.direccion)
        #después del paso, en el orden de FR-022: fin de la partida, llegada, enemigos, daño
        jugador = partida.jugador
        if partida.terminada:
            return FIN_PARTIDA
        if jugador.sala is self.destino:
            return LLEGADA
        for enemigo in partida.enemigos:
            if enemigo.sala is jugador.sala and enemigo.esta_vivo():
                return ENEMIGOS
        if jugador.vida < vida:
            return DANO
        return None
