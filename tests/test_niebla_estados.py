from tests.mapas_cazador import cadena
from tests.mapas_niebla import explorar_todo, partida_en, ruta_referencia


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
