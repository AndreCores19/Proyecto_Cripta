"""El oráculo de la línea de tiempo (spec 005, SC-002).

Modo 1, sin pergaminos (Fase 4): se juega una partida con semilla anotando el resumen vivo antes de
cada acción del jugador; un segundo juego vivo, instrumentado, anota una foto tras cada evento. Luego
cada `#k` y cada instante t se consulta y se compara con lo que esos juegos mostraron.
Los modos 2 (con pergaminos) y 3 (tras guardar y cargar) los agregan las fases 5 y 8.
"""
import pytest

from controller.controlador import Controlador
from linea_tiempo_apoyo import (PartidaInstrumentada, VistaMuda, armar_mundo, con_reloj,
                                ejecutar_comandos, instantes_clave, jugar_semilla, oraculo,
                                registrar_vivo, resumen_plano)
from model.linea_tiempo_logica import LineaTiempoPartida
from service.juego_service import JuegoService

MUNDO = dict(salas=9, enemigos=6, cazadores=2)


def _juego_vivo(k, semilla_mundo, semilla_juego, n, vida, clase=None, con_linea=True, **mundo):
    parametros = dict(MUNDO)
    parametros.update(mundo)
    if clase is not None:
        parametros["clase_partida"] = clase
    m = armar_mundo(semilla_mundo, vida_jugador=vida, **parametros)
    if not con_linea:
        return m, JuegoService(m.partida, m.fabrica)
    linea = LineaTiempoPartida()
    linea.iniciar(m.partida, m.constructor, k)
    return m, JuegoService(m.partida, m.fabrica, linea_tiempo=linea)


def _consultar(servicio):
    def consultar(modo, valor):
        r = (servicio.historia_por_instante(valor) if modo == "t"
             else servicio.historia_por_accion(valor))
        assert r.aceptada, f"{modo} {valor} rechazada: {r.motivo}"
        return con_reloj(resumen_plano(r.partida), r.reloj)
    return consultar


def _correr(k, semilla_mundo, semilla_juego, n, vida, **mundo):
    m, servicio = _juego_vivo(k, semilla_mundo, semilla_juego, n, vida, **mundo)
    vivos = []
    comandos = jugar_semilla(servicio, semilla_juego, n, vivos=vivos)
    m2, servicio2 = _juego_vivo(k, semilla_mundo, semilla_juego, n, vida,
                                clase=PartidaInstrumentada, con_linea=False, **mundo)
    ejecutar_comandos(servicio2, comandos)
    assert resumen_plano(m2.partida) == resumen_plano(m.partida)
    return servicio, vivos, m2.partida.instantaneas


@pytest.mark.parametrize("k, acciones", [(1, 400), (3, 400), (7, 400), (100000, 150)])
def test_oraculo_modo_1_sin_pergaminos_con_cazadores_veneno_trampas_y_puertas(k, acciones):
    """SC-002, FR-001, FR-002, FR-003, FR-004 · `#k` y cada instante de una partida de 400 acciones
    (150 con K mayor que el juego, que reproduce todo desde el cero) dan lo que el juego vivo mostró"""
    servicio, vivos, instantaneas = _correr(k, 4, 11, acciones, vida=600)
    p = servicio.partida
    assert p.acciones_jugador >= min(acciones, 100)
    consultar = _consultar(servicio)
    paso = 97 if k < 100 else 331
    oraculo(servicio, vivos, instantaneas, consultar,
            instantes=instantes_clave(vivos, instantaneas, p.reloj, paso))
    #los ingredientes del juego están: efectos activos y más de una sala conocida
    planos = [v[2] for v in vivos]
    assert any(plano[2][7] for plano in planos), "hubo un efecto activo (veneno o velocidad)"
    assert max(len(plano[5][1]) for plano in planos) >= 4


def test_oraculo_modo_1_con_una_muerte():
    """SC-002, FR-002 · un juego que termina con la muerte del jugador: cada instante hasta el final coincide"""
    servicio, vivos, instantaneas = _correr(3, 4, 23, 400, vida=90)
    p = servicio.partida
    assert p.terminada and not p.victoria
    oraculo(servicio, vivos, instantaneas, _consultar(servicio),
            instantes=instantes_clave(vivos, instantaneas, p.reloj, 53))
