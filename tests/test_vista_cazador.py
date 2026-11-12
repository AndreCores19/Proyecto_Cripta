"""La vista de sala marca a los cazadores y deja igual el resto (US6 · FR-016)."""
import re

from dto.estado_vista_dto import EnemigoVistaDTO, EstadoVistaDTO
from model.enemigo_logica import Enemigo
from tests.estado_fijo import armar_estado_fijo, cargar_golden
from view.vista_consola import VistaConsola


def _con_enemigos(*comportamientos):
    """Estado fijo con un enemigo activo por cada comportamiento, en la sala del jugador."""
    servicio, partida = armar_estado_fijo()
    sala = partida.jugador.sala
    nombres = {"cazador": ("Lobo", "e3"), "errante": ("Rata", "e1"), "rastreador": ("Sombra", "e2")}
    for comp in comportamientos:
        nombre, id_enemigo = nombres[comp]
        partida.enemigos.append(Enemigo(id_enemigo, "t", nombre, 12, 20 if comp == "cazador" else 15,
                                        3, 0, 100, comp, sala, rango=100))
    return servicio


def _imprimir(servicio, capsys):
    VistaConsola().mostrar_estado(servicio.estado_vista())
    return capsys.readouterr().out


def test_us6_1_el_cazador_se_marca_y_el_errante_no(capsys):
    """FR-016 · US6-1"""
    servicio = _con_enemigos("cazador", "errante")
    marcas = {e.id_enemigo: e.cazador for e in servicio.estado_vista().enemigos}
    assert marcas == {"r1": False, "e3": True, "e1": False}
    salida = _imprimir(servicio, capsys)
    assert "  Lobo (cazador) [e3] (Vida: 12/20)\n" in salida
    assert "  Rata [e1] (Vida: 12/15)\n" in salida
    assert salida.count("(cazador)") == 1


def test_us6_2_sin_cazadores_la_sala_se_imprime_como_en_la_parte_uno(capsys):
    """FR-016, FR-013 · US6-2: igual al golden de estado.txt con sus costos más las líneas de los enemigos."""
    salida = _imprimir(_con_enemigos("errante", "rastreador"), capsys)
    esperado = re.sub(r"^(  \w+ -> .+ \((?:abierta|cerrada))\)$", r"\1, costo 100)",
                      cargar_golden("estado.txt"), flags=re.MULTILINE)
    linea_golden = "  Rata [r1] (Vida: 12/15) [velocidad]\n"  # el estado fijo ya trae esta rata
    assert esperado.count(linea_golden) == 1
    esperado = esperado.replace(
        linea_golden, linea_golden + "  Rata [e1] (Vida: 12/15)\n  Sombra [e2] (Vida: 12/15)\n")
    assert salida == esperado
    assert "(cazador)" not in salida


def test_enemigo_vista_dto_sin_el_campo_nuevo_sigue_funcionando():
    """FR-016 · el valor por defecto de `cazador` es False."""
    assert EnemigoVistaDTO("Rata", "r1", 5, 10, []).cazador is False


def test_enemigos_en_sala_tambien_llena_el_campo_y_la_vista_no_recibe_modelo():
    """FR-016 · enemigos_en_sala() marca al cazador; el DTO no guarda objetos del modelo."""
    servicio = _con_enemigos("cazador", "errante")
    marcas = {e.id_enemigo: e.cazador for e in servicio.enemigos_en_sala()}
    assert marcas == {"r1": False, "e3": True, "e1": False}
    estado = servicio.estado_vista()
    assert isinstance(estado, EstadoVistaDTO)
    for e in estado.enemigos:
        assert isinstance(e, EnemigoVistaDTO)
        assert not any(isinstance(v, Enemigo) for v in vars(e).values())
    assert not any(isinstance(v, Enemigo) for v in vars(estado).values())
