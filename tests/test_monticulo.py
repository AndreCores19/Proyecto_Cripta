"""Pruebas del montículo mínimo genérico (spec 002, fase 2)."""
import os
import random

from structures.monticulo import MonticuloMinimo


def vaciado(m):
    salida = []
    while len(m) > 0:
        salida.append(m.extraer())
    return salida


def test_orden_igual_a_lista_ordenada():
    """FR-003 · FR-007 · Constitución I: 1000 prioridades aleatorias salen ordenadas."""
    azar = random.Random(5)
    valores = [azar.randint(0, 10**6) for _ in range(1000)]
    m = MonticuloMinimo()
    for v in valores:
        m.insertar(v, v)
    assert [p for p, _ in vaciado(m)] == sorted(valores)


def test_prioridades_iguales_salen_en_orden_de_insercion():
    """FR-014 · Constitución II: a igual prioridad, el primero insertado sale primero."""
    m = MonticuloMinimo()
    for i in range(20):
        m.insertar(i % 3, i)
    esperado = [i for p in range(3) for i in range(20) if i % 3 == p]
    assert [v for _, v in vaciado(m)] == esperado


def test_prioridades_tupla():
    """FR-007 · Constitución II: las tuplas se ordenan lexicográficamente."""
    m = MonticuloMinimo()
    m.insertar((2, 1), "a")
    m.insertar((1, 9), "b")
    m.insertar((1, 3), "c")
    assert [p for p, _ in vaciado(m)] == [(1, 3), (1, 9), (2, 1)]


def test_vacio_devuelve_none_y_len_sigue_operaciones():
    """FR-007: extraer y proximo en vacío dan None; len sigue inserciones y extracciones."""
    m = MonticuloMinimo()
    assert m.extraer() is None
    assert m.proximo() is None
    assert len(m) == 0
    m.insertar(3, "x")
    m.insertar(1, "y")
    assert len(m) == 2
    m.extraer()
    assert len(m) == 1
    m.extraer()
    assert len(m) == 0
    assert m.extraer() is None


def test_proximo_no_quita():
    """FR-007: proximo mira sin extraer."""
    m = MonticuloMinimo()
    m.insertar(5, "a")
    m.insertar(2, "b")
    assert m.proximo() == (2, "b")
    assert m.proximo() == (2, "b")
    assert len(m) == 2


def test_vaciar_reinicia_como_uno_nuevo():
    """FR-014 · Constitución II: tras vaciar, el orden es el de un montículo nuevo."""
    entradas = [(1, "a"), (0, "b"), (1, "c"), (0, "d"), (2, "e")]
    usado = MonticuloMinimo()
    for p, v in [(9, "z"), (9, "y"), (4, "w")]:
        usado.insertar(p, v)
    usado.extraer()
    usado.vaciar()
    assert len(usado) == 0
    nuevo = MonticuloMinimo()
    for p, v in entradas:
        usado.insertar(p, v)
        nuevo.insertar(p, v)
    assert vaciado(usado) == vaciado(nuevo)


def test_desempate_explicito_en_la_prioridad():
    """FR-014 · Constitución II: quien necesita desempate lo pone en la prioridad."""
    for orden in ([(2, 7), (2, 3)], [(2, 3), (2, 7)]):
        m = MonticuloMinimo()
        for p in orden:
            m.insertar(p, None)
        assert [p for p, _ in vaciado(m)] == [(2, 3), (2, 7)]


def test_sin_modulos_prohibidos():
    """FR-018 · Constitución I: el módulo no importa heapq, bisect ni collections."""
    ruta = os.path.join(os.path.dirname(__file__), "..", "structures", "monticulo.py")
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    for prohibido in ("heapq", "bisect", "collections"):
        assert prohibido not in texto
