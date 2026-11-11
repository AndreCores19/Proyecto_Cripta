import sys

from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.objeto_logica import Objeto, PERGAMINO_RETROCESO
from model.partida_logica import Partida
from model.sala_logica import Sala, Salida
from service.juego_service import JuegoService


class FabricaFalsa:
    def __init__(self):
        self.pobladas = []
        self.en_uso = []

    def poblar_sala(self, sala):
        self.pobladas.append(sala.id)

    def marcar_en_uso(self, ids):
        self.en_uso = list(ids)       #solo anota qué fichas le avisaron que siguen en uso


def armar_servicio():
    entrada, pasillo = Sala(1, "Entrada"), Sala(2, "Pasillo")
    ida = Salida("N", pasillo, cerrada=True, llave="llave1")
    vuelta = Salida("S", entrada)
    entrada.agregar_salida(ida)
    pasillo.agregar_salida(vuelta)
    ida.enlazar(vuelta)

    espada = Objeto(1, "espada", "Espada", "arma", 5, 30, ataque_bonus=4)
    llave = Objeto(2, "llave1", "Llave", "llave", 1, 1)
    pergamino = Objeto(3, "perg", "Pergamino", PERGAMINO_RETROCESO, 1, 1)
    entrada.objetos.extend([espada, llave, pergamino])

    jugador = Jugador(vida_max=50, ataque=10, defensa=0, velocidad=100, inventario_max=10, sala=entrada)
    partida = Partida(jugador, semilla=1)
    rata = Enemigo("r1", "rata", "Rata", 5, 5, 1, 0, 100, "guardian", pasillo)
    pasillo.inactivos.append(rata)
    fabrica = FabricaFalsa()
    return JuegoService(partida, fabrica), partida, fabrica, rata


def test_importar_el_servicio_no_ejecuta_scripts_de_prueba():
    # Un import de más llegó a lanzar solicitudes reales a la API
    assert not any(nombre.startswith("prueba_") for nombre in sys.modules)


def test_servicio_recoger_equipar_y_soltar():
    servicio, partida, _, _ = armar_servicio()
    assert servicio.recoger_objeto(1) is True
    assert servicio.recoger_objeto(999) is False
    assert servicio.equipar_objeto() is True
    assert partida.jugador.ataque == 14
    assert servicio.soltar_objeto() is True


def test_servicio_abrir_puerta_mover_y_poblar_la_sala_destino():
    servicio, partida, fabrica, _ = armar_servicio()
    assert servicio.mover("N") is False
    servicio.recoger_objeto(2)
    assert servicio.abrir_puerta("N") is True
    assert servicio.mover("N") is True
    assert partida.jugador.sala.nombre == "Pasillo"
    assert fabrica.pobladas == [2]


def test_servicio_esperar_y_atacar():
    servicio, partida, _, rata = armar_servicio()
    servicio.recoger_objeto(2)
    servicio.abrir_puerta("N")
    servicio.mover("N")
    antes = partida.reloj
    assert servicio.esperar() is True
    assert partida.reloj > antes
    assert servicio.atacar("r1") is True
    assert partida.enemigos_derrotados == 1


def test_servicio_retroceder_sin_pergamino_no_hace_nada():
    servicio, partida, _, _ = armar_servicio()
    servicio.recoger_objeto(1)
    reloj = partida.reloj
    assert servicio.retroceder() is False
    assert partida.reloj == reloj
    assert partida.jugador.inventario.tamano == 1


def test_servicio_retroceder_deshace_la_ultima_accion_y_gasta_el_pergamino():
    servicio, partida, _, _ = armar_servicio()
    servicio.recoger_objeto(3)          # pergamino
    servicio.recoger_objeto(1)          # espada
    assert partida.jugador.inventario.tamano == 2
    assert servicio.retroceder() is True
    assert partida.jugador.inventario.tamano == 0   # se deshace la espada y se gasta el pergamino

def test_servicio_avisa_a_la_fabrica_que_fichas_estan_en_uso():
    servicio, partida, fabrica, _ = armar_servicio()
    servicio.recoger_objeto(1)
    assert fabrica.en_uso != []