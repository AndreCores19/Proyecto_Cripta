"""Salida de --replay sin clases de view/ (T034 · FR-012, FR-014, Constitución III).

La salida debe ser idéntica a los golden files de la parte uno (T003).
"""
import importlib.util

import pytest

from adapters.salida_replay import imprimir_final_replay, imprimir_reporte
from aplicacion import Aplicacion
from tests.estado_fijo import AppFalsa, LectorFalso, armar_estado_fijo, cargar_golden
from view.vista_consola import VistaConsola
from view.vista_silenciosa import VistaSilenciosa

V = "v1"
COMANDOS = ["w", "d", "esperar", "zz"]


@pytest.mark.parametrize("final", ["victoria", "muerte", "salida"])
def test_final_replay_igual_al_golden(final, capsys):
    """FR-014 · salida del final de --replay (Constitución III)"""
    servicio, _ = armar_estado_fijo(final)
    imprimir_final_replay(servicio.resumen_final())
    assert capsys.readouterr().out == cargar_golden(f"final_replay_{final}.txt")


def test_reporte_replay_igual_al_golden(capsys):
    """FR-014 · reporte con presupuesto"""
    imprimir_reporte(12, 50, 7, 3)
    assert capsys.readouterr().out == cargar_golden("reporte_replay.txt")


def test_reporte_replay_sin_presupuesto_igual_al_golden(capsys):
    """FR-014 · reporte sin presupuesto ni aciertos"""
    imprimir_reporte(12, None, 0, 0)
    assert capsys.readouterr().out == cargar_golden("reporte_replay_sin_presupuesto.txt")


def _prohibir_vistas(monkeypatch):
    def prohibido(self, *args, **kwargs):
        raise AssertionError("vista instanciada en --replay")
    monkeypatch.setattr(VistaConsola, "__init__", prohibido)
    monkeypatch.setattr(VistaSilenciosa, "__init__", prohibido)


def test_reproducir_sin_vistas_igual_al_golden(monkeypatch, capsys):
    """FR-012, FR-014 · replay completo sin instanciar view/"""
    _prohibir_vistas(monkeypatch)
    Aplicacion.reproducir(AppFalsa(V, V), LectorFalso(1, COMANDOS, V, V))
    assert capsys.readouterr().out == cargar_golden("replay_completo.txt")


def test_reproducir_version_distinta_igual_al_golden(monkeypatch, capsys):
    """FR-012 · versión distinta: mismo mensaje y sin vistas"""
    _prohibir_vistas(monkeypatch)
    Aplicacion.reproducir(AppFalsa(V, V), LectorFalso(1, COMANDOS, "v0", V))
    assert capsys.readouterr().out == cargar_golden("replay_version.txt")


def test_vista_replay_eliminada_y_silenciosa_independiente():
    """FR-014 · la vista de replay ya no existe y VistaSilenciosa no hereda de nada"""
    assert importlib.util.find_spec("view.vista_replay") is None
    assert VistaSilenciosa.__mro__ == (VistaSilenciosa, object)
