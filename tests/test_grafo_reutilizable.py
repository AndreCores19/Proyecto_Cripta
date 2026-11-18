"""El grafo aparte de `historia` se arma una vez por servicio y se limpia entre consultas (spec 005).

Tras muchas consultas (con cazadores, trampas, puertas y pergaminos), `limpio()` deja cada sala y cada
salida igual que un grafo recién armado del esqueleto, y la consulta responde lo mismo que con un grafo nuevo.
"""
from data.grafo_reutilizable import GrafoReutilizable
from linea_tiempo_apoyo import armar_mundo, jugar_semilla, resumen_plano
from model.linea_tiempo_logica import LineaTiempoPartida
from service.historia_service import HistoriaService
from data.fabrica_reproduccion import FabricaReproduccion
from service.juego_service import JuegoService

CAMPOS_SALA = ("id", "nombre", "conocimiento", "rastro", "busq_marca", "busq_dist")
CAMPOS_SALIDA = ("direccion", "cerrada", "memoria", "llave", "cierre_automatico", "costo_declarado")


def _foto(salas):
    foto = []
    for sala in salas.valores:
        foto.append((tuple(getattr(sala, c) for c in CAMPOS_SALA),
                     len(sala.objetos), len(sala.inactivos), len(sala.trampas),
                     tuple(e.origen.id for e in sala.entradas),
                     tuple((tuple(getattr(s, c) for c in CAMPOS_SALIDA), s.destino.id, s.opuesta is not None)
                           for s in sala.salidas)))
    return foto


def _juego(k=3):
    m = armar_mundo(11, salas=9, enemigos=6, cazadores=2, con_pergaminos=True, vida_jugador=10 ** 6)
    linea = LineaTiempoPartida()
    linea.iniciar(m.partida, m.constructor, k)
    servicio = JuegoService(m.partida, m.fabrica, linea_tiempo=linea)
    jugar_semilla(servicio, 5, 250, con_pergaminos=True)
    return m, servicio


def test_el_servicio_reusa_un_solo_grafo_y_limpio_lo_deja_como_el_esqueleto():
    m, servicio = _juego()
    historia = servicio._historia()
    assert servicio._historia() is historia                         #uno por servicio
    reloj = servicio.partida.reloj
    for t in range(0, reloj + 1, max(1, reloj // 60)):
        assert servicio.historia_por_instante(t).aceptada
    for k in range(1, len(servicio.linea_tiempo) + 1, 7):
        assert servicio.historia_por_accion(k).aceptada
    grafo = GrafoReutilizable(m.constructor)
    historia = HistoriaService(servicio.linea_tiempo,
                               lambda: FabricaReproduccion.desde(m.fabrica, grafo.limpio()).armar_mundo())
    for t in range(0, reloj + 1, max(1, reloj // 30)):              #ensucia el grafo con consultas reales
        assert historia.reproducir_en_instante(t).aceptada
    assert _foto(grafo.limpio()) == _foto(m.constructor())


def test_la_respuesta_con_el_grafo_reusado_es_la_misma_que_con_un_grafo_nuevo():
    m, servicio = _juego()
    nuevo = HistoriaService(servicio.linea_tiempo,
                            lambda: FabricaReproduccion.desde(m.fabrica, m.constructor()).armar_mundo())
    reloj = servicio.partida.reloj
    instantes = list(range(reloj, -1, -max(1, reloj // 80)))         #de atrás hacia adelante y de vuelta
    for t in instantes + instantes[::-1]:
        assert resumen_plano(servicio.historia_por_instante(t).resumen) == \
            resumen_plano(nuevo.consultar_instante(t).resumen), t
    for k in range(1, len(servicio.linea_tiempo) + 1, 5):
        assert resumen_plano(servicio.historia_por_accion(k).resumen) == \
            resumen_plano(nuevo.consultar_accion(k).resumen), k


def test_otra_linea_de_tiempo_arma_otro_grafo():
    m, servicio = _juego()
    antes = servicio._historia()
    servicio.linea_tiempo = LineaTiempoPartida()
    servicio.linea_tiempo.iniciar(servicio.partida, m.constructor, 5)
    assert servicio._historia() is not antes
