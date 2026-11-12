"""El cazador conoce todo el mapa: ninguna decisión depende de la niebla ni del contenido descargado."""
from data.repositorio_cripta import RepositorioCripta
from dto.sala_dto import SalaDTO
from dto.salida_dto import SalidaDTO
from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.objeto_logica import Objeto
from model.partida_logica import Partida
from model.ruta_cazador import DecisorCazador, MODOS
from model.trampa_logica import Trampa
from service.juego_service import JuegoService
from tests.estado_fijo import FabricaFalsa
from tests.mapas_cazador import cadena, grilla
import pytest


def nueva_partida(sala_jugador, modo="individual"):
    jugador = Jugador(vida_max=10**6, ataque=10, defensa=10**6, velocidad=100,
                      inventario_max=10, sala=sala_jugador)
    partida = Partida(jugador, semilla=1)
    partida.decisor_cazador = DecisorCazador(modo)
    return partida


def agregar_cazador(partida, sala, rango, id_enemigo=1, aislado=True):
    h = Enemigo(id_enemigo, "cazador", f"Cazador{id_enemigo}", 10, 10, 5, 0, 100,
                "cazador", sala, rango=rango)
    partida.activar_enemigo(h)
    if aislado:
        partida.agenda.cancelar(h.evento)
        partida.reloj = 1000
    return h


def poblar(salas, desde=0):
    """Contenido 'descargado': objetos, trampas e inactivos en las salas desde el índice dado."""
    for i, sala in enumerate(salas):
        sala.objetos.append(Objeto(1000 + i, "escudo", "Escudo", "armadura", 4, 20, defensa_bonus=2))
        if i >= desde:
            sala.trampas.append(Trampa(2000 + i, "Pinchos", 5, id_catalogo="pinchos"))
            sala.inactivos.append(Enemigo(3000 + i, "rata", "Rata", 5, 5, 1, 0, 100,
                                          "guardián", sala))


def test_us4_1_la_ruta_cruza_salas_nunca_visitadas():
    """FR-008 · US4-1: el cazador avanza por salas con rastro None."""
    salas, _ = cadena([100, 100, 100])
    partida = nueva_partida(salas[3])
    h = agregar_cazador(partida, salas[0], 1000)
    assert all(s.rastro is None for s in salas[:3])
    partida._actuar_enemigo(h)
    assert h.sala is salas[1]
    assert salas[1].rastro is None and salas[2].rastro is None


@pytest.mark.parametrize("modo", MODOS)
def test_us4_2_con_o_sin_contenido_la_decision_es_la_misma(modo):
    """FR-010 · US4-2"""
    decisiones = []
    for con_contenido in (True, False):
        salas, _ = grilla(3, 3, 100)
        if con_contenido:
            poblar(salas)
        partida = nueva_partida(salas[8], modo)
        h = agregar_cazador(partida, salas[0], 1000)
        s = partida.decisor_cazador.decidir(partida, h)
        decisiones.append((s.destino.id, s.direccion))
    assert decisiones[0] == decisiones[1]


def _partida_de_la_grilla(con_contenido):
    salas, _ = grilla(4, 4, 100)
    if con_contenido:
        poblar(salas, desde=4)  # las trampas y los inactivos, fuera de la fila 1 por donde camina el jugador
    partida = nueva_partida(salas[0])
    cazadores = [agregar_cazador(partida, salas[15], 1000, 1, aislado=False),
                 agregar_cazador(partida, salas[12], 300, 2, aislado=False)]
    return partida, salas, cazadores


def _jugar_grilla(con_contenido):
    partida, salas, cazadores = _partida_de_la_grilla(con_contenido)
    lineas = []
    agregar = partida.bitacora.agregar

    def registrar(texto):
        lineas.append(texto)
        agregar(texto)

    partida.bitacora.agregar = registrar
    camino = ["E", "E", "E", "O", "O", "O"]
    for k in range(200):
        if k % 5 == 4:
            partida.esperar_jugador()
        else:
            partida.mover(camino[k % 6])
        if partida.terminada:
            break
    de_cazadores = [t for t in lineas if "Cazador" in t]
    estado = [partida.reloj, partida.acciones_jugador, partida.jugador.sala.id, partida.jugador.vida]
    estado += [(h.id_enemigo, h.sala.id, h.vida) for h in cazadores]
    return de_cazadores, estado


def test_us4_3_la_misma_partida_con_y_sin_contenido_es_identica():
    """FR-010, FR-014 · US4-3 · SC-004"""
    con = _jugar_grilla(True)
    sin = _jugar_grilla(False)
    assert con[0], "los cazadores deberían aparecer en la bitácora"
    assert con == sin


def test_us4_4_salas_construidas_desde_dtos_con_costo():
    """FR-008 · US4-4: sin red; el cazador usa los costos leídos de los datos."""
    repo = RepositorioCripta(fuente=None)
    repo.construir_salas([
        SalaDTO(1, "A", [SalidaDTO("E", 2, costo=100), SalidaDTO("S", 3, costo=500)]),
        SalaDTO(2, "B", [SalidaDTO("O", 1), SalidaDTO("E", 3, costo=100)]),
        SalaDTO(3, "C", [SalidaDTO("O", 2), SalidaDTO("N", 1)]),
    ])
    a, b, c = (repo.salas.buscar(i) for i in (1, 2, 3))
    partida = nueva_partida(c)
    h = agregar_cazador(partida, a, 300)
    partida._actuar_enemigo(h)
    assert h.sala is b  # A→B→C cuesta 200; la salida directa A→C cuesta 500


def test_el_cazador_no_pide_contenido_de_las_salas_a_las_que_entra():
    """FR-010 · Constitución V: solo los movimientos del jugador pueblan salas."""
    salas, _ = cadena([100] * 5)
    partida = nueva_partida(salas[0])
    h = agregar_cazador(partida, salas[5], 10000, aislado=False)
    fabrica = FabricaFalsa()
    servicio = JuegoService(partida, fabrica)
    assert servicio.mover("E")
    assert fabrica.pobladas == [2]
    for _ in range(3):
        servicio.esperar()
    assert h.sala is not salas[5]          # el cazador se movió...
    assert fabrica.pobladas == [2]         # ...y no pobló ninguna sala
    assert servicio.mover("E")
    assert fabrica.pobladas == [2, 3]
