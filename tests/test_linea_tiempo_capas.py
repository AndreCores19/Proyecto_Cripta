"""Capas: `--replay ... --hasta` y `--bench` de punta a punta sin crear ninguna vista (spec 005, T074).

Las dos corridas entran por `main.main()` como desde la consola, con cada clase de view/ parcheada para
fallar al construirse y el cliente HTTP parcheado para fallar (todo va por el paquete sin conexión).
`--replay` usa una cripta real del paquete; `--bench` corre todos los benchmarks con tamaños chicos.
"""
import os
import random
import shutil
import sys

import pytest

import main
from adapters.bitacora_partida import BitacoraPartida
from adapters.cliente_offline import ClienteOffline
from adapters.formato_historia import lineas_historia
from aplicacion import Aplicacion, _crear_servicio
from controller.controlador import Controlador
from linea_tiempo_apoyo import VistaMuda, _elegir_comando

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRIPTA = "cripta-02"


def _prohibir_vistas_y_red(monkeypatch):
    import adapters.cliente_http
    import view.vista_consola
    import view.vista_silenciosa

    def prohibido(self, *args, **kwargs):
        raise AssertionError(f"se creó {type(self).__name__} en una corrida sin vista ni red")

    monkeypatch.setattr(adapters.cliente_http.ClienteHttp, "__init__", prohibido)
    for modulo in (view.vista_consola, view.vista_silenciosa):
        for nombre in dir(modulo):
            clase = getattr(modulo, nombre)
            if isinstance(clase, type) and clase.__module__ == modulo.__name__:
                monkeypatch.setattr(clase, "__init__", prohibido)


@pytest.fixture
def carpeta(tmp_path, monkeypatch):
    """Una carpeta de trabajo con una copia del paquete sin conexión: cache/ y saves/ quedan ahí."""
    shutil.copytree(os.path.join(RAIZ, "offline"), tmp_path / "offline")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _grabar(semilla_juego, n):
    """Juega `n` comandos con semilla en la cripta real (el camino de `Aplicacion._sesion`, con una vista muda
    de las pruebas) y graba el log en saves/. Devuelve (servicio vivo, ruta del log)."""
    app = Aplicacion(main.URL, CRIPTA, cliente=ClienteOffline("offline"))
    partida = app.fabrica.nueva_partida(semilla=12345)
    servicio = _crear_servicio(app, partida)
    servicio.actualizar_fichas()
    bitacora = BitacoraPartida("saves")
    datos = app.repo_cripta.datos
    bitacora.abrir(datos.id_cripta, datos.version, app.repo_catalogo.version(), partida.semilla)
    controlador = Controlador(servicio, VistaMuda(), bitacora, app)
    azar = random.Random(semilla_juego)
    try:
        for _ in range(n):
            if servicio.terminada():
                break
            controlador.ejecutar(_elegir_comando(azar, servicio, False))
    finally:
        bitacora.cerrar()
    return servicio, os.path.join("saves", f"partida_{CRIPTA}_{partida.semilla}.log")


def _main(monkeypatch, argumentos):
    monkeypatch.setattr(sys, "argv", ["main.py"] + argumentos)
    main.main()


def _bloque(salida):
    lineas = salida.splitlines()
    inicio = lineas.index("-" * 40)
    return lineas[inicio:lineas.index("-" * 40, inicio + 1) + 1]


def test_replay_hasta_de_punta_a_punta_sin_vistas_en_la_cripta_real(carpeta, monkeypatch, capsys):
    """FR-013, FR-014, FR-016 · US4-1, US4-3 · `main.py --offline --replay LOG --hasta T` con la cripta real
    del paquete: imprime lo mismo que `historia T` en el juego grabado, sin crear ninguna clase de view/ ni el
    cliente HTTP, y sin solicitudes"""
    servicio, log = _grabar(semilla_juego=3, n=60)
    reloj = servicio.partida.reloj
    assert reloj > 0 and len(servicio.linea_tiempo) > 10
    esperado = {t: lineas_historia(servicio.historia_por_instante(t).resumen) for t in (0, reloj // 2, reloj)}
    capsys.readouterr()
    _prohibir_vistas_y_red(monkeypatch)
    for t, lineas in esperado.items():
        _main(monkeypatch, ["--offline", "--replay", log, "--hasta", str(t)])
        salida = capsys.readouterr().out
        assert _bloque(salida) == lineas, t
        assert "Solicitudes realizadas: 0 " in salida
    _main(monkeypatch, ["--offline", "--replay", log, "--hasta", str(reloj + 10 ** 6)])
    salida = capsys.readouterr().out
    assert _bloque(salida) == esperado[reloj]                 #el estado final, y el aviso de que terminó antes
    assert f"(instante {reloj})" in salida


#tamaños chicos para cada benchmark de `--bench`: (módulo, atributo, valor)
CHICOS = (
    ("bench_ciclo", "ACCIONES", 20),
    ("bench_ciclo", "ESCENARIOS", (("normal", 20, 30, 0), ("cazadores", 30, 20, 3))),
    ("bench_historial", "REPETICIONES", 10),
    ("bench_agenda", "TAMANOS", (100,)),
    ("bench_agenda", "OPERACIONES", 100),
    ("bench_inventario", "TAMANOS", (10, 100)),
    ("bench_inventario", "OPERACIONES", 200),
    ("bench_ordenamientos", "TAMANOS", (4, 8)),
    ("bench_ordenamientos", "TAMANOS_GRANDES", (16,)),
    ("bench_ordenamientos", "TANDAS", 1),
    ("bench_rastro", "REPETICIONES", 100),
    ("bench_cache", "TAMANOS", (25,)),
    ("bench_cache", "BUSQUEDAS", 100),
    ("bench_cache", "TANDAS", 1),
    ("bench_cache", "CAPACIDADES", (10,)),
    ("bench_cache", "ACCESOS", 100),
    ("bench_guardado", "TAMANOS", (50,)),
    ("bench_guardado", "COMANDOS", 20),
    ("bench_guardado", "TANDAS", 1),
    ("bench_fichas", "CANTIDADES", (10,)),
    ("bench_fichas", "ACTIVAS", (5,)),
    ("bench_fichas", "CAPACIDAD_GRANDE", 50),
    ("bench_fichas", "REPETICIONES", 2),
    ("bench_replay", "CANTIDADES", (100,)),
    ("bench_precarga", "ESCENARIOS", ((10, 20),)),
    ("bench_precarga", "SEMILLAS", 1),
    ("bench_catalogo", "ESCENARIOS", ((10, 20, 5),)),
    ("bench_catalogo", "SEMILLAS", 1),
)
CON_PEQUENO = ("bench_cazador", "bench_ir_a", "bench_solvabilidad")


def _achicar_funciones(monkeypatch):
    """Los benchmarks que fijan sus tamaños dentro de `ejecutar`: se envuelven sus funciones auxiliares para
    que corran el mismo código con menos trabajo."""
    from bench import bench_agenda, bench_bitacora, bench_rastro
    contar, contar_cazadores = bench_agenda.contar_operaciones, bench_agenda.contar_operaciones_cazadores
    monkeypatch.setattr(bench_agenda, "contar_operaciones",
                        lambda acciones=1000, num_enemigos=300, variable=False:
                        contar(5, min(num_enemigos, 50), variable))
    monkeypatch.setattr(bench_agenda, "contar_operaciones_cazadores",
                        lambda acciones, num_enemigos, num_cazadores:
                        contar_cazadores(5, min(num_enemigos, 50), min(num_cazadores, 5)))
    memoria, agregar = bench_bitacora.memoria_kb, bench_bitacora.tiempo_agregar_us
    monkeypatch.setattr(bench_bitacora, "memoria_kb", lambda fabrica, cantidad: memoria(fabrica, min(cantidad, 500)))
    monkeypatch.setattr(bench_bitacora, "tiempo_agregar_us",
                        lambda fabrica, repeticiones=200000: agregar(fabrica, 500))
    decision, ciclo = bench_rastro.medir_decision, bench_rastro.medir_por_ciclo
    monkeypatch.setattr(bench_rastro, "medir_decision",
                        lambda salidas, total_salas: decision(salidas, min(total_salas, 100)))
    monkeypatch.setattr(bench_rastro, "medir_por_ciclo", lambda r: ciclo(min(r, 20)))
    for nombre in ("medir_perezoso", "medir_con_evento", "medir_barrido"):
        original = getattr(bench_rastro, nombre)
        monkeypatch.setattr(bench_rastro, nombre, lambda n, original=original: original(min(n, 100)))


def test_bench_de_punta_a_punta_sin_vistas_ni_red(carpeta, monkeypatch, capsys):
    """FR-016, FR-024, FR-026 · `main.py --bench` corre todos los benchmarks (tamaños chicos), incluida la línea de
    tiempo y el historial bajo la nueva carga, sin crear ninguna clase de view/ ni el cliente HTTP"""
    import importlib
    for nombre, atributo, valor in CHICOS:
        modulo = importlib.import_module(f"bench.{nombre}")
        assert hasattr(modulo, atributo), (nombre, atributo)
        monkeypatch.setattr(modulo, atributo, valor)
    _achicar_funciones(monkeypatch)
    for nombre in CON_PEQUENO:
        modulo = importlib.import_module(f"bench.{nombre}")
        original = modulo.ejecutar
        monkeypatch.setattr(modulo, "ejecutar", lambda original=original: original(pequeno=True))
    from bench import bench_linea_tiempo
    original_linea = bench_linea_tiempo.ejecutar
    monkeypatch.setattr(bench_linea_tiempo, "ejecutar",
                        lambda: original_linea(acciones=30, consultas=4, consultas_sin_puntos=2,
                                               mundos=("referencia",)))
    _prohibir_vistas_y_red(monkeypatch)
    _main(monkeypatch, ["--bench"])
    salida = capsys.readouterr().out
    assert "== Timeline: memory and query time (world=referencia" in salida
    assert "Default K:" in salida
    assert "capture checkpoint (us)" in salida                 #bench_historial bajo la nueva carga
