from model.enemigo_logica import Enemigo
from model.sala_logica import AVISTADA, DESCONOCIDA, EXPLORADA, NO_OBSERVADA, Sala
from model.trampa_logica import Trampa
from tests.mapas_cazador import _unir, cadena
from tests.mapas_niebla import partida_en, servicio_en


def _encender(partida):
    partida.efectos.encender_antorcha(partida.jugador, 10 ** 6)


def _estrella():
    """Centro C (id 2) con tres vecinas: A (abierta), B (puerta cerrada), D (abierta y más lejos de A).

    A -E- C, C -E- B (cerrada), C -S- D. Cada vecina tiene además una salida propia hacia una sala lejana.
    """
    a, c, b, d = Sala(1, "A"), Sala(2, "C"), Sala(3, "B"), Sala(4, "D")
    lejanas = [Sala(5, "L5"), Sala(6, "L6"), Sala(7, "L7")]
    p_ac = _unir(a, "E", c, "O", 100)
    p_cb = _unir(c, "E", b, "O", 100, cerrada=True)
    p_cd = _unir(c, "S", d, "N", 100)
    lejos = [_unir(vecina, "S", lejana, "N", 100)
             for vecina, lejana in zip((a, b, d), lejanas)]
    return [a, c, b, d] + lejanas, a, c, b, d, lejanas, (p_ac, p_cb, p_cd), lejos


def test_vecinas_abiertas_o_cerradas_quedan_exploradas():
    """FR-008 · US3-1"""
    salas, a, c, b, d, lejanas, _, _ = _estrella()
    partida = partida_en(salas, a)
    _encender(partida)
    assert servicio_en(partida).mover("E") is True      # entra en C con la antorcha encendida
    for sala in (a, c, b, d):
        assert sala.conocimiento == EXPLORADA
    # los destinos de las salidas de las vecinas quedan avistados
    for lejana in lejanas:
        assert lejana.conocimiento == AVISTADA
    assert [s.id for s in partida.conocidas if s.conocimiento == EXPLORADA] != []


def test_vecina_con_enemigo_y_trampa_se_explora_sin_activar_nada():
    """FR-008, FR-009 · US3-2 (escenario 4)"""
    salas, a, c, b, d, lejanas, _, _ = _estrella()
    enemigo = Enemigo("e1", "rata", "Rata", 5, 5, 1, 0, 100, "guardian", b)
    b.inactivos.append(enemigo)
    trampa = Trampa(1, "Pinchos", 5)
    b.trampas.append(trampa)
    partida = partida_en(salas, a)
    servicio = servicio_en(partida)
    _encender(partida)
    vida = partida.jugador.vida
    assert servicio.mover("E") is True
    assert b.conocimiento == EXPLORADA
    assert enemigo in b.inactivos and enemigo not in partida.enemigos
    assert trampa.armada is True
    assert partida.jugador.vida == vida
    assert b.id not in servicio.fabrica.pobladas        # no se descargó su contenido
    assert c.id in servicio.fabrica.pobladas            # solo la sala en la que entró


def test_sin_antorcha_solo_se_explora_la_sala_en_la_que_se_entra():
    """FR-008 · US3-3"""
    salas, a, c, b, d, lejanas, _, _ = _estrella()
    partida = partida_en(salas, a)
    assert servicio_en(partida).mover("E") is True
    assert c.conocimiento == EXPLORADA
    assert b.conocimiento == AVISTADA and d.conocimiento == AVISTADA
    assert lejanas[0].conocimiento == AVISTADA          # la de A, que ya estaba explorada
    assert lejanas[1].conocimiento == DESCONOCIDA and lejanas[2].conocimiento == DESCONOCIDA


def test_vecina_tras_puerta_cerrada_se_explora():
    """FR-008 · US3-4"""
    salas, a, c, b, d, lejanas, pares, _ = _estrella()
    assert pares[1][0].cerrada is True
    partida = partida_en(salas, a)
    _encender(partida)
    servicio_en(partida).mover("E")
    assert b.conocimiento == EXPLORADA


def test_la_antorcha_no_anota_las_otras_puertas_de_la_vecina():
    """FR-008, FR-009 · US3-5"""
    salas, a, c, b, d, lejanas, pares, lejos = _estrella()
    partida = partida_en(salas, a)
    _encender(partida)
    servicio_en(partida).mover("E")
    # puertas propias de las vecinas B y D (la de A se anotó al salir de A, no por la antorcha)
    for ida, vuelta in lejos[1:]:
        assert ida.memoria == NO_OBSERVADA and vuelta.memoria == NO_OBSERVADA
    # la puerta que une C con B toca la sala del jugador: se lee en vivo, cerrada
    assert partida.puerta_recordada(pares[1][0]) == 2
    # la ruta no usa puertas sin observar: las vecinas son exploradas pero esas puertas no sirven
    assert partida.puerta_recordada(lejos[2][0]) == NO_OBSERVADA
    assert partida.puerta_recordada(lejos[1][0]) == NO_OBSERVADA


def test_encender_la_antorcha_dentro_de_una_sala_no_explora_sus_vecinas():
    """FR-008 · encender la antorcha no explora; solo entrar en una sala lo hace"""
    salas, pares = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    _encender(partida)
    assert salas[1].conocimiento == AVISTADA
    servicio = servicio_en(partida)
    servicio.esperar()
    assert salas[1].conocimiento == AVISTADA
    assert servicio.mover("E") is True
    assert salas[2].conocimiento == EXPLORADA            # ahora sí, al entrar en S2
    assert salas[3].conocimiento == AVISTADA
