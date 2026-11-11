import pytest

from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.ruta_cazador import Busqueda, DecisorCazador
from model.sala_logica import Sala, Salida
from tests.mapas_cazador import cadena


def preparar(sala_jugador, sala_cazador, rango, velocidad=100, reloj=1000):
    """Partida aislada: el cazador sin turno propio salvo el que programe la llamada probada."""
    jugador = Jugador(vida_max=10**6, ataque=10, defensa=10**6, velocidad=100,
                      inventario_max=10, sala=sala_jugador)
    partida = Partida(jugador, semilla=1)
    h = Enemigo(1, "cazador", "Cazador", 10, 10, 5, 0, velocidad, "cazador",
                sala_cazador, rango=rango)
    partida.activar_enemigo(h)
    partida.agenda.cancelar(h.evento)
    partida.reloj = reloj
    return partida, h


def _marcas(salas, estampa):
    return [s.busq_marca == estampa for s in salas]


def _unir(x, dx, y, dy, costo):
    i, v = Salida(dx, y, costo=costo), Salida(dy, x, costo=costo)
    x.agregar_salida(i)
    y.agregar_salida(v)
    i.enlazar(v)
    return i, v


# ---- Busqueda -------------------------------------------------------------

def test_busqueda_no_llega_mas_alla_del_limite():
    """FR-018, FR-003 · con límite 200 se alcanzan 3 salas y la cuarta queda en -1."""
    salas, _ = cadena([100, 100, 100])
    e = Busqueda().calcular(salas[0], 200)
    assert _marcas(salas, e) == [True, True, True, False]
    assert salas[3].busq_marca == -1


def test_busqueda_incluye_distancia_igual_al_limite_y_excluye_la_mayor():
    """FR-003 · distancia 200 con límite 200 entra; 201 no."""
    b = Busqueda()
    salas, _ = cadena([100, 101])
    e = b.calcular(salas[0], 200)
    assert b.distancia(salas[1], e) == 100
    assert b.distancia(salas[2], e) is None
    salas2, _ = cadena([100, 100])
    e2 = b.calcular(salas2[0], 200)
    assert b.distancia(salas2[2], e2) == 200


def test_busqueda_no_cruza_salidas_cerradas():
    """FR-009 · una salida cerrada no se cruza."""
    salas, pares = cadena([100, 100])
    pares[0][0].cerrada = True
    pares[0][1].cerrada = True
    b = Busqueda()
    e = b.calcular(salas[2], 1000)
    assert b.distancia(salas[1], e) == 100
    assert b.distancia(salas[0], e) is None


def test_busqueda_salida_de_un_solo_sentido():
    """FR-003 · A→B sin vuelta: con el jugador en B, A está a su costo; con el jugador en A, B no llega."""
    a, b = Sala(1, "A"), Sala(2, "B")
    a.agregar_salida(Salida("E", b, costo=70))
    busq = Busqueda()
    e = busq.calcular(b, 1000)
    assert busq.distancia(a, e) == 70
    e = busq.calcular(a, 1000)
    assert busq.distancia(b, e) is None


def test_busqueda_estampas_distintas_y_ultima_estampa_compartida():
    """FR-009 · cada búsqueda trae estampa nueva; ultima_estampa es la más reciente aunque alternen objetos."""
    salas, _ = cadena([100, 100])
    b1, b2 = Busqueda(), Busqueda()
    e1 = b1.calcular(salas[0], 500)
    e2 = b2.calcular(salas[0], 500)
    e3 = b1.calcular(salas[0], 500)
    assert len({e1, e2, e3}) == 3
    assert Busqueda.ultima_estampa == e3


def test_busqueda_no_escribe_fuera_de_la_region_alcanzada():
    """FR-018 · las salas fuera de la región conservan busq_marca == -1 y busq_dist == 0."""
    salas, _ = cadena([100, 100, 100, 100])
    Busqueda().calcular(salas[0], 100)
    for s in salas[2:]:
        assert s.busq_marca == -1 and s.busq_dist == 0


# ---- Escenarios de la historia 1 ------------------------------------------

def test_us1_1_misma_sala_ataca():
    """FR-002 · US1-1"""
    salas, _ = cadena([100])
    partida, h = preparar(salas[0], salas[0], 300)
    vida = partida.jugador.vida
    partida._actuar_enemigo(h)
    assert any("ataca" in linea for linea in partida.bitacora.obtener_todos())
    assert partida.jugador.vida < vida
    assert h.sala is salas[0]


def test_us1_2_rango_300_se_mueve():
    """FR-003, FR-005 · US1-2"""
    salas, _ = cadena([100, 150])
    partida, h = preparar(salas[2], salas[0], 300)
    partida._actuar_enemigo(h)
    assert h.sala is salas[1]


def test_us1_3_rango_igual_a_la_distancia_se_mueve():
    """FR-004, FR-005 · US1-3"""
    salas, _ = cadena([100, 150])
    partida, h = preparar(salas[2], salas[0], 250)
    partida._actuar_enemigo(h)
    assert h.sala is salas[1]


def test_us1_4_fuera_de_rango_espera():
    """FR-004 · US1-4"""
    salas, _ = cadena([100, 150])
    partida, h = preparar(salas[2], salas[0], 200)
    partida._actuar_enemigo(h)
    assert h.sala is salas[0]
    assert h.evento.tiempo == 1000 + 100


def test_us1_5_puerta_cerrada_espera_y_no_la_abre():
    """FR-004, FR-009 · US1-5"""
    salas, pares = cadena([100, 100])
    ida, vuelta = pares[0]
    for cara in (ida, vuelta):
        cara.cerrada = True
        cara.llave = "k"
    partida, h = preparar(salas[2], salas[0], 1000)
    partida._actuar_enemigo(h)
    assert h.sala is salas[0]
    assert h.evento.tiempo == 1100
    assert ida.cerrada is True and vuelta.cerrada is True
    ida.cerrada = False
    vuelta.cerrada = False
    partida.agenda.cancelar(h.evento)
    partida._actuar_enemigo(h)
    assert h.sala is salas[1]


def test_us1_6_elige_la_ruta_mas_barata():
    """FR-003, FR-005 · US1-6: A→C cuesta 500, A→B→C cuesta 200."""
    a, b, c = Sala(1, "A"), Sala(2, "B"), Sala(3, "C")
    _unir(a, "E", b, "O", 100)
    _unir(b, "E", c, "O", 100)
    _unir(a, "S", c, "N", 500)
    partida, h = preparar(c, a, 300)
    partida._actuar_enemigo(h)
    assert h.sala is b


def test_us1_7_el_movimiento_pasa_por_programar_movimiento():
    """FR-006, FR-009 · US1-7: velocidad 50, salida de costo 120 → próxima acción T + 240."""
    salas, pares = cadena([120, 100])
    partida, h = preparar(salas[2], salas[0], 300, velocidad=50, reloj=700)
    llamadas = []
    original = partida._programar_movimiento

    def espia(actor, salida):
        llamadas.append((actor, salida))
        return original(actor, salida)

    partida._programar_movimiento = espia
    partida._actuar_enemigo(h)
    assert h.sala is salas[1]
    assert len(llamadas) == 1 and llamadas[0][0] is h and llamadas[0][1] is pares[0][0]
    assert h.evento.tiempo == 700 + 240
    assert any("se mueve" in linea for linea in partida.bitacora.obtener_todos())


def test_us1_7_cambio_de_velocidad_con_accion_pendiente():
    """FR-006, FR-009 · US1-7: velocidad 50→100 a mitad de una salida de costo 500."""
    salas, _ = cadena([500, 100])
    partida, h = preparar(salas[2], salas[0], 1000, velocidad=50, reloj=0)
    partida._actuar_enemigo(h)
    assert h.evento.tiempo == 1000
    partida.reloj = 400
    partida.efectos.aplicar_velocidad(h, +50, 10**6)
    assert h.velocidad == 100
    assert h.evento.tiempo == 400 + max(1, (1000 - 400) * 50 // 100)


def test_decisor_rechaza_limite_menor_que_el_rango():
    """FR-018 · el límite usado nunca puede ser menor que el rango del cazador."""
    salas, _ = cadena([100, 100])
    partida, h = preparar(salas[2], salas[0], 300)
    with pytest.raises(RuntimeError):
        DecisorCazador().decidir(partida, h, limite_forzado=100)
