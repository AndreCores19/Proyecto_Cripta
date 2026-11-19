import ast
import os
import random

import pytest

from structures.linea_tiempo import LineaTiempo


def _vector(semilla, n, k=10):
    azar = random.Random(semilla)
    linea = LineaTiempo(k)
    reloj = azar.randint(0, 5)
    for i in range(n):
        linea.agregar_accion(reloj, "esperar")
        reloj += azar.randint(1, 40)
    return linea


def _lineal(relojes, t):
    resultado = -1
    for i in range(len(relojes)):
        if relojes[i] <= t:
            resultado = i
    return resultado


@pytest.mark.parametrize("semilla", range(6))
def test_ultimo_menor_o_igual_coincide_con_el_recorrido_lineal(semilla):
    """FR-022 · búsqueda por reloj (por debajo, en y por encima de los relojes)"""
    linea = _vector(semilla, 50 + semilla * 37)
    ultimo = linea.relojes[-1]
    for t in range(-3, ultimo + 5):
        assert linea.ultimo_menor_o_igual(t) == _lineal(linea.relojes, t)
    assert linea.ultimo_menor_o_igual(linea.relojes[0] - 1) == -1
    assert linea.ultimo_menor_o_igual(linea.relojes[0]) == 0
    assert linea.ultimo_menor_o_igual(ultimo + 1000) == len(linea) - 1


def test_ultimo_menor_o_igual_en_un_vector_vacio():
    """FR-022"""
    assert LineaTiempo(5).ultimo_menor_o_igual(10) == -1


def _comparaciones_medias(n):
    linea = LineaTiempo(10)
    for i in range(n):
        linea.agregar_accion(i * 3, "esperar")
    azar = random.Random(n)
    busquedas = 200
    for _ in range(busquedas):
        linea.ultimo_menor_o_igual(azar.randint(0, n * 3))
    return linea.comparaciones / busquedas


def test_las_comparaciones_crecen_como_log2_n():
    """FR-022 · O(log n): de 1 000 a 100 000 la cuenta sube una constante pequeña, no 100 veces"""
    chico = _comparaciones_medias(1_000)
    grande = _comparaciones_medias(100_000)
    assert chico <= 11 and grande <= 18
    assert 3 <= grande - chico <= 10
    assert grande / chico < 3


def test_los_relojes_deben_ser_estrictamente_crecientes():
    """FR-019 · reloj repetido o menor"""
    linea = LineaTiempo(3)
    linea.agregar_accion(5, "mover", "N")
    for malo in (5, 4, 0):
        with pytest.raises(ValueError):
            linea.agregar_accion(malo, "esperar")
    assert len(linea) == 1
    linea.agregar_accion(6, "esperar")
    assert len(linea) == 2


def test_recortar_solo_quita_del_final_y_deja_intactos_los_primeros():
    """FR-011 · recortar(n)"""
    linea = _vector(1, 40, k=5)
    for i in range(0, 41, 5):
        while len(linea.puntos) * 5 <= i and len(linea.puntos) * 5 <= len(linea):
            linea.agregar_punto(("estado", len(linea.puntos) * 5))
    antes = (list(linea.relojes[:17]), list(linea.tipos[:17]), list(linea.argumentos[:17]))
    linea.recortar(17)
    assert len(linea) == 17
    assert (linea.relojes, linea.tipos, linea.argumentos) == antes
    assert [p[1] for p in linea.puntos] == [0, 5, 10, 15]      #los puntos con frontera <= 17
    linea.recortar(17)                                          #recortar a lo mismo no cambia nada
    assert len(linea) == 17
    linea.recortar(0)
    assert len(linea) == 0 and len(linea.puntos) == 1
    with pytest.raises(ValueError):
        linea.recortar(1)


@pytest.mark.parametrize("k", [1, 3, 7, 100])
def test_la_cantidad_de_puntos_no_supera_a_entre_k_mas_uno(k):
    """FR-019 · len(puntos) <= A // K + 1 y ninguno fuera de la cuadrícula"""
    linea = LineaTiempo(k)
    linea.agregar_punto(("estado", 0))
    reloj = 0
    for acciones in range(1, 80):
        linea.agregar_accion(reloj, "esperar")
        reloj += 1
        if acciones % k == 0:
            linea.agregar_punto(("estado", acciones))
        assert len(linea.puntos) <= acciones // k + 1
    for i in range(len(linea.puntos)):
        assert linea.puntos[i] == ("estado", i * k)
    with pytest.raises(ValueError):                             #un punto de más queda fuera de la cuadrícula
        for _ in range(100):
            linea.agregar_punto(("de más",))


def test_punto_para_usa_la_casilla_frontera_entre_k():
    """FR-020 · punto_para(frontera) = casilla frontera // K"""
    linea = LineaTiempo(4)
    linea.agregar_punto("p0")
    for i in range(1, 10):
        linea.agregar_accion(i, "esperar")
        if i % 4 == 0:
            linea.agregar_punto(f"p{i // 4}")
    assert [linea.punto_para(b) for b in range(0, 9)] == ["p0"] * 4 + ["p1"] * 4 + ["p2"]
    with pytest.raises(IndexError):
        linea.punto_para(12)


@pytest.mark.parametrize("k", [0, -1, 2.5, "3", None, True])
def test_k_debe_ser_un_entero_positivo(k):
    """FR-011 · K inválido"""
    with pytest.raises(ValueError):
        LineaTiempo(k)


MODULOS_LINEA_TIEMPO = ("structures/linea_tiempo.py", "model/registro_estado.py", "model/reproduccion_logica.py",
                        "model/linea_tiempo_logica.py", "model/efectos_omitidos.py", "data/fabrica_reproduccion.py",
                        "service/historia_service.py", "data/grafo_reutilizable.py", "data/fichas_congeladas.py")
MODULOS_PROHIBIDOS = ("heapq", "bisect", "collections", "copy")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _arbol(ruta):
    with open(os.path.join(RAIZ, ruta), encoding="utf-8") as f:
        return ast.parse(f.read(), filename=ruta)


def _importados(arbol):
    """Los módulos que importa un archivo (`import a.b` y `from a.b import c` dan "a.b")."""
    nombres = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module is not None:
            nombres.append(nodo.module)
    return nombres


def _usos_prohibidos(arbol):
    """dict/set: literales, comprensiones y llamadas a `dict(` / `set(` (lo que podría servir de índice)."""
    usos = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp)):
            usos.append((type(nodo).__name__, nodo.lineno))
        elif (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
              and nodo.func.id in ("dict", "set", "frozenset")):
            usos.append((nodo.func.id + "(", nodo.lineno))
    return usos


@pytest.mark.parametrize("ruta", MODULOS_LINEA_TIEMPO)
def test_modulos_sin_prohibidos(ruta):
    """FR-028, FR-029, SC-001 · los módulos de la línea de tiempo no importan heapq, bisect, collections ni copy
    y no usan dict ni set (literal, comprensión o llamada)"""
    arbol = _arbol(ruta)
    for nombre in _importados(arbol):
        assert nombre.split(".")[0] not in MODULOS_PROHIBIDOS, (ruta, nombre)
    assert _usos_prohibidos(arbol) == [], ruta


def test_modulos_sin_prohibidos_model_y_structures_no_importan_view_ni_controller():
    """FR-029 · ningún archivo de model/ ni de structures/ importa de view/ ni de controller/"""
    revisados = 0
    for carpeta in ("model", "structures"):
        for nombre in sorted(os.listdir(os.path.join(RAIZ, carpeta))):
            if not nombre.endswith(".py"):
                continue
            ruta = f"{carpeta}/{nombre}"
            for importado in _importados(_arbol(ruta)):
                assert importado.split(".")[0] not in ("view", "controller"), (ruta, importado)
            revisados += 1
    assert revisados > 10


def test_el_detector_de_prohibidos_ve_lo_que_debe():
    """FR-028 · control del detector: encuentra cada forma prohibida en un texto de ejemplo"""
    ejemplo = ast.parse("import heapq\nfrom collections import deque\nfrom copy import deepcopy\n"
                        "a = {}\nb = {1}\nc = dict()\nd = set()\ne = {k: k for k in x}\nf = {k for k in x}\n"
                        "g = f'{a:>3}'\n")
    assert [n.split(".")[0] for n in _importados(ejemplo)] == ["heapq", "collections", "copy"]
    assert [u[0] for u in _usos_prohibidos(ejemplo)] == ["Dict", "Set", "dict(", "set(", "DictComp", "SetComp"]


def test_sin_dict_set_ni_modulos_prohibidos_en_la_estructura():
    """FR-028 · la estructura no importa ni usa lo prohibido"""
    import structures.linea_tiempo as modulo
    texto = open(modulo.__file__, encoding="utf-8").read()
    for prohibido in ("import heapq", "import bisect", "import collections", "import copy",
                      "from heapq", "from bisect", "from collections", "from copy", "dict(", "set(", "{}"):
        assert prohibido not in texto, prohibido
