"""Duración de los movimientos según el costo de la salida (US1 · SC-002..SC-005)."""
from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.sala_logica import Sala, Salida
from model.trampa_logica import Trampa

HUGE = 10 ** 6


def _mundo(costo_ida=None, costo_vuelta=None, velocidad=100):
    """Dos salas A (1) y B (2) enlazadas por E/O; el jugador empieza en A."""
    a, b = Sala(1, "A"), Sala(2, "B")
    ida = Salida("E", b, costo=costo_ida)
    vuelta = Salida("O", a, costo=costo_vuelta)
    a.agregar_salida(ida)
    b.agregar_salida(vuelta)
    ida.enlazar(vuelta)
    jugador = Jugador(vida_max=HUGE, ataque=10, defensa=HUGE, velocidad=velocidad,
                      inventario_max=10, sala=a)
    return Partida(jugador, semilla=1), a, b


def _mover_y_medir(partida, direccion):
    """Mueve al jugador y devuelve (T, tiempo de su siguiente acción)."""
    t = partida.reloj
    assert partida.mover(direccion) is True
    return t, partida.jugador.evento.tiempo


def test_costo_300_velocidad_100_tarda_300():
    """FR-003, FR-004, FR-016 · US1-1"""
    partida, a, b = _mundo(costo_ida=300)
    t, siguiente = _mover_y_medir(partida, "E")
    assert partida.jugador.sala is b
    assert siguiente == t + 300
    assert partida.reloj == siguiente


def test_sin_costo_tarda_100():
    """FR-002, FR-004 · US1-2"""
    partida, _, _ = _mundo()
    t, siguiente = _mover_y_medir(partida, "E")
    assert siguiente == t + 100


def test_costo_en_los_dos_lados_aplica_en_ida_y_vuelta():
    """FR-005 · US1-3"""
    partida, _, _ = _mundo(costo_ida=250, costo_vuelta=250)
    t, siguiente = _mover_y_medir(partida, "E")
    assert siguiente == t + 250
    t, siguiente = _mover_y_medir(partida, "O")
    assert siguiente == t + 250


def test_costo_50_velocidad_150_tarda_33():
    """FR-004 · US1-4"""
    partida, _, _ = _mundo(costo_ida=50, velocidad=150)
    t, siguiente = _mover_y_medir(partida, "E")
    assert siguiente == t + 33


def test_costo_1_velocidad_1000_tarda_al_menos_1():
    """FR-004, FR-006 · US1-5"""
    partida, _, _ = _mundo(costo_ida=1, velocidad=1000)
    t, siguiente = _mover_y_medir(partida, "E")
    assert siguiente == t + 1


def test_costo_declarado_solo_en_la_ida_tambien_vale_de_vuelta():
    """FR-005 · US1-7"""
    partida, _, _ = _mundo(costo_ida=300)
    _mover_y_medir(partida, "E")
    t, siguiente = _mover_y_medir(partida, "O")
    assert siguiente == t + 300


def test_atacar_y_esperar_no_usan_el_costo_de_las_salidas():
    """FR-006 · US1-8: con salidas de costo 500, atacar y esperar tardan lo de la parte uno."""
    partida, a, _ = _mundo(costo_ida=500, costo_vuelta=500)
    rata = Enemigo("r1", "rata", "Rata", HUGE, HUGE, 1, 0, 100, "guardian", a)
    partida.activar_enemigo(rata)

    t = partida.reloj
    assert partida.esperar_jugador() is True
    assert partida.jugador.evento.tiempo == t + 100

    t = partida.reloj
    assert partida.atacar(rata) is True
    assert partida.jugador.evento.tiempo == t + 100


# --- Orden de los hechos al mover (FR-016) -------------------------------------

def _espiar_programacion(partida):
    """Envuelve _programar_movimiento y anota el estado en el momento de la llamada."""
    llamadas = []
    original = partida._programar_movimiento

    def espia(actor, salida):
        llamadas.append({
            "sala": partida.jugador.sala,
            "reloj": partida.reloj,
            "rastro": salida.destino.rastro,
            "trampas_armadas": [t.armada for t in salida.destino.trampas],
        })
        return original(actor, salida)

    partida._programar_movimiento = espia
    return llamadas


def test_el_jugador_ya_esta_en_la_sala_destino_al_programar_la_siguiente_accion():
    """FR-016 · el jugador está en el destino en T, antes de programar su siguiente acción."""
    partida, _, b = _mundo(costo_ida=300)
    llamadas = _espiar_programacion(partida)
    _mover_y_medir(partida, "E")
    assert len(llamadas) == 1
    assert llamadas[0]["sala"] is b


def test_la_marca_de_rastro_del_destino_es_t():
    """FR-016 · sala.rastro == T al programar la siguiente acción."""
    partida, _, b = _mundo(costo_ida=300)
    partida.esperar_jugador()           # T distinto de 0
    llamadas = _espiar_programacion(partida)
    t = partida.reloj
    assert t > 0
    partida.mover("E")
    assert llamadas[0]["reloj"] == t
    assert llamadas[0]["rastro"] == t
    assert b.rastro == t


def test_una_trampa_armada_del_destino_se_dispara_en_t_antes_de_la_siguiente_accion():
    """FR-016 · la trampa se activa en T, antes de programar la siguiente acción."""
    partida, _, b = _mundo(costo_ida=300)
    b.trampas.append(Trampa(1, "Pinchos", 5))
    llamadas = _espiar_programacion(partida)
    t = partida.reloj
    partida.mover("E")
    assert llamadas[0]["trampas_armadas"] == [False]
    assert llamadas[0]["reloj"] == t
    assert any(m.startswith(f"t={t}: Pinchos te causa") for m in partida.bitacora.obtener_todos())


def test_entrar_en_la_sala_de_salida_termina_en_t_sin_programar_siguiente_accion():
    """FR-016 · victoria en T y no se programa ninguna siguiente acción."""
    partida, _, b = _mundo(costo_ida=300)
    partida.sala_salida = b
    partida.abrio_puerta_salida = True
    llamadas = _espiar_programacion(partida)
    t = partida.reloj
    assert partida.mover("E") is True
    assert partida.terminada and partida.victoria
    assert partida.reloj == t
    assert llamadas == []


# --- US2: los enemigos pagan el costo de la salida (FR-007, FR-008, FR-016) -----

def _mundo_enemigo(tipo_comportamiento, costos, velocidad=100):
    """Sala E (10) con una salida por cada costo hacia vecinas V1.., y el jugador en una sala aparte.

    Preparación aislada: el jugador no está en la sala del enemigo ni en los destinos, y se
    cancela el turno de activación del enemigo; solo queda la acción que programe el método probado.
    """
    origen = Sala(10, "Origen")
    vecinas = []
    for i, costo in enumerate(costos):
        v = Sala(11 + i, f"V{i + 1}")
        ida = Salida(f"d{i}", v, costo=costo)
        vuelta = Salida(f"r{i}", origen, costo=costo)
        origen.agregar_salida(ida)
        v.agregar_salida(vuelta)
        ida.enlazar(vuelta)
        vecinas.append(v)
    aparte = Sala(99, "Aparte")
    jugador = Jugador(vida_max=HUGE, ataque=10, defensa=HUGE, velocidad=100,
                      inventario_max=10, sala=aparte)
    partida = Partida(jugador, semilla=1)
    enemigo = Enemigo("e1", "rata", "Rata", HUGE, HUGE, 1, 0, velocidad, tipo_comportamiento, origen)
    partida.activar_enemigo(enemigo)
    partida.agenda.cancelar(enemigo.evento)
    return partida, enemigo, origen, vecinas


def test_errante_se_mueve_y_su_siguiente_accion_tarda_el_costo_de_la_salida():
    """FR-007, FR-016 · US2-1"""
    partida, enemigo, _, (destino,) = _mundo_enemigo("errante", [200])
    partida.reloj = 1000
    partida._actuar_enemigo(enemigo)
    assert enemigo.sala is destino
    assert enemigo.evento.tiempo == 1000 + 200


def test_enemigo_sin_salida_espera_con_el_intervalo_de_la_parte_uno():
    """FR-006, FR-007 · el enemigo que no se mueve sigue esperando COSTO_ESPERAR"""
    partida, enemigo, origen, _ = _mundo_enemigo("errante", [])
    partida.reloj = 50
    partida._actuar_enemigo(enemigo)
    assert enemigo.sala is origen
    assert enemigo.evento.tiempo == 50 + 100


def test_rastreador_elige_el_rastro_mas_fresco_sin_importar_el_costo():
    """FR-008 · US2-2: costos 250 y 40; el rastro más fresco está tras la salida de 250."""
    partida, enemigo, _, (lejos, cerca) = _mundo_enemigo("rastreador", [250, 40])
    partida.reloj = 500
    lejos.rastro = 450      # más fresco, salida cara
    cerca.rastro = 300      # más viejo, salida barata
    salida = partida._decidir_rastreador(enemigo)
    assert salida.destino is lejos
    assert salida.costo == 250


def test_rastreador_con_rastros_iguales_desempata_por_id_de_sala_menor():
    """FR-008 · US2-2 (empate): gana la sala vecina de menor id."""
    partida, enemigo, _, (v1, v2) = _mundo_enemigo("rastreador", [40, 250])
    partida.reloj = 500
    v1.rastro = v2.rastro = 400
    assert v1.id < v2.id
    assert partida._decidir_rastreador(enemigo).destino is v1


def test_enemigo_de_velocidad_50_en_salida_de_costo_120_tarda_240():
    """FR-007 · US2-3.

    La spec de cazadores debe incluir un escenario equivalente con el comportamiento real de
    un cazador; aquí se prueba directamente _programar_movimiento.
    """
    partida, enemigo, origen, (destino,) = _mundo_enemigo("errante", [120], velocidad=50)
    partida.reloj = 700
    partida._programar_movimiento(enemigo, origen.salidas[0])
    assert enemigo.evento.tiempo == 700 + 240
