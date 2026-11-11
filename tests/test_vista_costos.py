"""Vista de sala con el costo de cada salida (US4 · FR-010)."""
import re

from controller.controlador import Controlador
from dto.estado_vista_dto import EstadoVistaDTO
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.sala_logica import Sala, Salida
from service.juego_service import JuegoService
from tests.estado_fijo import FabricaFalsa, armar_estado_fijo, cargar_golden
from view.vista_consola import VistaConsola

HUGE = 10 ** 6


def _servicio_con_costos():
    """Sala 1 con norte (costo 300), sur (sin costo) y este (cerrada, costo 40)."""
    a = Sala(1, "A")
    n, s, e = Sala(2, "Norte"), Sala(3, "Sur"), Sala(4, "Este")
    for dir_, dest, costo, cerrada in (("N", n, 300, False), ("S", s, None, False),
                                       ("E", e, 40, True)):
        ida = Salida(dir_, dest, cerrada=cerrada, costo=costo)
        a.agregar_salida(ida)
        vuelta = Salida("X", a)
        dest.agregar_salida(vuelta)
        ida.enlazar(vuelta)
    jugador = Jugador(vida_max=HUGE, ataque=1, defensa=1, velocidad=100,
                      inventario_max=10, sala=a)
    jugador.nombre = "Ana"
    return JuegoService(Partida(jugador, semilla=1), FabricaFalsa())


def test_estado_vista_trae_el_costo_resuelto_de_cada_salida():
    """FR-010 · US4-1: costo declarado 300, sin declarar 100."""
    salidas = {s.direccion: s for s in _servicio_con_costos().estado_vista().salidas}
    assert salidas["N"].costo == 300
    assert salidas["S"].costo == 100


def test_salida_cerrada_conserva_su_costo():
    """FR-010 · US4-2: cerrada con costo 40."""
    s = {s.direccion: s for s in _servicio_con_costos().estado_vista().salidas}["E"]
    assert s.cerrada is True
    assert s.costo == 40


def test_la_vista_imprime_el_costo_en_cada_linea_de_salida(capsys):
    """FR-010 · US4-1, US4-2"""
    VistaConsola().mostrar_estado(_servicio_con_costos().estado_vista())
    salida = capsys.readouterr().out
    assert "N -> Norte (abierta, costo 300)" in salida
    assert "S -> Sur (abierta, costo 100)" in salida
    assert "E -> Este (cerrada, costo 40)" in salida


def test_salida_igual_al_golden_de_la_parte_uno_mas_el_costo(capsys):
    """FR-010 · Golden estado.txt con ', costo 100' dentro del paréntesis de cada salida."""
    servicio, _ = armar_estado_fijo()
    VistaConsola().mostrar_estado(servicio.estado_vista())
    obtenido = capsys.readouterr().out
    esperado = re.sub(r"^(  \w+ -> .+ \((?:abierta|cerrada))\)$", r"\1, costo 100)",
                      cargar_golden("estado.txt"), flags=re.MULTILINE)
    assert "costo 100" in esperado
    assert obtenido == esperado


class _VistaFalsa:
    def __init__(self):
        self.estados = []
        self.finales = []

    def mostrar_estado(self, estado):
        self.estados.append(estado)

    def pedir_comando(self):
        return "salir"

    def mostrar_mensaje(self, texto):
        pass

    def mostrar_final(self, resumen):
        self.finales.append(resumen)


def test_el_controlador_pasa_un_estado_vista_dto_a_la_vista():
    """FR-010 · mostrar_estado recibe EstadoVistaDTO, no Partida."""
    servicio, _ = armar_estado_fijo()
    vista = _VistaFalsa()
    Controlador(servicio, vista, None, None).jugar()
    assert len(vista.estados) == 1
    assert isinstance(vista.estados[0], EstadoVistaDTO)
