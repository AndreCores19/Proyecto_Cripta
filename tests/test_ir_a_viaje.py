from model.enemigo_logica import Enemigo
from model.sala_logica import ABIERTA, CERRADA, Sala
from model.trampa_logica import Trampa
from model.viaje_logica import (DANO, ENEMIGOS, FIN_PARTIDA, LLEGADA, RETROCESO, SIN_RUTA, Viaje)
from tests.mapas_cazador import _unir, cadena, grilla
from tests.mapas_niebla import explorar_todo, partida_en, servicio_en
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


# --- Puertas y recálculo (T030) ---------------------------------------------

def _todo_conocido(salas, jugador):
    """Partida con todas las salas exploradas, las puertas recordadas y `conocidas` completa (preparación de la prueba)."""
    partida = partida_en(salas, jugador)
    explorar_todo(salas)
    for sala in salas:
        if not any(c is sala for c in partida.conocidas):
            partida.conocidas.append(sala)
    return partida, servicio_en(partida)


def _con_alternativa():
    """S1 -E- S2 -E- S3 directa y S2 -N- S6 -E- S3 por el lado; todo conocido, el jugador en S1."""
    s1, s2, s3, s6 = Sala(1, "S1"), Sala(2, "S2"), Sala(3, "S3"), Sala(6, "S6")
    _unir(s1, "E", s2, "O", 100)
    directa = _unir(s2, "E", s3, "O", 100)
    _unir(s2, "N", s6, "S", 100)
    _unir(s6, "E", s3, "N", 100)
    salas = [s1, s2, s3, s6]
    partida, servicio = _todo_conocido(salas, s1)
    return salas, directa, partida, servicio


def test_puerta_recordada_abierta_pero_cerrada_se_actualiza_y_sin_alternativa_se_detiene():
    """FR-006, FR-020, FR-022 · US7-1 (escenario 2)"""
    salas, pares, partida, servicio = _recorrida([100, 100, 100])
    reloj0 = partida.reloj
    partida._poner_cerrada(pares[1][0], True)               # se cierra sin que el jugador la vea
    assert partida.puerta_recordada(pares[1][0]) == ABIERTA
    resultado = servicio.ir_a("4")
    assert resultado.aceptado is True and resultado.motivo == SIN_RUTA
    assert resultado.pasos == 1 and partida.jugador.sala is salas[1]
    assert partida.reloj == reloj0 + 100                     # nada de tiempo tras el último paso
    assert partida.puerta_recordada(pares[1][0]) == CERRADA  # el mapa ya la muestra cerrada


def test_con_una_alternativa_conocida_el_viaje_continua_por_ella():
    """FR-020 · US7-2"""
    salas, directa, partida, servicio = _con_alternativa()
    visitadas = []

    def mover(direccion):
        resultado = servicio.mover(direccion)
        if partida.jugador.sala is salas[1]:
            partida._poner_cerrada(directa[0], True)         # al llegar a S2 la directa está cerrada
        visitadas.append(partida.jugador.sala.id)
        return resultado

    viaje = Viaje(partida, salas[2], mover)
    while viaje.paso() is None:
        pass
    assert visitadas == [2, 6, 3]                            # por el lado, no por la directa


def test_los_eventos_del_reloj_cambian_una_puerta_y_el_siguiente_paso_usa_ese_estado():
    """FR-006, FR-020, FR-022 · US7-9"""
    salas, directa, partida, servicio = _con_alternativa()
    partida.agenda.programar(partida.reloj + 50, "cierre_puerta", None, directa[0])
    visitadas = []

    def mover(direccion):
        resultado = servicio.mover(direccion)
        visitadas.append(partida.jugador.sala.id)
        return resultado

    viaje = Viaje(partida, salas[2], mover)
    assert viaje.paso() is None and visitadas == [2]
    assert directa[0].cerrada is True                         # se cerró durante el primer paso
    while viaje.paso() is None:
        pass
    assert visitadas == [2, 6, 3]


# --- Motivos de parada (T031) -----------------------------------------------

def _cadena_conocida(largo=4, costo=100):
    salas, pares = cadena([costo] * largo)
    partida, servicio = _todo_conocido(salas, salas[0])
    return salas, pares, partida, servicio


def _enemigo(sala, comportamiento="guardian", **extra):
    return Enemigo("e1", "rata", "Rata", 50, 50, 1, 0, 100, comportamiento, sala, **extra)


def test_ruta_que_entra_en_una_sala_con_enemigos_dormidos_los_activa_y_se_detiene():
    """FR-022, FR-023 · US7-3 (escenario 3)"""
    salas, _, partida, servicio = _cadena_conocida()
    enemigo = _enemigo(salas[2])
    salas[2].inactivos.append(enemigo)
    resultado = servicio.ir_a("5")
    assert resultado.motivo == ENEMIGOS and resultado.pasos == 2
    assert partida.jugador.sala is salas[2]
    assert enemigo in partida.enemigos and enemigo.esta_vivo()
    assert salas[2].inactivos == []


def test_sala_con_enemigos_activos_detiene_el_viaje():
    """FR-022 · US7-4"""
    salas, _, partida, servicio = _cadena_conocida()
    partida.activar_enemigo(_enemigo(salas[1]))
    resultado = servicio.ir_a("5")
    assert resultado.motivo == ENEMIGOS and resultado.pasos == 1
    assert partida.jugador.sala is salas[1]


def test_dano_de_una_trampa_detiene_el_viaje():
    """FR-022, FR-023 · US7-5 (trampa)"""
    salas, _, partida, servicio = _cadena_conocida()
    salas[1].trampas.append(Trampa(1, "Pinchos", 5))
    resultado = servicio.ir_a("5")
    assert resultado.motivo == DANO and resultado.pasos == 1
    assert partida.jugador.vida == partida.jugador.vida_max - 5


def test_dano_de_veneno_durante_un_paso_detiene_el_viaje():
    """FR-022 · US7-5 (efecto entre dos pasos)"""
    salas, _, partida, servicio = _cadena_conocida()
    partida.efectos.aplicar_veneno(partida.jugador, 3)
    resultado = servicio.ir_a("5")
    assert resultado.motivo == DANO and resultado.pasos == 1
    assert partida.jugador.vida < partida.jugador.vida_max


def test_ataque_de_un_enemigo_en_los_eventos_del_paso_se_informa_como_enemigos():
    """FR-022 · US7-5 (ataque de enemigo): el orden de FR-022 pone enemigos antes que daño"""
    salas, _, partida, servicio = _cadena_conocida()
    partida.activar_enemigo(_enemigo(salas[1]))
    vida = partida.jugador.vida
    resultado = servicio.ir_a("5")
    assert partida.jugador.vida < vida                        # el enemigo le pegó durante el paso
    assert resultado.motivo == ENEMIGOS


def test_el_paso_que_gana_la_partida_termina_el_viaje():
    """FR-022, FR-023 · US7-6 (victoria en una sala intermedia)"""
    salas, _, partida, servicio = _cadena_conocida()
    partida.sala_salida = salas[1]
    partida.abrio_puerta_salida = True
    resultado = servicio.ir_a("5")
    assert resultado.motivo == FIN_PARTIDA and resultado.pasos == 1
    assert partida.terminada is True and partida.victoria is True


def test_el_paso_en_el_que_el_jugador_muere_no_da_otro_paso():
    """FR-022, FR-023 · US7-6 (muerte en una trampa)"""
    salas, _, partida, servicio = _cadena_conocida()
    salas[1].trampas.append(Trampa(1, "Abismo", 10 ** 7))
    resultado = servicio.ir_a("5")
    assert resultado.motivo == FIN_PARTIDA and resultado.pasos == 1
    assert partida.terminada is True and partida.victoria is False
    assert partida.jugador.sala is salas[1]


def test_varios_motivos_a_la_vez_gana_el_primero_del_orden():
    """FR-022, FR-023 · US7-7"""
    # llegada en una sala con enemigos: llegada
    salas, _, partida, servicio = _cadena_conocida(largo=2)
    salas[2].inactivos.append(_enemigo(salas[2]))
    assert servicio.ir_a("3").motivo == LLEGADA
    # daño y enemigos (sala intermedia con enemigos y trampa): enemigos
    salas, _, partida, servicio = _cadena_conocida()
    salas[1].inactivos.append(_enemigo(salas[1]))
    salas[1].trampas.append(Trampa(1, "Pinchos", 5))
    assert servicio.ir_a("5").motivo == ENEMIGOS
    # muerte en una trampa de la sala destino: fin de la partida, no llegada
    salas, _, partida, servicio = _cadena_conocida(largo=2)
    salas[2].trampas.append(Trampa(1, "Abismo", 10 ** 7))
    assert servicio.ir_a("3").motivo == FIN_PARTIDA
    # victoria en la sala destino: fin de la partida, no llegada
    salas, _, partida, servicio = _cadena_conocida(largo=2)
    partida.sala_salida = salas[2]
    partida.abrio_puerta_salida = True
    assert servicio.ir_a("3").motivo == FIN_PARTIDA
    # trampa no mortal en la sala destino: llegada antes que daño
    salas, _, partida, servicio = _cadena_conocida(largo=2)
    salas[2].trampas.append(Trampa(1, "Pinchos", 5))
    assert servicio.ir_a("3").motivo == LLEGADA


def test_sin_ruta_conocida_antes_de_un_paso_no_consume_tiempo():
    """FR-022, FR-023 · US7-8"""
    salas, pares, partida, servicio = _recorrida([100, 100])
    reloj = partida.reloj
    partida._poner_cerrada(pares[0][0], True)                 # toca la sala del jugador: se lee en vivo
    resultado = servicio.ir_a("3")
    assert resultado.motivo == SIN_RUTA and resultado.pasos == 0
    assert partida.reloj == reloj


def test_un_cazador_que_entra_en_la_sala_durante_el_paso_detiene_el_viaje():
    """FR-022, FR-023 · US7-10"""
    salas, _, partida, servicio = _cadena_conocida()
    cazador = _enemigo(salas[2], "cazador", rango=500)
    partida.activar_enemigo(cazador)
    assert not any(e.sala is salas[1] for e in partida.enemigos)
    resultado = servicio.ir_a("5")
    assert resultado.motivo == ENEMIGOS and resultado.pasos == 1
    assert cazador.sala is partida.jugador.sala
    assert partida.jugador.sala is salas[1]
