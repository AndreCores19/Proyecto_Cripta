"""Los benchmarks del cazador: forma de la salida, reproducibilidad y aislamiento de la vista (US7)."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

from bench import bench_cazador, bench_ciclo
from model.ruta_cazador import Busqueda

RAIZ = Path(__file__).resolve().parent.parent


def _escenarios_chicos(monkeypatch):
    monkeypatch.setattr(bench_ciclo, "ESCENARIOS", (
        ("normal", 5, 8, 0),
        ("cazadores", 10, 20, 3),
        ("cazadores_rango_total", 10, 20, 3),
    ))
    monkeypatch.setattr(bench_ciclo, "ACCIONES", 20)


def test_us7_1_el_ciclo_con_cazadores_imprime_promedio_p99_peor_y_veredicto(monkeypatch, capsys):
    """FR-017 · US7-1"""
    _escenarios_chicos(monkeypatch)
    bench_ciclo.ejecutar()
    lineas = capsys.readouterr().out.splitlines()
    for nombre in ("cazadores", "cazadores_rango_total"):
        linea = next(l for l in lineas if l.split()[:1] == [nombre])
        numeros = re.findall(r"\d+\.\d{3}", linea)
        assert len(numeros) == 3, linea  # promedio, p99 y peor ciclo
        assert linea.rstrip().endswith("cumple")


@pytest.mark.parametrize("p99,veredicto", [(20.0, "cumple"), (20.001, "NO cumple")])
def test_us7_1_el_veredicto_usa_menor_o_igual(monkeypatch, capsys, p99, veredicto):
    """FR-017 · US7-1: un p99 de exactamente 20.0 ms cumple."""
    monkeypatch.setattr(bench_ciclo, "ESCENARIOS", (("cazadores", 10, 20, 3),))
    monkeypatch.setattr(bench_ciclo, "medir_ciclos", lambda partida: [p99] * 100)
    bench_ciclo.ejecutar()
    linea = next(l for l in capsys.readouterr().out.splitlines() if l.split()[:1] == ["cazadores"])
    assert linea.rstrip().endswith(veredicto)
    if veredicto == "cumple":
        assert not linea.rstrip().endswith("NO cumple")


def test_us7_2_el_escalado_compara_dos_criptas_con_la_misma_region():
    """FR-018 · US7-2 · SC-008"""
    chica, grande, razon = bench_cazador.escalado(40, 120, 200, 1)
    assert chica > 0 and grande > 0
    assert razon == pytest.approx(grande / chica)
    region = []
    for total in (40, 120):
        partida, salas, cazador = bench_cazador.cripta_local(1, total, 200)
        estampa = Busqueda().calcular(partida.jugador.sala, 200)
        region.append([(s.id, s.busq_dist) for s in salas if s.busq_marca == estampa])
    assert region[0] == region[1] and len(region[0]) > 1


def test_us7_3_imprime_las_cuatro_comparaciones(capsys):
    """FR-019 · US7-3 · SC-009"""
    bench_cazador.ejecutar(pequeno=True)
    salida = capsys.readouterr().out
    for titulo in ("1. un cazador contra muchos", "2. rango chico contra rango grande",
                   "3. una búsqueda por cazador contra compartida",
                   "4. reusar contra recalcular"):
        assert titulo in salida
    partes = re.split(r"^(?=\d\. )", salida, flags=re.MULTILINE)
    for parte in partes:
        if parte.startswith(("3.", "4.")):
            assert "puertas cambian seguido" in parte
            assert "puertas casi nunca cambian" in parte


def test_us7_4_los_tres_modos_deciden_igual_y_el_benchmark_falla_si_no(monkeypatch):
    """FR-019, FR-011 · US7-4 · SC-009"""
    listas = [bench_cazador.ejecucion(m, 3, 30, 6, 400, 60, 1, registrar=True).decisiones
              for m in bench_cazador.MODOS]
    assert listas[0] and listas[0] == listas[1] == listas[2]
    assert bench_cazador.verificar_equivalencia(3, 30, 6, 400, 60, 1) == listas[0]

    class Falso:
        busqueda = None

        def decidir(self, partida, cazador, limite_forzado=None):
            return None  # nunca se mueve

    original = bench_cazador.DecisorCazador
    monkeypatch.setattr(bench_cazador, "DecisorCazador",
                        lambda modo: Falso() if modo == "falso" else original(modo))
    with pytest.raises(RuntimeError):
        bench_cazador.verificar_equivalencia(3, 30, 6, 400, 60, 1, modos=("individual", "falso"))


def _huella(partida, salas, cazadores):
    salidas = [(s.id, x.direccion, x.destino.id, x.costo, x.cerrada) for s in salas for x in s.salidas]
    return salidas, [(h.id_enemigo, h.sala.id, h.rango) for h in cazadores]


def test_us7_5_la_cripta_del_benchmark_sale_de_la_semilla():
    """FR-020 · US7-5 · SC-010"""
    a = _huella(*bench_cazador.armar_cripta(5, 40, 6))
    b = _huella(*bench_cazador.armar_cripta(5, 40, 6))
    c = _huella(*bench_cazador.armar_cripta(6, 40, 6))
    assert a == b
    assert a != c


def test_us7_6_los_benchmarks_no_importan_nada_de_la_vista():
    """FR-021 · US7-6 · SC-010"""
    codigo = ("import sys; sys.path.insert(0, sys.argv[1]); "
              "import bench.bench_ciclo, bench.bench_cazador; "
              "bench.bench_cazador.ejecutar(pequeno=True); "
              "print(any(name.startswith('view') for name in sys.modules))")
    resultado = subprocess.run([sys.executable, "-I", "-c", codigo, str(RAIZ)],
                               capture_output=True, text=True, cwd=RAIZ, timeout=300)
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip().splitlines()[-1] == "False"
    for archivo in (RAIZ / "bench").glob("*.py"):
        assert "Vista" not in archivo.read_text(encoding="utf-8"), archivo.name


def test_ejecutar_modos_corre_el_ciclo_una_vez_por_modo(monkeypatch, capsys):
    """FR-017, FR-019 · bench_ciclo --modos: un bloque por modo del decisor."""
    monkeypatch.setattr(bench_ciclo, "ESCENARIOS", (("cazadores", 10, 20, 3),))
    monkeypatch.setattr(bench_ciclo, "ACCIONES", 20)
    bench_ciclo.ejecutar_modos()
    salida = capsys.readouterr().out
    for modo in bench_cazador.MODOS:
        assert f"--- modo {modo} ---" in salida
    assert salida.count("cazadores") >= 3
