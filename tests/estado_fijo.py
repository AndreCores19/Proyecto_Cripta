"""Estado de juego fijo y dobles de prueba compartidos (T003 · FR-010, FR-014).

No es un módulo de pruebas: lo usan tests/capturar_salida_parte1.py (para
escribir los golden files de la parte uno) y las pruebas que comparan la
salida actual con esos golden files. No importa nada de otros módulos de
prueba.

Cada llamada a armar_estado_fijo() construye salas, actores y partida nuevos;
nada se comparte entre llamadas.
"""
from pathlib import Path

from aplicacion import Aplicacion
from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.objeto_logica import Objeto
from model.partida_logica import Partida
from model.sala_logica import Sala, Salida
from model.trampa_logica import Trampa
from service.juego_service import JuegoService

SEMILLA_FIJA = 1
CARPETA_GOLDEN = Path(__file__).resolve().parent.parent / "specs" / "001-exit-costs" / "salida-parte1"
FINALES = (None, "victoria", "muerte", "salida")


class FabricaFalsa:
    """Mismo comportamiento que la de tests/test_service.py, sin importarla."""

    def __init__(self):
        self.pobladas = []
        self.en_uso = []

    def poblar_sala(self, sala):
        self.pobladas.append(sala.id)

    def marcar_en_uso(self, ids):
        self.en_uso = list(ids)

    def nueva_partida(self, semilla=None):
        # Una partida recién construida en cada llamada; la semilla se ignora
        # porque el estado fijo ya usa SEMILLA_FIJA.
        return armar_estado_fijo()[1]


def _armar_salas():
    # Dos salas enlazadas: E/O abierta, N/S cerrada con llave.
    entrada, pasillo = Sala(1, "Entrada"), Sala(2, "Pasillo")
    este = Salida("E", pasillo)
    oeste = Salida("O", entrada)
    norte = Salida("N", pasillo, cerrada=True, llave="llave1")
    sur = Salida("S", entrada)
    entrada.agregar_salida(norte)
    entrada.agregar_salida(este)
    pasillo.agregar_salida(sur)
    pasillo.agregar_salida(oeste)
    este.enlazar(oeste)
    norte.enlazar(sur)
    return entrada, pasillo


def armar_estado_fijo(final=None):
    """Devuelve (servicio, partida) con un estado fijo y nuevo en cada llamada.

    final: None, "victoria", "muerte" o "salida" (fija victoria/terminada).
    """
    if final not in FINALES:
        raise ValueError(f"final desconocido: {final}")
    entrada, pasillo = _armar_salas()

    # Dos objetos en el suelo y una trampa armada en la sala del jugador.
    entrada.objetos.extend([
        Objeto(4, "escudo", "Escudo", "armadura", 4, 20, defensa_bonus=2),
        Objeto(5, "antorcha", "Antorcha", "antorcha", 1, 3, duracion=200),
    ])
    entrada.trampas.append(Trampa(1, "Pinchos", 5, id_catalogo="pinchos"))

    # Tres objetos en el inventario, la espada equipada (queda como actual).
    jugador = Jugador(vida_max=50, ataque=10, defensa=1, velocidad=100,
                      inventario_max=10, sala=entrada)
    jugador.nombre = "Ana"
    inv = jugador.inventario
    inv.agregar(Objeto(2, "llave1", "Llave", "llave", 1, 2))
    inv.agregar(Objeto(3, "pocion", "Poción", "pocion", 2, 50, cura=10))
    inv.agregar(Objeto(1, "espada", "Espada", "arma", 5, 30, ataque_bonus=4))
    inv.siguiente()
    inv.siguiente()                 # actual = espada
    inv.equipar_actual(jugador)

    # Un enemigo con un efecto en la sala del jugador.
    rata = Enemigo("r1", "rata", "Rata", 12, 15, 3, 0, 100, "guardian", entrada)
    entrada.inactivos.append(rata)

    partida = Partida(jugador, semilla=SEMILLA_FIJA)
    partida.efectos.aplicar_velocidad(rata, -50, 10 ** 6)

    # Al menos 25 líneas de bitácora (la bitácora guarda las últimas 20).
    for i in range(1, 26):
        partida.bitacora.agregar(f"t={partida.reloj}: línea de bitácora {i:02d}")

    if final == "victoria":
        partida.victoria = True
        partida.terminada = True
    elif final == "muerte":
        partida.victoria = False
        partida.terminada = True
    elif final == "salida":
        partida.victoria = False
        partida.terminada = False

    servicio = JuegoService(partida, FabricaFalsa())
    return servicio, partida


class LectorFalso:
    def __init__(self, semilla, comandos, version_cripta, version_catalogo):
        self.cripta = "fija"
        self.semilla = semilla
        self.comandos = list(comandos)
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo


class _DatosCripta:
    def __init__(self, version):
        self.id_cripta = "fija"
        self.version = version


class _RepoCripta:
    def __init__(self, version):
        self.datos = _DatosCripta(version)


class _RepoCatalogo:
    def __init__(self, version):
        self._version = version
        self.aciertos_memoria = 4
        self.aciertos_disco = 3
        self.fallos = 3

    def version(self):
        return self._version


class _Cliente:
    def __init__(self):
        self.solicitudes = 12
        self.presupuesto = 50


class AppFalsa:
    """Lo que Aplicacion.reproducir lee. Usar una nueva en cada llamada."""

    _versiones_coinciden = Aplicacion._versiones_coinciden
    _reportar = Aplicacion._reportar

    def __init__(self, version_cripta, version_catalogo):
        self.fabrica = FabricaFalsa()
        self.repo_cripta = _RepoCripta(version_cripta)
        self.repo_catalogo = _RepoCatalogo(version_catalogo)
        self.cliente = _Cliente()


def cargar_golden(nombre):
    return (CARPETA_GOLDEN / nombre).read_text(encoding="utf-8")
