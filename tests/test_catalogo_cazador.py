from model.enemigo_logica import Enemigo
from model.sala_logica import Sala


def _enemigo(comportamiento, **extra):
    return Enemigo(1, "t", "N", 10, 10, 1, 1, 100, comportamiento, Sala(1, "A"), **extra)


def test_rango_se_guarda_y_por_defecto_es_cero():
    """FR-001 · Enemigo.rango."""
    assert _enemigo("cazador", rango=300).rango == 300
    assert _enemigo("cazador").rango == 0


def test_es_cazador_solo_para_cazador():
    """FR-001 · es_cazador()."""
    assert _enemigo("cazador").es_cazador() is True
    for otro in ("errante", "rastreador", "guardián"):
        assert _enemigo(otro).es_cazador() is False
