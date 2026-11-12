"""Un log grabado en una cripta con cazadores se reproduce igual (FR-014, FR-021, Constitución III)."""
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
from view.vista_consola import VistaConsola
from view.vista_silenciosa import VistaSilenciosa

ID_CRIPTA = "cripta-cazadores"
SEMILLA_SALAS = 11
SEMILLA_PARTIDA = 9          # distinta de la de las salas: el replay debe tomarla del log
COSTOS = (1, 50, 100, 250, 500, 1000)
NUM_SALAS = 20


def armar_servicio(semilla_salas, semilla_partida):
    """Salas a mano (cadena con costos mixtos), cazadores con rangos distintos y un errante."""
    azar = random.Random(semilla_salas)
    salas = [Sala(i + 1, f"Sala {i + 1}") for i in range(NUM_SALAS)]
    for i in range(NUM_SALAS - 1):
        costo = azar.choice(COSTOS)
        salas[i].agregar_salida(Salida("N", salas[i + 1], costo=costo))
        salas[i + 1].agregar_salida(Salida("S", salas[i], costo=costo))
    jugador = Jugador(vida_max=10 ** 9, ataque=10, defensa=10 ** 6, velocidad=100,
                      inventario_max=10, sala=salas[0])
    partida = Partida(jugador, semilla=semilla_partida)
    enemigos = [Enemigo(f"c{k}", "x", f"Cazador {k}", 50, 50, 5, 0, 100, "cazador",
                        salas[azar.randrange(1, NUM_SALAS)], rango=rango)
                for k, rango in enumerate((300, 1000, 5000, 1000000))]
    enemigos.append(Enemigo("e0", "x", "Enemigo 0", 50, 50, 5, 0, 100, "errante",
                            salas[azar.randrange(NUM_SALAS)]))
    for enemigo in enemigos:
        partida.activar_enemigo(enemigo)
    return JuegoService(partida, FabricaFalsa())


def comandos_fijos():
    return ["esperar" if i % 4 == 3 else ("w" if (i // 15) % 2 == 0 else "s") for i in range(120)]


def instantanea(servicio):
    resumen = servicio.resumen_final()
    estado = servicio.estado_vista()
    cazadores = [(e.id_enemigo, e.sala.id, e.vida) for e in servicio.partida.enemigos
                 if e.es_cazador()]
    return {
        "reloj": resumen.reloj,
        "victoria": resumen.victoria,
        "acciones": resumen.acciones,
        "sala": estado.id_sala,
        "vida": estado.jugador.vida,
        "enemigos": [(e.id_enemigo, e.vida, e.cazador) for e in estado.enemigos],
        "cazadores": cazadores,
    }


def test_el_replay_con_cazadores_reproduce_el_estado_y_no_crea_vistas(tmp_path, monkeypatch):
    """FR-014, FR-021 · mismas salas y semilla del log, mismos comandos → mismo resumen y misma vista."""
    grabada = armar_servicio(SEMILLA_SALAS, SEMILLA_PARTIDA)
    bitacora = BitacoraPartida(tmp_path)
    bitacora.abrir(ID_CRIPTA, "v1", "v1", grabada.semilla())
    controlador = Controlador(grabada, VistaSilenciosa(), bitacora, None)
    for comando in comandos_fijos():
        controlador.ejecutar(comando)
    bitacora.cerrar()
    esperado = instantanea(grabada)
    assert esperado["acciones"] == 120
    inicial = [(e.id_enemigo, e.sala.id) for e in armar_servicio(SEMILLA_SALAS, SEMILLA_PARTIDA)
               .partida.enemigos if e.es_cazador()]
    assert [(c[0], c[1]) for c in esperado["cazadores"]] != inicial, "los cazadores no se movieron"

    def prohibido(self, *args, **kwargs):
        raise AssertionError("vista instanciada durante el replay")

    monkeypatch.setattr(VistaConsola, "__init__", prohibido)
    monkeypatch.setattr(VistaSilenciosa, "__init__", prohibido)

    lector = LectorBitacora(tmp_path / f"partida_{ID_CRIPTA}_{SEMILLA_PARTIDA}.log")
    lector.leer()
    assert lector.semilla == SEMILLA_PARTIDA
    assert lector.comandos == comandos_fijos()
    repetida = armar_servicio(SEMILLA_SALAS, lector.semilla)
    replay = Controlador(repetida, None, None, None)
    for comando in lector.comandos:
        replay.ejecutar(comando)
    assert instantanea(repetida) == esperado
