"""Determinismo de la línea de tiempo (spec 005, T075).

La misma cripta, la misma semilla y los mismos comandos, jugados dos veces, dan líneas de tiempo idénticas
(los tres vectores, cada registro de cada punto de control y el libro de efectos omitidos) y las mismas
respuestas a una lista fija de consultas; también si en una de las dos corridas se consulta entre comando
y comando (consultar no cambia ni la partida viva ni lo que se anota).
"""
from array import array

import pytest

from controller.controlador import Controlador
from linea_tiempo_apoyo import VistaMuda, armar_mundo, jugar_semilla, resumen_plano
from model.linea_tiempo_logica import LineaTiempoPartida
from service.juego_service import JuegoService

MUNDO = dict(salas=9, enemigos=6, cazadores=2, con_pergaminos=True, vida_jugador=10 ** 6)


def _plano(valor):
    """Cualquier registro (objetos con __slots__ o __dict__, listas, tuplas, array) como tuplas comparables."""
    if valor is None or isinstance(valor, (bool, int, float, str)):
        return valor
    if isinstance(valor, (list, tuple)):
        return tuple(_plano(v) for v in valor)
    if isinstance(valor, array):
        return (valor.typecode, tuple(valor))
    campos = getattr(type(valor), "__slots__", None)
    if campos is None:
        campos = sorted(vars(valor))
    return (type(valor).__name__,) + tuple((c, _plano(getattr(valor, c))) for c in campos)


def plano_linea(linea_partida):
    """Todo lo que la línea de tiempo guarda (sin `comparaciones`, que cuenta el trabajo de las consultas)."""
    linea = linea_partida.linea
    return (linea.k, tuple(linea.relojes), tuple(linea.tipos), _plano(linea.argumentos),
            _plano(linea.puntos), _plano(linea.omitidos), linea.reloj_final, linea.reloj_decision_pendiente,
            linea.operaciones_retroceso, linea_partida.reloj_final)


def _servicio(k, semilla_mundo):
    m = armar_mundo(semilla_mundo, **MUNDO)
    linea = LineaTiempoPartida()
    linea.iniciar(m.partida, m.constructor, k)
    return JuegoService(m.partida, m.fabrica, linea_tiempo=linea)


def _respuestas(servicio):
    """Una lista fija de consultas: instantes repartidos (con bordes) y cada 3.ª acción."""
    reloj = servicio.partida.reloj
    instantes = sorted(set([0, 1, reloj - 1, reloj] + list(range(0, reloj + 1, max(1, reloj // 40)))))
    respuestas = []
    for t in instantes:
        if t < 0:
            continue
        r = servicio.historia_por_instante(t)
        respuestas.append(("t", t, r.aceptada, r.motivo, resumen_plano(r.resumen) if r.aceptada else None))
    for k in range(1, len(servicio.linea_tiempo) + 2, 3):
        r = servicio.historia_por_accion(k)
        respuestas.append(("#", k, r.aceptada, r.motivo, resumen_plano(r.resumen) if r.aceptada else None))
    return respuestas


def _jugar(comandos, k, semilla_mundo, consultar_entre=False):
    servicio = _servicio(k, semilla_mundo)
    controlador = Controlador(servicio, VistaMuda(), None, None)
    consultas = 0
    for i, comando in enumerate(comandos):
        if servicio.terminada():
            break
        controlador.ejecutar(comando)
        if consultar_entre:
            reloj = servicio.partida.reloj
            for t in (0, reloj // 3, reloj):
                assert servicio.historia_por_instante(t).aceptada
                consultas += 1
            if len(servicio.linea_tiempo) > 0:
                servicio.historia_por_accion(1 + i % len(servicio.linea_tiempo))
                consultas += 1
    return servicio, consultas


@pytest.mark.parametrize("k, semilla_mundo, semilla_juego", [(3, 11, 5), (10, 4, 8), (1, 7, 2)])
def test_la_misma_partida_dos_veces_da_la_misma_linea_de_tiempo_y_las_mismas_respuestas(k, semilla_mundo,
                                                                                        semilla_juego):
    """FR-009, SC-011 · la misma cripta, semilla y comandos dos veces: vectores, registros de los puntos de
    control y libro idénticos, y las mismas respuestas a una lista fija de consultas"""
    comandos = jugar_semilla(_servicio(k, semilla_mundo), semilla_juego, 220, con_pergaminos=True)
    a, _ = _jugar(comandos, k, semilla_mundo)
    b, _ = _jugar(comandos, k, semilla_mundo)
    assert a.partida.retrocesos > 0, "la partida debe leer algún pergamino"
    assert len(a.linea_tiempo.linea.omitidos) > 0
    assert plano_linea(a.linea_tiempo) == plano_linea(b.linea_tiempo)
    assert resumen_plano(a.partida) == resumen_plano(b.partida)
    assert _respuestas(a) == _respuestas(b)


@pytest.mark.parametrize("k, semilla_mundo, semilla_juego", [(3, 11, 5), (10, 4, 8)])
def test_consultar_entre_comando_y_comando_no_cambia_la_linea_de_tiempo_ni_las_respuestas(k, semilla_mundo,
                                                                                         semilla_juego):
    """FR-009, SC-011 · con y sin consultas intercaladas: la misma partida viva, la misma línea de tiempo y
    las mismas respuestas a la lista fija"""
    comandos = jugar_semilla(_servicio(k, semilla_mundo), semilla_juego, 220, con_pergaminos=True)
    sin, _ = _jugar(comandos, k, semilla_mundo)
    con, consultas = _jugar(comandos, k, semilla_mundo, consultar_entre=True)
    assert consultas > 400
    assert resumen_plano(sin.partida) == resumen_plano(con.partida)
    assert sin.partida.reloj == con.partida.reloj and sin.partida.azar.getstate() == con.partida.azar.getstate()
    assert plano_linea(sin.linea_tiempo) == plano_linea(con.linea_tiempo)
    assert _respuestas(sin) == _respuestas(con)


def test_el_plano_de_la_linea_ve_una_diferencia():
    """control: una sola diferencia en un punto de control cambia el plano"""
    s, _ = _jugar(jugar_semilla(_servicio(3, 11), 5, 40, con_pergaminos=True), 3, 11)
    antes = plano_linea(s.linea_tiempo)
    s.linea_tiempo.linea.puntos[-1].reloj += 1
    assert plano_linea(s.linea_tiempo) != antes
