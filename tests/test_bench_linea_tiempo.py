"""El benchmark de la línea de tiempo y el del historial bajo la nueva carga (spec 005, Fases 10 y 11).

Tamaños chicos (300 acciones); la corrida completa de 5 000 acciones es la prueba marcada `lenta`
(T069), que solo corre con `-m lenta`. Sin red y sin vista.
"""
import os
import re

import pytest

from bench import bench_historial, bench_linea_tiempo
from bench.bench_linea_tiempo import SIN_PUNTOS, elegir_k, p99
from bench.juego_sintetico import MundoSintetico, jugar
from model.linea_tiempo_logica import K_POR_DEFECTO

CHICO = 300
BENCH_ANTES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "specs", "005-timeline", "bench-antes.txt")


def _prohibir_red_y_vistas(monkeypatch):
    import adapters.cliente_http
    import view.vista_consola
    import view.vista_silenciosa

    def prohibido(self, *args, **kwargs):
        raise AssertionError("el benchmark creó un cliente de red o una vista")
    monkeypatch.setattr(adapters.cliente_http.ClienteHttp, "__init__", prohibido)
    for modulo in (view.vista_consola, view.vista_silenciosa):
        for nombre in dir(modulo):
            clase = getattr(modulo, nombre)
            if isinstance(clase, type) and clase.__module__ == modulo.__name__:
                monkeypatch.setattr(clase, "__init__", prohibido)


@pytest.fixture(scope="module")
def reporte():
    """Una corrida chica del benchmark en el mundo de referencia: (K elegido, mediciones, líneas)."""
    lineas = []
    elegido, resultados = bench_linea_tiempo.ejecutar(acciones=CHICO, consultas=20, consultas_sin_puntos=4,
                                                      mundos=("referencia",), imprimir=lineas.append)
    return elegido, resultados, lineas


# ---------------------------------------------------------------- US7-3, US8-5: determinismo (FR-025)

@pytest.mark.parametrize("nombre", ["referencia", "grande"])
def test_la_partida_sintetica_es_la_misma_con_la_misma_semilla_y_otra_con_otra(nombre):
    """FR-025 · US7-3, US8-5 · dos veces la misma semilla: los mismos comandos y el mismo estado final"""
    mundo = MundoSintetico(nombre)
    a, b = jugar(nombre, 3, CHICO, 50, mundo), jugar(nombre, 3, CHICO, 50, mundo)
    otra = jugar(nombre, 4, CHICO, 50, mundo)
    assert a.comandos == b.comandos
    assert a.partida.acciones_jugador == b.partida.acciones_jugador == CHICO
    final = lambda j: (j.partida.reloj, j.partida.jugador.sala.id, j.partida.retrocesos,
                       [(e.id_enemigo, e.sala.id, e.vida) for e in j.partida.enemigos])
    assert final(a) == final(b)
    assert otra.comandos != a.comandos
    assert a.lecturas >= 1, "la partida sintética lee al menos un pergamino"


# ---------------------------------------------------------------- US8-1, US8-2, US8-4: el reporte (FR-026)

def test_el_reporte_tiene_una_fila_por_k_la_fila_none_las_columnas_y_la_linea_del_k_por_defecto(reporte):
    """FR-026 · US8-1, US8-2, US8-4 · filas K=10, 50, 200 y none, columnas del contrato y una línea
    "Default K" que nombra la fila de la que sale"""
    elegido, _, lineas = reporte
    texto = "\n".join(lineas)
    assert "== Timeline: memory and query time (world=referencia" in texto
    for columna in ("checkpoints", "memory checkpoints", "memory actions + ledger", "graph build",
                    "max actions re-played", "p99 (ms)", "mean (ms)", "worst (ms)", "verdict p99 <= 50 ms"):
        assert columna in texto
    filas = [linea.split("|")[0].strip() for linea in lineas if re.match(r"^\s*(10|50|200|none) \|", linea)]
    assert filas == ["10", "50", "200", "none"]
    defecto = [linea for linea in lineas if linea.startswith("Default K:")]
    assert len(defecto) == 1
    if elegido is None:
        assert "the group decides" in defecto[0]
    else:
        assert f"-> row K={elegido}" in defecto[0]
    assert any(linea.startswith("Linearity") for linea in lineas)
    assert any("checkpoints off the K grid=0" in linea for linea in lineas)


def test_ninguna_fila_reproduce_mas_de_k_y_la_fila_none_reproduce_toda_la_partida(reporte):
    """FR-020 · SC-008 · en cada fila K el máximo de acciones reproducidas es <= K; en `none`, la partida entera"""
    _, resultados, _ = reporte
    _, mediciones = resultados[0]
    for m in mediciones:
        if m.k == SIN_PUNTOS:
            assert m.max_reproducidas == CHICO and m.puntos == 1
        else:
            assert m.max_reproducidas <= m.k
            assert m.puntos == CHICO // m.k + 1


def test_la_memoria_crece_lineal_con_las_acciones():
    """FR-021, FR-026 · US6-3 · la misma semilla con A y 2A acciones y K fijo: razón de memoria entre 1.5 y 2.5"""
    m1, m2 = bench_linea_tiempo.medir_linealidad("referencia", 10, CHICO)
    assert 1.5 <= m2 / m1 <= 2.5, (m1, m2)


def test_el_benchmark_no_pide_nada_a_la_red_ni_crea_vistas(monkeypatch):
    """FR-016, FR-024 · US7-2 · sin cliente de red ni clases de view/ (el esqueleto sale del paquete offline)"""
    _prohibir_red_y_vistas(monkeypatch)
    lineas = []
    bench_linea_tiempo.ejecutar(acciones=60, consultas=5, consultas_sin_puntos=2, mundos=("referencia", "grande"),
                                imprimir=lineas.append)
    assert any(linea.startswith("Default K:") for linea in lineas)


def test_el_p99_usa_el_indice_del_contrato_y_las_consultas_cubren_toda_la_partida():
    """FR-024 · p99 = ordenados[int(n·0.99)]; el conjunto incluye el instante más viejo y el más reciente"""
    assert p99(list(range(100, 0, -1))) == 100                     #n=100: índice 99
    assert p99(list(range(200))) == 198                             #n=200: índice 198
    juego = jugar("grande", 3, 80, 10)
    lista = bench_linea_tiempo.instantes(juego, 30, 5)
    assert len(lista) == 30 and 0 in lista and juego.partida.reloj in lista
    assert lista == bench_linea_tiempo.instantes(juego, 30, 5)      #por semilla


def test_la_regla_del_k_por_defecto_sobre_tablas_inventadas():
    """FR-026 · el mayor K con p99 <= 25 ms; la fila none no cuenta; si ninguno cumple, None (decide el grupo)"""
    assert elegir_k([(10, 3.0), (50, 12.0), (200, 40.0), (SIN_PUNTOS, 900.0)]) == 50
    assert elegir_k([(10, 3.0), (50, 12.0), (200, 25.0)]) == 200
    assert elegir_k([(200, 5.0), (10, 30.0), (50, 20.0)]) == 200
    assert elegir_k([(10, 26.0), (50, 40.0), (200, 90.0), (SIN_PUNTOS, 1.0)]) is None
    texto = bench_linea_tiempo.linea_k_por_defecto([])[1]
    assert "the group decides" in texto


# ---------------------------------------------------------------- T064: adelante vs atrás (FR-026, FR-027)

def test_adelante_contra_atras_sale_de_una_corrida(reporte):
    """FR-026, FR-027 · costo por acción reproducida, por acción invertida, cierres por acción y bytes
    extrapolados: números medidos, no constantes"""
    adelante, atras, cierres, extrapolado = bench_linea_tiempo.adelante_atras("referencia", 120)
    assert adelante > 0 and atras > 0 and cierres > 0 and extrapolado > 0
    _, _, lineas = reporte
    texto = "\n".join(lineas)
    assert re.search(r"re-simulate forward [0-9.]+ us/action \| invert backward [0-9.]+ us/action", texto)
    assert re.search(r"closures per action in Historial [0-9.]+ \| extrapolated bytes at A=5000 actions \d+ KB",
                     texto)


# ---------------------------------------------------------------- T069: US7-1 a tamaño completo (lenta)

@pytest.mark.lenta
def test_p99_con_el_k_por_defecto_en_5000_acciones_de_referencia():
    """FR-024 · SC-006 · US7-1 · con el K por defecto, 5 000 acciones en `referencia`: p99 <= 50 ms"""
    _, m = bench_linea_tiempo.medir("referencia", K_POR_DEFECTO, 5000, 200)
    print(f"K={K_POR_DEFECTO}: p99={m.p99:.2f} ms, peor={m.peor:.2f} ms, promedio={m.promedio:.2f} ms")
    assert m.max_reproducidas <= K_POR_DEFECTO
    assert m.p99 <= 50


# ---------------------------------------------------------------- T070: el historial de la parte uno bajo la nueva carga (FR-027)

def _antes():
    """Las filas de bench-antes.txt: escenario -> (acción, deshacer)."""
    filas = {}
    with open(BENCH_ANTES, encoding="utf-8") as f:
        for linea in f:
            partes = linea.split()
            if len(partes) == 9 and partes[0] in ("pequeño", "larga", "normal", "grande", "extremo"):
                filas[partes[0]] = (float(partes[3]), float(partes[5]))
    return filas


def test_el_historial_imprime_la_parte_uno_junto_a_la_linea_de_tiempo(capsys, monkeypatch):
    """FR-027 · US8-3 · bench_historial: por escenario, la parte uno (sin línea de tiempo, medida en vivo) junto a la
    línea de tiempo activa (acción, deshacer, cierres guardados, máximo 5 cuadros) y "capture checkpoint (us)"
    en lugar de "copiar todo". Solo estructura: la comparación de tiempos con bench-antes.txt queda en el
    reporte del benchmark (un umbral de tiempo aquí fallaba con la máquina cargada)"""
    monkeypatch.setattr(bench_historial, "REPETICIONES", 60)
    filas = bench_historial.ejecutar()
    salida = capsys.readouterr().out
    assert "copiar todo" not in salida
    for columna in ("action (part one)", "action (timeline)", "undo (part one)", "undo (timeline)",
                    "closures kept (max 5 frames)", "capture checkpoint (us)"):
        assert columna in salida
    antes = _antes()
    assert [f[0] for f in filas] == ["pequeño", "larga", "normal", "grande", "extremo"]
    for nombre, accion_uno, accion_linea, deshacer_uno, deshacer_linea, cierres, cuadros, captura in filas:
        assert nombre in antes, f"bench-antes.txt no tiene la fila {nombre}"
        assert cuadros <= 5 and cierres > 0 and captura > 0
        assert accion_uno > 0 and deshacer_uno > 0
        assert accion_linea > 0 and deshacer_linea > 0
