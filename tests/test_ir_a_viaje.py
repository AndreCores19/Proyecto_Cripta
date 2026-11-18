from model.sala_logica import Sala
from model.viaje_logica import (DANO, ENEMIGOS, FIN_PARTIDA, LLEGADA, RETROCESO, SIN_RUTA, Viaje)
from tests.mapas_cazador import _unir, cadena, grilla
from tests.mapas_niebla import partida_en, servicio_en
from tests.test_niebla_retroceso import instantanea_conocimiento


def _recorrida(costos):
    """Cadena que el jugador ya recorrió de punta a punta y de vuelta: queda en S1, con todo explorado."""
    salas, pares = cadena(costos)
    partida = partida_en(salas, salas[0])
    servicio = servicio_en(partida)
    for _ in costos:
        assert servicio.mover("E") is True
    for _ in costos:
        assert servicio.mover("O") is True
    assert partida.jugador.sala is salas[0]
    return salas, pares, partida, servicio


def test_destino_sin_explorar_o_id_desconocido_se_rechaza_sin_cambiar_nada():
    """FR-016 · US6-1 (escenario 1)"""
    salas, _ = cadena([100, 100, 100])
    partida = partida_en(salas, salas[0])
    servicio = servicio_en(partida)
    antes = instantanea_conocimiento(salas, partida)
    reloj = partida.reloj
    acciones = partida.acciones_jugador
    for id_sala in ("2", "3", "999", "xyz"):                 # la 2 está avistada, el resto no se conoce
        resultado = servicio.ir_a(id_sala)
        assert resultado.aceptado is False
        assert resultado.motivo == "no_explorada" and resultado.pasos == 0
        assert partida.reloj == reloj and partida.acciones_jugador == acciones
        assert instantanea_conocimiento(salas, partida) == antes
        assert partida.jugador.sala is salas[0]


def test_viaje_a_una_sala_explorada_llega_y_cuenta_los_pasos():
    """FR-016, FR-019 · US6-2"""
    salas, pares, partida, servicio = _recorrida([100, 100, 100])
    acciones = partida.acciones_jugador
    resultado = servicio.ir_a("4")
    assert resultado.aceptado is True
    assert resultado.motivo == LLEGADA
    assert resultado.pasos == 3 and resultado.direcciones == ["E", "E", "E"]
    assert partida.jugador.sala is salas[3]
    assert partida.acciones_jugador == acciones + 3


def test_el_id_se_busca_sin_distinguir_mayusculas():
    """FR-016 · el id se compara como texto"""
    salas, _ = cadena([100, 100])
    for i, sala in enumerate(salas):
        sala.id = f"Sala{i}"
    partida = partida_en(salas, salas[0])
    servicio = servicio_en(partida)
    servicio.mover("E")
    resultado = servicio.ir_a("SALA1")
    assert resultado.aceptado is True and resultado.motivo == LLEGADA and resultado.pasos == 0


def test_cada_paso_avanza_el_reloj_lo_que_cuesta_la_salida_y_los_eventos_ocurren_entre_pasos():
    """FR-019, FR-022 · US6-7"""
    salas, pares = cadena([100, 300, 50])
    lateral = Sala(9, "lateral")
    puerta, _ = _unir(salas[1], "N", lateral, "S", 100)       # puerta lateral, fuera de la ruta
    todas = salas + [lateral]
    partida = partida_en(todas, salas[0])
    servicio = servicio_en(partida)
    for _ in range(3):
        servicio.mover("E")
    for _ in range(3):
        servicio.mover("O")
    reloj0 = partida.reloj
    partida.agenda.programar(reloj0 + 150, "cierre_puerta", None, puerta)   # cae durante el segundo paso
    relojes, cerradas = [], []

    def mover(direccion):
        resultado = servicio.mover(direccion)
        relojes.append(partida.reloj)
        cerradas.append(puerta.cerrada)
        return resultado

    viaje = Viaje(partida, salas[3], mover)
    while viaje.paso() is None:
        pass
    assert relojes == [reloj0 + 100, reloj0 + 400, reloj0 + 450]
    assert cerradas == [False, True, True]                    # se cerró entre el primer y el segundo paso
    assert partida.jugador.sala is salas[3]


def test_ya_en_el_destino_llegada_sin_pasos_ni_tiempo():
    """FR-016, FR-022 · US6-10"""
    salas, pares, partida, servicio = _recorrida([100, 100])
    reloj = partida.reloj
    resultado = servicio.ir_a("1")
    assert resultado.aceptado is True and resultado.motivo == LLEGADA
    assert resultado.pasos == 0 and resultado.direcciones == []
    assert partida.reloj == reloj
