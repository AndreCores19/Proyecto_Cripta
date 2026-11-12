from model.enemigo_logica import Enemigo
from model.sala_logica import Sala, Salida


def _enemigo(comportamiento, **extra):
    return Enemigo(1, "t", "N", 10, 10, 1, 1, 100, comportamiento, Sala(1, "A"), **extra)


def test_rango_se_guarda_y_por_defecto_es_cero():
    """FR-001 · Enemigo.rango."""
    assert _enemigo("cazador", rango=300).rango == 300
    assert _enemigo("cazador").rango == 0


def test_es_cazador_solo_para_cazador():
    """FR-001 · es_cazador()."""
    assert _enemigo("cazador").es_cazador() is True
    for otro in ("errante", "rastreador", "guardián"):
        assert _enemigo(otro).es_cazador() is False


# ---- Historia 5: el catálogo define al cazador ------------------------------

import random
import types
from pathlib import Path

from data.fabrica_modelo import FabricaModelo
from dto.ficha_dto import ficha_desde_json
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from tests.estado_sin_cazadores import resumen
from tests.mapas_cazador import cadena, decision_referencia, grilla

ANTES = Path(__file__).resolve().parent.parent / "specs" / "002-hunter-enemy" / "estado-sin-cazadores-antes.txt"


def _json_ficha(comportamiento="cazador", **extra):
    datos = {"id": "ent_lobo", "nombre": "Lobo", "clase": "enemigo", "vida_max": 20,
             "ataque": 5, "defensa": 1, "velocidad": 100, "comportamiento": comportamiento}
    datos.update(extra)
    return datos


def _crear(ficha, sala, id_instancia="h1"):
    instancia = types.SimpleNamespace(instancia=id_instancia, tipo="ent_lobo", vida=None)
    return FabricaModelo.crear_enemigo(None, instancia, ficha, sala)


def _partida(sala_jugador):
    jugador = Jugador(vida_max=10**6, ataque=10, defensa=10**6, velocidad=100,
                      inventario_max=10, sala=sala_jugador)
    return Partida(jugador, semilla=1)


def _aislar(partida, enemigo, reloj=1000):
    partida.activar_enemigo(enemigo)
    partida.agenda.cancelar(enemigo.evento)
    partida.reloj = reloj


def test_us5_1_la_ficha_con_rango_crea_un_cazador():
    """FR-001 · US5-1"""
    ficha = ficha_desde_json(_json_ficha(rango=400))
    assert ficha.rango == 400
    enemigo = _crear(ficha, Sala(1, "A"))
    assert enemigo.es_cazador() and enemigo.rango == 400


def test_us5_5_sin_rango_el_cazador_vale_cero():
    """FR-001, FR-002, FR-004 · US5-5: espera con el jugador a una salida y ataca si comparten sala."""
    ficha = ficha_desde_json(_json_ficha())
    assert ficha.rango == 0
    salas, _ = cadena([100])
    partida = _partida(salas[1])
    h = _crear(ficha, salas[0])
    assert h.rango == 0
    _aislar(partida, h)
    partida._actuar_enemigo(h)
    assert h.sala is salas[0]
    assert h.evento.tiempo == 1000 + 100
    partida.agenda.cancelar(h.evento)
    h.sala = salas[1]
    vida = partida.jugador.vida
    partida._actuar_enemigo(h)
    assert partida.jugador.vida < vida
    assert any("ataca" in linea for linea in partida.bitacora.obtener_todos())


def test_errante_con_rango_lo_conserva_pero_se_mueve_como_errante():
    """FR-013 · el rango no cambia la regla del errante."""
    resultados = []
    for rango in (0, 1000):
        a, b, c = Sala(1, "A"), Sala(2, "B"), Sala(3, "C")
        for x, dx, y, dy in ((a, "E", b, "O"), (a, "S", c, "N")):
            i, v = Salida(dx, y, costo=100), Salida(dy, x, costo=100)
            x.agregar_salida(i)
            y.agregar_salida(v)
            i.enlazar(v)
        partida = _partida(c)
        e = _crear(ficha_desde_json(_json_ficha("errante", rango=rango)), a)
        assert e.rango == rango and not e.es_cazador()
        _aislar(partida, e)
        esperada = random.Random(1).choice([s for s in a.salidas if not s.cerrada])
        partida._actuar_enemigo(e)
        assert e.sala is esperada.destino
        resultados.append(e.sala.id)
    assert resultados[0] == resultados[1]


def test_el_rango_sale_solo_de_la_ficha():
    """FR-015 · la fábrica no inventa valores: cada ficha trae el suyo."""
    for rango in (7, 123, 5000):
        assert _crear(ficha_desde_json(_json_ficha(rango=rango)), Sala(1, "A")).rango == rango


def test_us5_2_partidas_sin_cazadores_no_cambian():
    """FR-013 · US5-2 · SC-006: el estado final de las semillas 1, 2 y 3 es el guardado antes de los cambios."""
    partes = [f"--- semilla {s} ---\n{resumen(s)}" for s in (1, 2, 3)]
    assert "\n".join(partes) == ANTES.read_text(encoding="utf-8")


def test_us5_3_los_otros_comportamientos_siguen_su_regla():
    """FR-013 · US5-3: errante, rastreador y cazador deciden cada uno con su regla."""
    salas, _ = grilla(3, 3, 100)
    partida = _partida(salas[8])
    mk = lambda i, comp, sala, rango=0: Enemigo(i, "t", f"E{i}", 10, 10, 1, 0, 100, comp, sala, rango=rango)
    cazador = mk(1, "cazador", salas[0], 1000)
    errante = mk(2, "errante", salas[4])
    rastreador = mk(3, "rastreador", salas[2])
    for e in (cazador, errante, rastreador):
        _aislar(partida, e)
    salas[5].rastro = partida.reloj
    # lo que cada regla devuelve en este estado
    estado = partida.azar.getstate()
    esp_errante = partida._decidir_errante(errante)
    partida.azar.setstate(estado)
    esp_rastreador = partida._decidir_rastreador(rastreador)
    esp_cazador = decision_referencia(salas, salas[8], cazador)
    assert esp_rastreador is not None and esp_cazador is not None
    for e in (errante, rastreador, cazador):
        partida._actuar_enemigo(e)
    assert errante.sala is esp_errante.destino
    assert rastreador.sala is esp_rastreador.destino
    assert cazador.sala is esp_cazador.destino
