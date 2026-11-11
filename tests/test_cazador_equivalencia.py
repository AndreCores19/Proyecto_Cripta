from tests.mapas_cazador import cadena, distancias_referencia


def test_oraculo_cadena_100_150():
    """FR-003, FR-011 · el oráculo da 0, 150 y 250 con el jugador al final de la cadena."""
    salas, _ = cadena([100, 150])
    dist = distancias_referencia(salas, salas[2])
    assert dist == [250, 150, 0]


def test_oraculo_cadena_jugador_al_inicio():
    """FR-003, FR-011 · con el jugador en la primera sala: 0, 100 y 250."""
    salas, _ = cadena([100, 150])
    assert distancias_referencia(salas, salas[0]) == [0, 100, 250]
