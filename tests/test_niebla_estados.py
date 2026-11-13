from tests.mapas_cazador import cadena, grilla
from tests.mapas_niebla import explorar_todo, partida_en, ruta_referencia, servicio_en


def test_oraculo_cadena_250_y_primera_salida():
    """FR-017, FR-018 · cadena 100+150, todo explorado y abierto: d = 250 y la primera salida va hacia B."""
    salas, pares = cadena([100, 150])
    explorar_todo(salas)
    partida = partida_en(salas, salas[0])
    d, salida = ruta_referencia(salas, partida, salas[2])
    assert d == 250
    assert salida is pares[0][0]
    assert salida.destino is salas[1]


def test_oraculo_sin_ruta_con_la_salida_del_medio_cerrada():
    """FR-017, FR-018 · la salida de la sala del medio está cerrada y recordada así: no hay ruta."""
    salas, pares = cadena([100, 150])
    for cara in pares[1]:
        cara.cerrada = True
    explorar_todo(salas)
    partida = partida_en(salas, salas[0])
    assert ruta_referencia(salas, partida, salas[2]) == (None, None)


def test_oraculo_jugador_ya_en_el_destino():
    """FR-017 · el jugador ya está en el destino: (0, None)."""
    salas, _ = cadena([100])
    explorar_todo(salas)
    partida = partida_en(salas, salas[1])
    assert ruta_referencia(salas, partida, salas[1]) == (0, None)


def test_oraculo_usa_la_memoria_lejos_y_el_estado_real_cerca():
    """FR-017, FR-018 · una puerta lejana se lee de `memoria`; una que toca la sala del jugador, de su estado real."""
    salas, pares = cadena([100, 150])
    explorar_todo(salas)
    # La puerta del medio se cierra en realidad pero el jugador no la ve: sigue recordada abierta.
    for cara in pares[1]:
        cara.cerrada = True
    partida = partida_en(salas, salas[0])
    d, salida = ruta_referencia(salas, partida, salas[2])
    assert d == 250 and salida is pares[0][0]
    # La puerta que toca la sala del jugador se lee en vivo: cerrada, no hay salida.
    for cara in pares[0]:
        cara.cerrada = True
    assert ruta_referencia(salas, partida, salas[2]) == (None, None)


def test_oraculo_no_usa_salas_sin_explorar_ni_puertas_sin_observar():
    """FR-017, FR-018 · una sala sin explorar o una puerta sin observar no se usan."""
    salas, pares = cadena([100, 150])
    explorar_todo(salas)
    partida = partida_en(salas, salas[0])
    pares[1][0].memoria = 0
    pares[1][1].memoria = 0
    assert ruta_referencia(salas, partida, salas[2]) == (None, None)
    pares[1][0].memoria = pares[1][1].memoria = 1
    salas[2].conocimiento = 1
    assert ruta_referencia(salas, partida, salas[2]) == (None, None)


# --- Estados de conocimiento (T007) ---------------------------------------

DESCONOCIDA, AVISTADA, EXPLORADA = 0, 1, 2


def _estados(salas):
    return [s.conocimiento for s in salas]


def _comprobar_conocidas(partida, salas):
    """`conocidas` tiene exactamente las salas con conocimiento > 0 y sin repetir."""
    con_nivel = [s for s in salas if s.conocimiento > 0]
    assert len(partida.conocidas) == len(con_nivel)
    for s in con_nivel:
        assert sum(1 for c in partida.conocidas if c is s) == 1


def test_inicio_sala_explorada_destinos_avistados_resto_desconocido():
    """FR-001, FR-002, FR-003, FR-004 · US1-1"""
    salas, _ = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    assert partida.reloj == 0
    assert _estados(salas) == [EXPLORADA, AVISTADA, DESCONOCIDA, DESCONOCIDA]
    _comprobar_conocidas(partida, salas)


def test_entrar_en_sala_avistada_la_explora_y_avista_sus_destinos():
    """FR-001, FR-003, FR-004 · US1-2 (los destinos ya explorados no bajan de nivel)"""
    salas, _ = grilla(2, 2, 100)          # ids 1 2 / 3 4
    partida = partida_en(salas, salas[0])
    assert _estados(salas) == [EXPLORADA, AVISTADA, AVISTADA, DESCONOCIDA]
    assert servicio_en(partida).mover("E") is True
    assert _estados(salas) == [EXPLORADA, EXPLORADA, AVISTADA, AVISTADA]
    _comprobar_conocidas(partida, salas)


def test_reentrar_conserva_el_estado():
    """FR-001 · US1-7"""
    salas, _ = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    servicio = servicio_en(partida)
    assert servicio.mover("E") is True
    antes = _estados(salas)
    assert servicio.mover("O") is True
    assert servicio.mover("E") is True
    assert _estados(salas) == antes == [EXPLORADA, EXPLORADA, AVISTADA, DESCONOCIDA]
    _comprobar_conocidas(partida, salas)


def test_conocidas_en_orden_de_descubrimiento():
    """FR-005, FR-013 · `conocidas` lista las salas con nivel > 0 en el orden en que se descubren"""
    salas, _ = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    assert [s.id for s in partida.conocidas] == [1, 2]
    servicio = servicio_en(partida)
    servicio.mover("E")
    assert [s.id for s in partida.conocidas] == [1, 2, 3]
    servicio.mover("E")
    assert [s.id for s in partida.conocidas] == [1, 2, 3, 4]
    servicio.mover("O")
    assert [s.id for s in partida.conocidas] == [1, 2, 3, 4]
