"""El comando `inv` escrito en el controlador con la vista real imprime el inventario (bug de T049 · FR-010, FR-014)."""
from controller.controlador import Controlador
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from model.sala_logica import Sala
from service.juego_service import JuegoService
from tests.estado_fijo import FabricaFalsa, armar_estado_fijo, cargar_golden
from view.vista_consola import VistaConsola

# Lo que imprimía la parte uno (commit bc7cfd7, view/vista_consola.py) con un inventario vacío de capacidad 10.
INVENTARIO_VACIO_PARTE1 = "Inventario (0/10):\n  (vacío)\n"


def test_inv_con_objetos_imprime_el_golden(capsys):
    servicio, _ = armar_estado_fijo()
    Controlador(servicio, VistaConsola(), None, None).ejecutar("inv")
    assert capsys.readouterr().out == cargar_golden("inventario.txt")


def test_inv_con_el_inventario_vacio_imprime_lo_de_la_parte_uno(capsys):
    jugador = Jugador(vida_max=50, ataque=10, defensa=1, velocidad=100,
                      inventario_max=10, sala=Sala(1, "Entrada"))
    servicio = JuegoService(Partida(jugador, semilla=1), FabricaFalsa())
    Controlador(servicio, VistaConsola(), None, None).ejecutar("inv")
    assert capsys.readouterr().out == INVENTARIO_VACIO_PARTE1
