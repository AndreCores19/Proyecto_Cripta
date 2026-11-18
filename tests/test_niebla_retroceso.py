from controller.controlador import Controlador
from model.objeto_logica import Objeto, PERGAMINO_RETROCESO
from model.sala_logica import ABIERTA, AVISTADA, CERRADA, DESCONOCIDA, EXPLORADA, NO_OBSERVADA
from tests.mapas_cazador import cadena, grilla
from tests.mapas_niebla import explorar_todo, partida_en, servicio_en
from view.vista_silenciosa import VistaSilenciosa


def instantanea_conocimiento(salas, partida):
    """Conocimiento completo: (id, conocimiento) por sala, (origen.id, direccion, memoria) por salida y ids de `conocidas`."""
    niveles = [(s.id, s.conocimiento) for s in salas]
    puertas = [(s.id, x.direccion, x.memoria) for s in salas for x in s.salidas]
    return niveles, puertas, [s.id for s in partida.conocidas]


def _encender(partida):
    partida.efectos.encender_antorcha(partida.jugador, 10 ** 6)


def test_retroceder_un_movimiento_deshace_la_sala_explorada():
    """FR-013, FR-014 · US4-2"""
    salas, _ = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    antes = instantanea_conocimiento(salas, partida)
    servicio_en(partida).mover("E")
    assert salas[1].conocimiento == EXPLORADA and salas[2].conocimiento == AVISTADA
    assert partida.retroceder() is True
    assert salas[1].conocimiento == AVISTADA
    assert salas[2].conocimiento == DESCONOCIDA
    assert [s.id for s in partida.conocidas] == [1, 2]
    assert instantanea_conocimiento(salas, partida) == antes


def test_retroceder_devuelve_la_memoria_de_puertas_a_su_valor_anterior():
    """FR-013, FR-014 · US4-3"""
    salas, pares = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    servicio = servicio_en(partida)
    medio = pares[1][0]
    servicio.mover("E")
    servicio.mover("O")                       # memoria de la puerta S2-S3: abierta
    assert medio.memoria == ABIERTA
    partida._poner_cerrada(medio, True)
    servicio.mover("E")
    servicio.mover("O")                       # ahora la anota cerrada
    assert medio.memoria == CERRADA
    assert partida.retroceder() is True       # deshace la última salida de S2
    assert medio.memoria == ABIERTA and pares[1][1].memoria == ABIERTA
    # y la anotada por el primer movimiento (salir de S1) vuelve a no observada al deshacerla
    assert pares[0][0].memoria == ABIERTA     # se anotó al salir de S1 y de S2; sigue así
    while partida.retroceder():
        pass
    assert pares[0][0].memoria == NO_OBSERVADA and medio.memoria == NO_OBSERVADA


def test_movimiento_con_antorcha_se_deshace_con_todo_lo_que_exploro():
    """FR-008, FR-013 · US3-6 (escenario 5)"""
    salas, _ = cadena([100, 100, 100, 100])
    partida = partida_en(salas, salas[0])
    _encender(partida)
    antes = instantanea_conocimiento(salas, partida)
    assert antes[0] == [(1, 2), (2, 1), (3, 0), (4, 0), (5, 0)]
    servicio_en(partida).mover("E")
    assert [s.conocimiento for s in salas] == [EXPLORADA, EXPLORADA, EXPLORADA, AVISTADA, DESCONOCIDA]
    assert partida.retroceder() is True
    assert [s.conocimiento for s in salas] == [EXPLORADA, AVISTADA, DESCONOCIDA, DESCONOCIDA, DESCONOCIDA]
    assert instantanea_conocimiento(salas, partida) == antes


def test_retroceder_solo_el_ultimo_conserva_lo_anterior():
    """FR-013 · se deshace solo el último de varios movimientos"""
    salas, _ = cadena([100, 100, 100, 100])
    partida = partida_en(salas, salas[0])
    servicio = servicio_en(partida)
    servicio.mover("E")
    despues_del_primero = instantanea_conocimiento(salas, partida)
    servicio.mover("E")
    assert salas[2].conocimiento == EXPLORADA
    assert partida.retroceder() is True
    assert instantanea_conocimiento(salas, partida) == despues_del_primero
    assert salas[1].conocimiento == EXPLORADA


# --- Guardado, recarga y determinismo (T019) -------------------------------

COMANDOS = ["d", "d", "a", "s", "d", "d", "w", "a", "esperar", "s", "s", "a", "d", "w", "a", "a"]


def _juego(con_antorcha):
    salas, _ = grilla(3, 3, 100)
    partida = partida_en(salas, salas[0])
    if con_antorcha:
        _encender(partida)
    controlador = Controlador(servicio_en(partida), VistaSilenciosa(), None, None)
    return salas, partida, controlador


def test_recargar_la_lista_de_comandos_reconstruye_el_conocimiento():
    """FR-012, FR-014 · US4-1"""
    for con_antorcha in (False, True):
        salas, partida, controlador = _juego(con_antorcha)
        for comando in COMANDOS:
            controlador.ejecutar(comando)
        original = instantanea_conocimiento(salas, partida)
        assert len(original[2]) >= 4
        salas2, partida2, controlador2 = _juego(con_antorcha)      # salas reconstruidas con el mismo constructor
        for comando in controlador.comandos:                        # como Aplicacion._reejecutar
            controlador2.ejecutar(comando)
        assert instantanea_conocimiento(salas2, partida2) == original


def test_misma_cripta_semilla_y_comandos_dan_el_mismo_conocimiento_en_cada_paso():
    """FR-012, FR-014 · US4-4"""
    for con_antorcha in (False, True):
        salas_a, partida_a, controlador_a = _juego(con_antorcha)
        salas_b, partida_b, controlador_b = _juego(con_antorcha)
        for comando in COMANDOS:
            controlador_a.ejecutar(comando)
            controlador_b.ejecutar(comando)
            assert (instantanea_conocimiento(salas_a, partida_a)
                    == instantanea_conocimiento(salas_b, partida_b))


# --- El pergamino y los viajes (T035) ---------------------------------------

def _preparar_conocido(salas, partida):
    """Todo explorado y recordado, y `conocidas` completa (preparación de la prueba)."""
    explorar_todo(salas)
    for sala in salas:
        if not any(c is sala for c in partida.conocidas):
            partida.conocidas.append(sala)


def test_el_paso_revertido_devuelve_las_salas_exploradas_y_las_puertas_observadas():
    """FR-013, FR-025 · US8-2"""
    salas, pares = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    _preparar_conocido(salas, partida)
    # S3 aún no se conoce y la puerta de S1 nunca se observó: el paso hacia S2 descubre ambas cosas
    salas[2].conocimiento = 0
    partida.conocidas.remove(salas[2])
    for cara in pares[0]:
        cara.memoria = 0
    antes = instantanea_conocimiento(salas, partida)
    servicio = servicio_en(partida)
    resultado = servicio.ir_a("2")
    assert resultado.motivo == "llegada" and resultado.pasos == 1
    assert salas[2].conocimiento == 1 and pares[0][0].memoria == 1
    assert instantanea_conocimiento(salas, partida) != antes
    assert partida.retroceder() is True
    assert instantanea_conocimiento(salas, partida) == antes


def test_un_pergamino_leido_tras_un_viaje_revierte_solo_su_ultimo_paso():
    """FR-013, FR-025 · US8-3"""
    salas, _ = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    servicio = servicio_en(partida)
    for _ in range(3):
        servicio.mover("E")
    for _ in range(3):
        servicio.mover("O")
    partida.jugador.inventario.agregar(Objeto(90, "pergamino", "Pergamino", PERGAMINO_RETROCESO, 1, 1))
    resultado = servicio.ir_a("4")
    assert resultado.motivo == "llegada" and resultado.pasos == 3
    assert partida.jugador.sala is salas[3]
    reloj_tras_dos_pasos = partida.reloj - 100
    assert servicio.retroceder() is True
    assert partida.jugador.sala is salas[2]                   # solo el último paso
    assert partida.reloj == reloj_tras_dos_pasos
