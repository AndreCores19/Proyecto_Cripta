"""`--replay LOG --hasta T` (spec 005, Fase 7, US4).

Se graba una partida con semilla con `BitacoraPartida` (el camino real del juego), y se reproduce con
`Aplicacion.reproducir` sobre un mundo nuevo igual al grabado: la misma cripta falsa, la misma semilla y
los mismos comandos, sin red (el cliente falso falla ante cualquier llamada y el catálogo es falso).
"""
import sys

import pytest

from adapters.bitacora_partida import BitacoraPartida
from adapters.formato_historia import lineas_historia
from adapters.lector_bitacora import LectorBitacora
from aplicacion import Aplicacion
from controller.controlador import Controlador
from linea_tiempo_apoyo import VistaMuda, armar_mundo, jugar_semilla
from model.linea_tiempo_logica import LineaTiempoPartida
from service.juego_service import JuegoService

ID_CRIPTA = "prueba"
VERSION = "v1"
SEMILLA_MUNDO = 3


def _mundo(con_pergaminos=False, **cambios):
    parametros = dict(salas=7, enemigos=5, cazadores=2, con_pergaminos=con_pergaminos, vida_jugador=5000)
    parametros.update(cambios)
    return armar_mundo(SEMILLA_MUNDO, **parametros)


def _comandos(n=60, semilla=5, con_pergaminos=False):
    m = _mundo(con_pergaminos)
    return jugar_semilla(JuegoService(m.partida, m.fabrica), semilla, n, con_pergaminos=con_pergaminos)


class Grabada:
    """El juego vivo grabado: su servicio (con línea de tiempo), el log y el reloj tras cada comando."""

    def __init__(self, carpeta, comandos, con_pergaminos=False, k=3, **mundo):
        m = _mundo(con_pergaminos, **mundo)
        linea = LineaTiempoPartida()
        linea.iniciar(m.partida, m.constructor, k)
        self.servicio = JuegoService(m.partida, m.fabrica, linea_tiempo=linea)
        bitacora = BitacoraPartida(carpeta)
        bitacora.abrir(ID_CRIPTA, VERSION, VERSION, m.partida.semilla)
        controlador = Controlador(self.servicio, VistaMuda(), bitacora, None)
        self.relojes = []                           #el reloj tras cada comando ejecutado
        for comando in comandos:
            if self.servicio.terminada():
                break
            controlador.ejecutar(comando)
            self.relojes.append(m.partida.reloj)
        bitacora.cerrar()
        self.ruta = carpeta / f"partida_{ID_CRIPTA}_{m.partida.semilla}.log"
        self.partida = m.partida

    def lineas(self, t):
        respuesta = self.servicio.historia_por_instante(t)
        assert respuesta.aceptada, respuesta.motivo
        return lineas_historia(respuesta.resumen)


class _CatalogoInfo:
    aciertos_memoria = 0
    aciertos_disco = 0
    fallos = 0

    def version(self):
        return VERSION


class _ClienteInfo:
    solicitudes = 0
    presupuesto = None


class AppDeMundo:
    """Lo que `Aplicacion.reproducir` lee, sobre un mundo de prueba nuevo (sin red)."""

    _versiones_coinciden = Aplicacion._versiones_coinciden
    reproducir = Aplicacion.reproducir

    def __init__(self, con_pergaminos=False, k=None, **mundo):
        m = _mundo(con_pergaminos, **mundo)
        self.mundo = m
        m.fabrica.nueva_partida = lambda semilla: self._partida(semilla)
        m.datos.id_cripta = ID_CRIPTA
        m.datos.version = VERSION
        self.fabrica = m.fabrica
        self.dtos = m.dtos
        self.repo_cripta = m.repo
        self.repo_catalogo = _CatalogoInfo()
        self.cliente = _ClienteInfo()
        self.checkpoint_cada = k

    def _partida(self, semilla):
        #la partida del mundo ya está armada con la semilla del mundo, que es la del log
        assert semilla == self.mundo.partida.semilla
        return self.mundo.partida


def _leer(ruta):
    lector = LectorBitacora(ruta)
    lector.leer()
    return lector


def _bloque_historia(salida):
    """Las líneas del resumen impreso: desde la primera raya hasta la siguiente."""
    lineas = salida.splitlines()
    inicio = lineas.index("-" * 40)
    fin = lineas.index("-" * 40, inicio + 1)
    return lineas[inicio:fin + 1], lineas[fin + 1:]


def _prohibir_vistas(monkeypatch):
    import view.vista_consola
    import view.vista_silenciosa

    def prohibido(self, *args, **kwargs):
        raise AssertionError("vista instanciada en --replay --hasta")

    for modulo in (view.vista_consola, view.vista_silenciosa):
        for nombre in dir(modulo):
            clase = getattr(modulo, nombre)
            if isinstance(clase, type) and clase.__module__ == modulo.__name__:
                monkeypatch.setattr(clase, "__init__", prohibido)


# ---------------------------------------------------------------- US4-1, US4-3 (FR-013, FR-014, FR-016)

def test_hasta_dentro_del_juego_imprime_lo_mismo_que_historia_en_el_juego(tmp_path, monkeypatch, capsys):
    """FR-013, FR-014, FR-016 · US4-1, US4-3 · las líneas de `--hasta t` son las de `historia t` en la partida
    viva con la misma cripta, semilla y comandos; ninguna clase de view/ se crea"""
    grabada = Grabada(tmp_path, _comandos(60))
    _prohibir_vistas(monkeypatch)
    for t in (0, 1, grabada.partida.reloj // 3, grabada.partida.reloj // 2, grabada.partida.reloj):
        app = AppDeMundo()
        app.reproducir(_leer(grabada.ruta), hasta=t)
        bloque, resto = _bloque_historia(capsys.readouterr().out)
        assert bloque == grabada.lineas(t), t
        assert not any("terminó antes" in linea for linea in resto)
        assert app.mundo.cliente.llamadas == 0


def test_hasta_despues_del_final_imprime_el_estado_final_y_avisa_que_termino_antes(tmp_path, capsys):
    """FR-015 · US4-2 · t mayor que el reloj final: el estado final y el aviso con el reloj final"""
    grabada = Grabada(tmp_path, _comandos(40))
    final = grabada.partida.reloj
    for t in (final + 1, final + 99999999):
        AppDeMundo().reproducir(_leer(grabada.ruta), hasta=t)
        bloque, resto = _bloque_historia(capsys.readouterr().out)
        assert bloque == grabada.lineas(final)
        assert resto[0] == f"La partida terminó antes (instante {final})."


def test_hasta_tras_una_muerte_avisa_con_el_reloj_de_la_muerte(tmp_path, capsys):
    """FR-015 · US4-2 · una partida que terminó con la muerte del jugador"""
    mundo = dict(enemigos=0, cazadores=0, vida_jugador=4)
    grabada = Grabada(tmp_path, ["w"] + ["esperar"] * 300, **mundo)
    assert grabada.partida.terminada and not grabada.partida.victoria
    final = grabada.partida.reloj
    AppDeMundo(**mundo).reproducir(_leer(grabada.ruta), hasta=final + 5)
    bloque, resto = _bloque_historia(capsys.readouterr().out)
    assert bloque == grabada.lineas(final)
    assert resto[0] == f"La partida terminó antes (instante {final})."


def test_hasta_igual_al_reloj_final_no_avisa(tmp_path, capsys):
    """FR-015 · un t dentro del juego (igual al último instante) nunca se informa como terminado antes"""
    grabada = Grabada(tmp_path, _comandos(30))
    AppDeMundo().reproducir(_leer(grabada.ruta), hasta=grabada.partida.reloj)
    bloque, resto = _bloque_historia(capsys.readouterr().out)
    assert bloque == grabada.lineas(grabada.partida.reloj)
    assert not any("terminó antes" in linea for linea in resto)


# ---------------------------------------------------------------- US4-5 (FR-010, FR-014)

def test_hasta_con_lecturas_de_pergamino_da_el_juego_como_quedo(tmp_path, capsys):
    """FR-010, FR-014 · US4-5 · un log con lecturas de pergamino: el resumen es el del juego como quedó"""
    comandos = _comandos(120, semilla=8, con_pergaminos=True)
    grabada = Grabada(tmp_path, comandos, con_pergaminos=True)
    assert grabada.partida.retrocesos >= 1, "el log debe tener al menos una lectura"
    final = grabada.partida.reloj
    for t in sorted({0, final // 4, final // 2, (3 * final) // 4, final}):
        AppDeMundo(con_pergaminos=True).reproducir(_leer(grabada.ruta), hasta=t)
        bloque, _ = _bloque_historia(capsys.readouterr().out)
        assert bloque == grabada.lineas(t), t


# ---------------------------------------------------------------- T049: se detiene en cuanto el reloj llega (FR-013, FR-006)

def test_el_replay_se_detiene_en_cuanto_el_reloj_llega_a_t_y_la_consulta_no_pide_nada(tmp_path, monkeypatch, capsys):
    """FR-013, FR-006 · se ejecutan solo los comandos hasta que el reloj es >= t; las resoluciones del catálogo
    y las llamadas al cliente son las de un --replay simple del mismo prefijo (la consulta no agrega ninguna)"""
    comandos = _comandos(80)
    grabada = Grabada(tmp_path, comandos)
    t = grabada.relojes[len(grabada.relojes) // 4] - 1
    esperados = next(i + 1 for i, r in enumerate(grabada.relojes) if r >= t)
    assert esperados < len(grabada.relojes)

    ejecutados = []
    original = Controlador.ejecutar

    def contar(self, texto):
        ejecutados.append(texto)
        return original(self, texto)
    monkeypatch.setattr(Controlador, "ejecutar", contar)

    con_hasta = AppDeMundo()
    con_hasta.reproducir(_leer(grabada.ruta), hasta=t)
    capsys.readouterr()
    assert len(ejecutados) == esperados < len(_leer(grabada.ruta).comandos)
    prefijo = list(ejecutados)

    class _LectorPrefijo:
        cripta, version_cripta, version_catalogo = ID_CRIPTA, VERSION, VERSION
        semilla = grabada.partida.semilla
        comandos = prefijo

    simple = AppDeMundo()
    simple.reproducir(_LectorPrefijo())
    capsys.readouterr()
    assert simple.mundo.catalogo.resoluciones == con_hasta.mundo.catalogo.resoluciones
    assert con_hasta.mundo.cliente.llamadas == simple.mundo.cliente.llamadas == 0


def test_sin_hasta_el_replay_es_el_de_siempre(tmp_path, capsys):
    """FR-013 · sin `--hasta` el replay imprime el final y el reporte, sin resumen de historia"""
    grabada = Grabada(tmp_path, _comandos(30))
    AppDeMundo().reproducir(_leer(grabada.ruta))
    salida = capsys.readouterr().out
    assert "Historia en el instante" not in salida
    assert f"Tiempo final: {grabada.partida.reloj}" in salida


# ---------------------------------------------------------------- US4-4: la línea de comandos (FR-013)

def _correr_main(monkeypatch, argumentos):
    import main
    creadas = []

    class AplicacionEspia:
        def __init__(self, *args):
            creadas.append(args)

        def reproducir(self, lector, hasta=None):
            creadas.append(("reproducir", hasta))

        def jugar(self, ruta_carga=None, forzar=False):
            creadas.append(("jugar",))

    monkeypatch.setattr(main, "Aplicacion", AplicacionEspia)
    monkeypatch.setattr(sys, "argv", ["main.py"] + argumentos)
    main.main()
    return creadas


@pytest.mark.parametrize("valor", ["-1", "abc", "1.5", "", "+3", "1e3"])
def test_hasta_mal_formado_o_negativo_es_un_error_con_estado_1_y_no_imprime_estado(valor, tmp_path, monkeypatch,
                                                                                    capsys):
    """FR-013 · US4-4 · `--hasta` mal formado o negativo: mensaje, salida 1 y ningún estado"""
    grabada = Grabada(tmp_path, _comandos(10))
    with pytest.raises(SystemExit) as salida:
        _correr_main(monkeypatch, ["--offline", "--replay", str(grabada.ruta), f"--hasta={valor}"])
    assert salida.value.code == 1
    texto = capsys.readouterr().out
    assert "--hasta" in texto
    assert "Historia en el instante" not in texto and "Sala " not in texto


def test_hasta_sin_replay_es_un_error_de_argparse(monkeypatch, capsys):
    """FR-013 · US4-4 · `--hasta` sin `--replay`"""
    with pytest.raises(SystemExit) as salida:
        _correr_main(monkeypatch, ["cripta-x", "--offline", "--hasta", "5"])
    assert salida.value.code == 2
    assert "--hasta" in capsys.readouterr().err


def test_un_log_mal_escrito_informa_el_error_y_no_imprime_estado(tmp_path, monkeypatch, capsys):
    """FR-013 · US4-4 · un log que el juego no escribió bien: el error de siempre, salida 1, sin estado"""
    malo = tmp_path / "malo.log"
    malo.write_text("esto no es una bitácora\n", encoding="utf-8")
    with pytest.raises(SystemExit) as salida:
        _correr_main(monkeypatch, ["--offline", "--replay", str(malo), "--hasta", "5"])
    assert salida.value.code == 1
    texto = capsys.readouterr().out
    assert "No se pudo leer la bitácora" in texto and "Historia en el instante" not in texto


def test_main_pasa_hasta_a_reproducir(tmp_path, monkeypatch):
    """FR-013 · `--replay LOG --hasta T` llega a `Aplicacion.reproducir` como entero"""
    grabada = Grabada(tmp_path, _comandos(10))
    creadas = _correr_main(monkeypatch, ["--offline", "--replay", str(grabada.ruta), "--hasta", "300"])
    assert creadas[-1] == ("reproducir", 300)
    creadas = _correr_main(monkeypatch, ["--offline", "--replay", str(grabada.ruta)])
    assert creadas[-1] == ("reproducir", None)
