"""Frontera del servicio (T027 · Constitución III · FR-010, FR-014)."""
from pathlib import Path

import pytest

from controller.controlador import Controlador
from dto.resumen_final_dto import ResumenFinalDTO
from tests.estado_fijo import armar_estado_fijo, cargar_golden
from view.vista_consola import VistaConsola

RAIZ = Path(__file__).resolve().parent.parent


def _sin_modelo(valor, ruta="valor"):
    """Recorre atributos y listas; ninguna instancia puede venir de model/."""
    modulo = type(valor).__module__
    assert not modulo.startswith("model"), f"{ruta} es de {modulo}"
    if isinstance(valor, (list, tuple)):
        for i, x in enumerate(valor):
            _sin_modelo(x, f"{ruta}[{i}]")
    elif hasattr(valor, "__dict__"):
        for nombre, x in vars(valor).items():
            _sin_modelo(x, f"{ruta}.{nombre}")


def test_las_salidas_del_servicio_no_son_del_modelo():
    """FR-010 · FR-014 · ninguna salida del servicio es una clase de model/."""
    servicio, _ = armar_estado_fijo()
    salidas = {
        "estado_vista": servicio.estado_vista(),
        "resumen_final": servicio.resumen_final(),
        "inventario_vista": servicio.inventario_vista(),
        "objetos_en_sala": servicio.objetos_en_sala(),
        "enemigos_en_sala": servicio.enemigos_en_sala(),
    }
    for criterio in ("peso", "valor", "nombre"):
        salidas[f"vista_ordenada({criterio})"] = servicio.vista_ordenada(criterio)
    for nombre, valor in salidas.items():
        _sin_modelo(valor, nombre)
    assert len(servicio.objetos_en_sala()) == 2
    assert len(servicio.vista_ordenada("peso")) == 3


def test_terminada_es_bool_y_semilla_es_int():
    """FR-014 · tipos simples."""
    servicio, partida = armar_estado_fijo()
    assert servicio.terminada() is False
    assert isinstance(servicio.semilla(), int)
    assert servicio.semilla() == partida.semilla
    servicio, _ = armar_estado_fijo("muerte")
    assert servicio.terminada() is True


def test_enemigos_en_sala_solo_vivos_de_la_sala_del_jugador():
    """FR-010 · filtro de ataque: vivos, en la sala, en orden de partida.enemigos."""
    servicio, partida = armar_estado_fijo()
    rata = partida.enemigos[0]
    ids = [e.id_enemigo for e in servicio.enemigos_en_sala()]
    assert ids == ["r1"]
    rata.vida = 0
    assert servicio.enemigos_en_sala() == []


def test_atacar_por_id():
    """FR-006 · atacar(id) True con enemigo vivo en la sala; False con id desconocido."""
    servicio, partida = armar_estado_fijo()
    rata = partida.enemigos[0]
    vida = rata.vida
    reloj = partida.reloj
    assert servicio.atacar("x") is False
    assert rata.vida == vida and partida.reloj == reloj
    assert servicio.atacar("R1") is True
    assert rata.vida < vida or not rata.esta_vivo()


def test_el_controlador_no_lee_el_modelo():
    """FR-010 · el texto de controlador.py no contiene .partida ni from model."""
    texto = (RAIZ / "controller" / "controlador.py").read_text(encoding="utf-8")
    assert ".partida" not in texto
    assert "from model" not in texto


class _VistaFalsa:
    def __init__(self):
        self.finales = []

    def mostrar_estado(self, estado):
        pass

    def pedir_comando(self):
        return "salir"

    def mostrar_mensaje(self, texto):
        pass

    def mostrar_final(self, resumen):
        self.finales.append(resumen)


def test_mostrar_final_recibe_resumen_final_dto():
    """FR-010 · mostrar_final recibe ResumenFinalDTO, no Partida."""
    servicio, _ = armar_estado_fijo()
    vista = _VistaFalsa()
    Controlador(servicio, vista, None, None).jugar()
    assert len(vista.finales) == 1
    assert isinstance(vista.finales[0], ResumenFinalDTO)


@pytest.mark.parametrize("final", ["victoria", "muerte", "salida"])
def test_golden_final_consola(final, capsys):
    """FR-010 · FR-014 · mostrar_final igual al golden de la parte uno."""
    servicio, _ = armar_estado_fijo(final)
    VistaConsola().mostrar_final(servicio.resumen_final())
    assert capsys.readouterr().out == cargar_golden(f"final_consola_{final}.txt")


def test_golden_inventario(capsys):
    """FR-010 · mostrar_inventario igual al golden."""
    servicio, _ = armar_estado_fijo()
    VistaConsola().mostrar_inventario(servicio.inventario_vista())
    assert capsys.readouterr().out == cargar_golden("inventario.txt")


@pytest.mark.parametrize("criterio", ["peso", "valor", "nombre"])
def test_golden_inventario_ordenado(criterio, capsys):
    """FR-010 · mostrar_inventario_ordenado igual al golden."""
    servicio, _ = armar_estado_fijo()
    VistaConsola().mostrar_inventario_ordenado(servicio.vista_ordenada(criterio), criterio)
    assert capsys.readouterr().out == cargar_golden(f"inventario_{criterio}.txt")
