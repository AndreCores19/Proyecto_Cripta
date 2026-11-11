"""Un log grabado en salas con costos mixtos se reproduce igual (G2 · FR-014)."""
import random

from adapters.bitacora_partida import BitacoraPartida
from adapters.lector_bitacora import LectorBitacora
from controller.controlador import Controlador
from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.sala_logica import Sala, Salida
from service.juego_service import JuegoService
from tests.estado_fijo import FabricaFalsa
from view.vista_silenciosa import VistaSilenciosa

ID_CRIPTA = "cripta-prueba"
SEMILLA_SALAS = 7
SEMILLA_PARTIDA = 5          # distinta de la de las salas: el replay debe tomarla del log
COSTOS = (1, 50, 100, 250, 500, 1000)
NUM_SALAS = 20


def armar_salas(semilla):
    """Salas nuevas en cadena con costos mixtos y los mismos enemigos, desde random.Random(semilla)."""
    azar = random.Random(semilla)
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(NUM_SALAS)]
    for i in range(NUM_SALAS - 1):
        costo = azar.choice(COSTOS)
        salas[i].agregar_salida(Salida("N", salas[i + 1], costo=costo))
        salas[i + 1].agregar_salida(Salida("S", salas[i], costo=costo))
    enemigos = []
    for k in range(15):
        comportamiento = "errante" if k % 2 == 0 else "rastreador"
        enemigos.append(Enemigo(f"e{k}", "x", f"Enemigo {k}", 50, 50, 5, 0, 100,
                                comportamiento, salas[azar.randrange(NUM_SALAS)]))
    return salas, enemigos


def armar_servicio(semilla_salas, semilla_partida):
    salas, enemigos = armar_salas(semilla_salas)
    jugador = Jugador(vida_max=10 ** 9, ataque=10, defensa=10 ** 6, velocidad=100,
                      inventario_max=10, sala=salas[0])
    partida = Partida(jugador, semilla=semilla_partida)
    for enemigo in enemigos:
        partida.activar_enemigo(enemigo)
    return JuegoService(partida, FabricaFalsa())


def comandos_fijos():
    comandos = []
    for i in range(120):
        comandos.append("esperar" if i % 4 == 3 else ("w" if (i // 19) % 2 == 0 else "s"))
    return comandos


def instantanea(servicio):
    resumen = servicio.resumen_final()
    estado = servicio.estado_vista()
    return {
        "reloj": resumen.reloj,
        "victoria": resumen.victoria,
        "acciones": resumen.acciones,
        "sala": estado.id_sala,
        "vida": estado.jugador.vida,
        "enemigos": [(e.id_enemigo, e.vida) for e in estado.enemigos],
    }


def test_el_replay_reproduce_el_estado_de_la_partida_grabada(tmp_path):
    """FR-014 · mismas salas y semilla del log, mismos comandos → mismo resumen y misma vista."""
    # Grabación
    grabada = armar_servicio(SEMILLA_SALAS, SEMILLA_PARTIDA)
    bitacora = BitacoraPartida(tmp_path)
    bitacora.abrir(ID_CRIPTA, "v1", "v1", grabada.semilla())
    controlador = Controlador(grabada, VistaSilenciosa(), bitacora, None)
    for comando in comandos_fijos():
        controlador.ejecutar(comando)
    bitacora.cerrar()
    esperado = instantanea(grabada)
    assert esperado["acciones"] == 120

    # Replay: salas nuevas (con la misma semilla) y la semilla leída del log
    lector = LectorBitacora(tmp_path / f"partida_{ID_CRIPTA}_{SEMILLA_PARTIDA}.log")
    lector.leer()
    assert lector.semilla == SEMILLA_PARTIDA
    assert lector.comandos == comandos_fijos()
    repetida = armar_servicio(SEMILLA_SALAS, lector.semilla)
    replay = Controlador(repetida, None, None, None)
    for comando in lector.comandos:
        replay.ejecutar(comando)

    assert instantanea(repetida) == esperado
