from model.reproduccion_logica import Reproductor


class ResultadoHistoria:
    """Lo que devuelve una consulta: aceptada o el motivo; la partida del mundo aparte y su reloj.

    (La Fase 6 lo convierte en `RespuestaHistoriaDTO` para el controlador y la vista.)"""

    def __init__(self, aceptada, motivo=None, partida=None, reloj=None):
        self.aceptada = aceptada
        self.motivo = motivo
        self.partida = partida                #Partida del mundo aparte (nunca la viva), o None
        self.reloj = reloj                    #el instante pedido, o el reloj de la decisión para `#k`


def _rechazo(motivo):
    return ResultadoHistoria(False, motivo)


class HistoriaService:
    """Consulta el pasado de una partida sin tocarla: valida, reproduce en un mundo aparte y responde."""

    def __init__(self, linea_tiempo, armar_mundo):
        self.linea_tiempo = linea_tiempo      #LineaTiempoPartida de la partida viva (solo lectura)
        self.armar_mundo = armar_mundo        #función que arma un Mundo nuevo, sin red, por consulta

    def reproducir_en_instante(self, t):
        if type(t) is not int or t < 0:
            return _rechazo("argumento_invalido")
        if t > self.linea_tiempo.reloj_final:
            return _rechazo("despues_del_reloj")
        partida = Reproductor(self.linea_tiempo, self.armar_mundo).en_instante(t)
        return ResultadoHistoria(True, None, partida, t)

    def reproducir_en_accion(self, k):
        if type(k) is not int or k < 1:
            return _rechazo("argumento_invalido")
        if k > len(self.linea_tiempo):
            return _rechazo("accion_inexistente")
        partida, reloj = Reproductor(self.linea_tiempo, self.armar_mundo).antes_de_la_accion(k)
        return ResultadoHistoria(True, None, partida, reloj)
