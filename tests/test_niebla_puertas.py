from model.sala_logica import ABIERTA, CERRADA, NO_OBSERVADA, Salida
from tests.mapas_cazador import cadena
from tests.mapas_niebla import partida_en, servicio_en


def _caras_coinciden(pares):
    """Las dos caras de cada puerta guardan siempre el mismo valor de memoria."""
    for ida, vuelta in pares:
        assert ida.memoria == vuelta.memoria


def _cadena_de_cuatro():
    """S1 -E- S2 -E- S3 -E- S4; la puerta del medio (S2-S3) es la que se observa."""
    salas, pares = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    return salas, pares, partida, servicio_en(partida)


def test_puerta_observada_abierta_se_recuerda_abierta():
    """FR-006, FR-007 · US2-1"""
    salas, pares, partida, servicio = _cadena_de_cuatro()
    medio = pares[1][0]
    assert medio.memoria == NO_OBSERVADA
    servicio.mover("E")                      # en S2: la puerta S2-S3 se ve abierta
    servicio.mover("O")                      # al salir de S2 se anota
    assert medio.memoria == ABIERTA and pares[1][1].memoria == ABIERTA
    assert partida.puerta_recordada(medio) == ABIERTA
    _caras_coinciden(pares)


def test_puerta_que_se_cierra_lejos_sigue_recordada_abierta():
    """FR-006, FR-007 · US2-2"""
    salas, pares, partida, servicio = _cadena_de_cuatro()
    medio = pares[1][0]
    servicio.mover("E")
    servicio.mover("O")                      # el jugador está en S1, que no toca la puerta S2-S3
    partida._poner_cerrada(medio, True)      # se cierra sin que el jugador la vea
    assert medio.cerrada is True
    assert partida.puerta_recordada(medio) == ABIERTA
    assert partida.puerta_recordada(pares[1][1]) == ABIERTA
    _caras_coinciden(pares)


def test_al_volver_a_una_de_sus_dos_salas_se_ve_cerrada():
    """FR-006, FR-007 · US2-3"""
    salas, pares, partida, servicio = _cadena_de_cuatro()
    medio = pares[1][0]
    servicio.mover("E")
    servicio.mover("O")
    partida._poner_cerrada(medio, True)
    assert servicio.mover("E") is True       # entra en S2: la puerta toca su sala
    assert partida.puerta_recordada(medio) == CERRADA
    assert partida.puerta_recordada(pares[1][1]) == CERRADA
    servicio.mover("O")                      # al salir queda anotada cerrada
    assert medio.memoria == CERRADA and pares[1][1].memoria == CERRADA
    _caras_coinciden(pares)


def test_ultima_observacion_desde_el_otro_lado_gana():
    """FR-006, FR-007 · US2-4"""
    salas, pares, partida, servicio = _cadena_de_cuatro()
    medio = pares[1][0]
    servicio.mover("E")
    servicio.mover("O")                      # observada abierta desde S2
    assert medio.memoria == ABIERTA
    servicio.mover("E")
    servicio.mover("E")                      # ahora en S3, el otro lado
    partida._poner_cerrada(medio, True)      # el jugador la ve cerrarse desde S3
    servicio.mover("E")                      # sale de S3 hacia S4: anota desde su lado
    assert medio.memoria == CERRADA and pares[1][1].memoria == CERRADA
    assert partida.puerta_recordada(medio) == CERRADA
    _caras_coinciden(pares)


def test_puerta_que_se_cierra_sola_con_el_jugador_dentro_se_ve_cerrada():
    """FR-006 · US2-5"""
    salas, pares, partida, servicio = _cadena_de_cuatro()
    medio = pares[1][0]
    servicio.mover("E")                      # en S2, la puerta S2-S3 está abierta
    assert partida.puerta_recordada(medio) == ABIERTA
    partida.agenda.programar(partida.reloj + 50, "cierre_puerta", None, medio)
    assert servicio.esperar() is True        # el cierre ocurre durante la espera
    assert medio.cerrada is True
    assert partida.puerta_recordada(medio) == CERRADA
    assert partida.puerta_recordada(pares[1][1]) == CERRADA


def test_la_memoria_no_cambia_la_epoca_de_puertas():
    """FR-007 · escribir `memoria` no es un cambio real de `cerrada`"""
    salas, pares, partida, servicio = _cadena_de_cuatro()
    antes = Salida.epoca_puertas
    servicio.mover("E")
    servicio.mover("O")
    assert pares[1][0].memoria == ABIERTA
    assert Salida.epoca_puertas == antes


def test_un_cambio_real_de_cerrada_no_escribe_memoria():
    """FR-007 · solo salir de la sala escribe la memoria"""
    salas, pares, partida, servicio = _cadena_de_cuatro()
    medio = pares[1][0]
    servicio.mover("E")
    servicio.mover("O")
    partida._poner_cerrada(medio, True)
    partida._poner_cerrada(medio, False)
    partida._poner_cerrada(medio, True)
    assert medio.memoria == ABIERTA and pares[1][1].memoria == ABIERTA


def test_puerta_de_un_solo_sentido_sin_opuesta_se_recuerda():
    """FR-006 · una salida sin gemela se anota sin fallar"""
    salas, pares, partida, servicio = _cadena_de_cuatro()
    sola = Salida("N", salas[0], costo=100)
    salas[1].agregar_salida(sola)
    servicio.mover("E")
    servicio.mover("O")
    assert sola.memoria == ABIERTA
