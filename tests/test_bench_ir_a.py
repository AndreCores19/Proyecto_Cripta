"""El benchmark de «ir a»: reproducibilidad, forma del informe, rutas correctas y aislamiento de la vista (US9)."""
import re
import subprocess
import sys
from pathlib import Path

from bench import bench_ir_a
from tests.mapas_niebla import ruta_referencia

RAIZ = Path(__file__).resolve().parent.parent


def _huella(salas):
    return [(s.id, x.direccion, x.destino.id, x.costo) for s in salas for x in s.salidas]


def test_us9_2_la_misma_semilla_arma_la_misma_cripta():
    """FR-027 · US9-2"""
    _, a = bench_ir_a.armar_cripta(5, 40)
    _, b = bench_ir_a.armar_cripta(5, 40)
    _, c = bench_ir_a.armar_cripta(6, 40)
    assert _huella(a) == _huella(b)
    assert _huella(a) != _huella(c)


def test_us9_1_el_informe_trae_promedio_p99_maximo_y_veredicto(capsys):
    """FR-026, FR-027 · US9-1"""
    bench_ir_a.ejecutar(pequeno=True)
    lineas = capsys.readouterr().out.splitlines()
    filas = [l for l in lineas if "ruta" in l and "paso completo" in l]
    assert len(filas) == len(bench_ir_a.PEQUENO.tamanos)
    for fila in filas:
        assert len(re.findall(r"\d+\.\d", fila)) == 6          # promedio, p99 y máximo, de la ruta y del paso
    veredicto = next(l for l in lineas if l.startswith("Veredicto con"))
    assert "p99 de la ruta" in veredicto and "máximo" in veredicto
    assert veredicto.rstrip().endswith("cumple") and not veredicto.rstrip().endswith("NO cumple")


def test_us9_1_el_veredicto_usa_menor_o_igual_que_5_ms(monkeypatch, capsys):
    """FR-026 · SC-007: un p99 de exactamente 5.0 ms cumple y uno de 5.001 ms no"""
    for p99_us, esperado in ((5000.0, "cumple"), (5001.0, "NO cumple")):
        class Falsa:
            us_ruta = [p99_us] * 100

        monkeypatch.setattr(bench_ir_a, "medir", lambda salas, repeticiones, semilla=1: Falsa())
        monkeypatch.setattr(bench_ir_a, "medir_paso_completo", lambda salas, repeticiones, semilla=1: [1.0] * 100)
        bench_ir_a.ejecutar(pequeno=True)
        veredicto = next(l for l in capsys.readouterr().out.splitlines() if l.startswith("Veredicto con"))
        assert veredicto.rstrip().endswith(esperado)
        if esperado == "cumple":
            assert not veredicto.rstrip().endswith("NO cumple")


def test_us9_las_rutas_medidas_coinciden_con_el_oraculo():
    """FR-026, FR-018 · cada ruta medida en la configuración pequeña es la del oráculo"""
    for salas, repeticiones in bench_ir_a.PEQUENO.tamanos:
        medicion = bench_ir_a.medir(salas, repeticiones)
        assert len(medicion.rutas) == len(medicion.pares) == len(medicion.us_ruta) == repeticiones
        for (aqui, destino), (salida, d) in zip(medicion.pares, medicion.rutas):
            medicion.partida.jugador.sala = aqui
            esperado_d, esperada = ruta_referencia(medicion.salas, medicion.partida, destino)
            if esperado_d == 0:
                assert (salida, d) == (None, 0)
            else:
                assert (salida, d) == (esperada, esperado_d)


def test_us9_el_benchmark_no_importa_la_vista():
    """FR-027 · el módulo no nombra view/ y ejecutarlo no deja ningún módulo de view cargado"""
    fuente = (RAIZ / "bench" / "bench_ir_a.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(from|import)\s+view\b", fuente, flags=re.MULTILINE)
    codigo = ("import sys; sys.path.insert(0, sys.argv[1]); "
              "import bench.bench_ir_a; bench.bench_ir_a.ejecutar(pequeno=True); "
              "print(any(name.startswith('view') for name in sys.modules))")
    resultado = subprocess.run([sys.executable, "-I", "-c", codigo, str(RAIZ)],
                               capture_output=True, text=True, cwd=RAIZ, timeout=300)
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip().splitlines()[-1] == "False"
