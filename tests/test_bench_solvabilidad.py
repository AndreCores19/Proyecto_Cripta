"""El benchmark de la verificación: reproducibilidad, forma del informe, alternativa ingenua con el mismo orden
y aislamiento de la vista (US8)."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

from bench import bench_solvabilidad
from model.solvabilidad_logica import Verificador

RAIZ = Path(__file__).resolve().parent.parent


def _huella(cripta):
    salidas = [(s.id, x.direccion, x.destino.id, x.llave, x.cerrada) for s in cripta.salas.valores for x in s.salidas]
    return salidas, list(cripta.llaves), cripta.sala_inicial, cripta.sala_salida, cripta.llave_salida


def test_us8_3_la_misma_semilla_arma_la_misma_cripta():
    """FR-020 · US8-3"""
    for armar in (lambda s: bench_solvabilidad.armar_publicada(s),
                  lambda s: bench_solvabilidad.armar_publicada(s, resoluble=False),
                  lambda s: bench_solvabilidad.armar_cadena(s, 200, 4)):
        assert _huella(armar(5)) == _huella(armar(5))
        assert _huella(armar(5)) != _huella(armar(6))


def test_us8_1_la_cripta_con_la_forma_de_la_mayor_publicada_tiene_300_salas_y_4_llaves():
    """FR-018 · US8-1: 300 salas, 4 llaves; la resoluble se puede ganar y la otra no"""
    resoluble = bench_solvabilidad.armar_publicada(1)
    assert len(resoluble.salas.valores) == 300 and len(resoluble.llaves) == 4
    assert bench_solvabilidad.verificar(resoluble).resoluble is True
    imposible = bench_solvabilidad.armar_publicada(1, resoluble=False)
    resultado = bench_solvabilidad.verificar(imposible)
    assert resultado.resoluble is False and len(resultado.ciclos) >= 1


def test_us8_1_el_informe_trae_promedio_p99_maximo_y_el_veredicto_contra_200_ms(capsys):
    """FR-018, FR-019 · US8-1, US8-2"""
    bench_solvabilidad.ejecutar(pequeno=True)
    lineas = capsys.readouterr().out.splitlines()
    filas = [l for l in lineas if l.lstrip().startswith(("resoluble", "no resoluble"))]
    assert len(filas) == 2
    for fila in filas:
        assert len(re.findall(r"\d+\.\d{3}", fila)) == 3          # promedio, p99 y máximo, en ms
    veredicto = next(l for l in lineas if l.startswith("Veredicto con 300 salas"))
    assert "máximo" in veredicto and "200 ms" in veredicto
    assert veredicto.rstrip().endswith("cumple") and not veredicto.rstrip().endswith("NO cumple")
    assert any(l.startswith("Crecimiento") for l in lineas)


@pytest.mark.parametrize("maximo_us,esperado", [(200000.0, "cumple"), (200001.0, "NO cumple")])
def test_us8_1_el_veredicto_usa_el_maximo_y_menor_o_igual_que_200_ms(monkeypatch, capsys, maximo_us, esperado):
    """FR-018 · un máximo de exactamente 200.0 ms cumple y uno de 200.001 ms no"""
    monkeypatch.setattr(bench_solvabilidad, "medir_verificacion", lambda cripta, repeticiones: [1.0, maximo_us])
    bench_solvabilidad.ejecutar(pequeno=True)
    veredicto = next(l for l in capsys.readouterr().out.splitlines() if l.startswith("Veredicto con 300 salas"))
    assert veredicto.rstrip().endswith(esperado)
    if esperado == "cumple":
        assert not veredicto.rstrip().endswith("NO cumple")


def test_us8_2_la_alternativa_ingenua_da_el_mismo_orden_que_la_verificacion():
    """FR-019, FR-021 · US8-2: una pasada completa por llave, el mismo orden"""
    criptas = [bench_solvabilidad.armar_publicada(s) for s in range(1, 6)]
    criptas += [bench_solvabilidad.armar_cadena(s, n, k) for s, n, k in ((1, 60, 2), (2, 300, 6), (3, 1000, 20))]
    for cripta in criptas:
        rapido = bench_solvabilidad.verificar(cripta)
        assert bench_solvabilidad.verificar_ingenuo(cripta) == rapido.orden


def test_us8_2_si_la_ingenua_decide_distinto_el_benchmark_falla(monkeypatch):
    """FR-019, FR-021 · el benchmark comprueba que ambos dan el mismo orden"""
    monkeypatch.setattr(bench_solvabilidad, "verificar_ingenuo", lambda cripta: ["otro"])
    with pytest.raises(RuntimeError):
        bench_solvabilidad.ejecutar(pequeno=True)


def test_us8_2_en_cadenas_de_llaves_cada_sala_y_salida_se_visitan_una_vez_sin_importar_las_llaves():
    """FR-019 · US8-2: el trabajo crece con las salas y las salidas, no con salas por llave"""
    for n, k in ((100, 2), (1000, 20), (4000, 80)):
        cripta = bench_solvabilidad.armar_cadena(1, n, k)
        resultado = bench_solvabilidad.verificar(cripta)
        salas = len(cripta.salas.valores)
        assert resultado.resoluble is True
        assert resultado.visitas_salas == salas
        assert resultado.examenes_salidas == sum(len(s.salidas) for s in cripta.salas.valores)


def test_us8_el_benchmark_no_importa_la_vista():
    """FR-020, FR-021 · el módulo no nombra view/ y ejecutarlo no deja ningún módulo de view cargado"""
    fuente = (RAIZ / "bench" / "bench_solvabilidad.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(from|import)\s+view\b", fuente, flags=re.MULTILINE)
    codigo = ("import sys; sys.path.insert(0, sys.argv[1]); "
              "import bench.bench_solvabilidad; bench.bench_solvabilidad.ejecutar(pequeno=True); "
              "print(any(name.startswith('view') for name in sys.modules))")
    resultado = subprocess.run([sys.executable, "-I", "-c", codigo, str(RAIZ)],
                               capture_output=True, text=True, cwd=RAIZ, timeout=300)
    assert resultado.returncode == 0, resultado.stderr
    assert resultado.stdout.strip().splitlines()[-1] == "False"


def test_el_benchmark_usa_el_verificador_del_modelo():
    """FR-018 · se mide Verificador.verificar, no una copia"""
    assert bench_solvabilidad.Verificador is Verificador
