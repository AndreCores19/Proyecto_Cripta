"""`--checkpoint-cada K` (spec 005, Fase 9, US6-6, US6-7, US6-8).

La opción se valida antes de que nada corra (ni cliente, ni aplicación); sin ella el juego usa
`K_POR_DEFECTO`; al cargar una partida gana el K con que se guardó y, si la opción se escribió con otro
valor, se avisa. Todo sin red.
"""
import sys

import pytest

import aplicacion
from aplicacion import Aplicacion, _crear_servicio, k_para_carga
from model.linea_tiempo_logica import K_POR_DEFECTO
from tests.estado_fijo import AppFalsa, LectorFalso
from tests.test_ir_a_guardado import JUGADA, AppDePrueba, VistaGuionada


def _prohibir_clientes(monkeypatch):
    import adapters.cliente_http
    import adapters.cliente_offline

    def prohibido(self, *args, **kwargs):
        raise AssertionError("se creó un cliente: la opción mal escrita debía cortar antes")
    monkeypatch.setattr(adapters.cliente_http.ClienteHttp, "__init__", prohibido)
    monkeypatch.setattr(adapters.cliente_offline.ClienteOffline, "__init__", prohibido)


def _correr_main(monkeypatch, argumentos):
    """Corre main() con una Aplicacion espía; devuelve lo que recibió (argumentos y llamadas)."""
    import main
    llamadas = []

    class AplicacionEspia:
        def __init__(self, *args):
            llamadas.append(("crear",) + args)

        def jugar(self, ruta_carga=None, forzar=False):
            llamadas.append(("jugar",))

        def reproducir(self, lector, hasta=None):
            llamadas.append(("reproducir", hasta))

    def verificar_falso(url, id_cripta, cliente):
        llamadas.append(("verificar", id_cripta))
        return 0

    monkeypatch.setattr(main, "Aplicacion", AplicacionEspia)
    monkeypatch.setattr(main, "verificar_cripta", verificar_falso)
    monkeypatch.setattr(sys, "argv", ["main.py"] + argumentos)
    try:
        main.main()
    except SystemExit as salida:
        llamadas.append(("salida", salida.code))
    return llamadas


# ---------------------------------------------------------------- US6-6: valores inválidos (FR-019)

@pytest.mark.parametrize("valor", [None, "0", "-5", "abc", "2.5", ""])
def test_un_k_invalido_sale_con_2_sin_correr_nada_ni_pedir_nada(valor, monkeypatch, capsys):
    """FR-019 · US6-6 · sin valor, 0, negativo, no numérico o decimal: error de argparse, salida 2, nada corre"""
    _prohibir_clientes(monkeypatch)
    opcion = ["--checkpoint-cada"] if valor is None else [f"--checkpoint-cada={valor}"]
    llamadas = _correr_main(monkeypatch, ["cripta-x", "--offline"] + opcion)
    assert llamadas == [("salida", 2)]
    assert "--checkpoint-cada" in capsys.readouterr().err


# ---------------------------------------------------------------- US6-7: el valor por defecto (FR-019, FR-026)

def test_sin_la_opcion_la_aplicacion_recibe_none_y_la_linea_de_tiempo_usa_el_k_por_defecto(monkeypatch):
    """FR-019, FR-026 · US6-7 · sin la opción el juego arranca con `K_POR_DEFECTO`"""
    llamadas = _correr_main(monkeypatch, ["cripta-x", "--offline"])
    crear = llamadas[0]
    assert crear[0] == "crear" and crear[5] is None and llamadas[1] == ("jugar",)
    app = AppFalsa("v1", "v1")
    app.checkpoint_cada = None
    servicio = _crear_servicio(app, app.fabrica.nueva_partida(1))
    assert servicio.linea_tiempo.k == K_POR_DEFECTO


def test_con_la_opcion_la_aplicacion_recibe_el_k_y_la_linea_de_tiempo_lo_usa(monkeypatch):
    """FR-019 · `--checkpoint-cada 7` llega a la aplicación y a la línea de tiempo"""
    llamadas = _correr_main(monkeypatch, ["cripta-x", "--offline", "--checkpoint-cada", "7"])
    assert llamadas[0][5] == 7
    app = AppFalsa("v1", "v1")
    app.checkpoint_cada = 7
    assert _crear_servicio(app, app.fabrica.nueva_partida(1)).linea_tiempo.k == 7


def test_la_opcion_se_acepta_con_replay_y_se_ignora_con_verificar(tmp_path, monkeypatch, capsys):
    """FR-019 · con `--replay` el K llega a la aplicación; `--verificar` la ignora y verifica igual"""
    log = tmp_path / "partida.log"
    log.write_text("CRIPTA-LOG 1\ncripta: c\nversion_cripta: v\nversion_catalogo: v\nsemilla: 1\n---\nw\n",
                   encoding="utf-8")
    llamadas = _correr_main(monkeypatch, ["--offline", "--replay", str(log), "--checkpoint-cada", "5"])
    assert llamadas[0][5] == 5 and llamadas[1] == ("reproducir", None)
    llamadas = _correr_main(monkeypatch, ["--offline", "--verificar", "cripta-x", "--checkpoint-cada", "5"])
    assert llamadas == [("verificar", "cripta-x"), ("salida", 0)]


def test_replay_usa_el_k_de_la_opcion(monkeypatch, capsys):
    """FR-019 · `Aplicacion.reproducir` arma la línea de tiempo con el K de la aplicación"""
    usados = []
    original = aplicacion._crear_servicio

    def espia(app, partida, k=None):
        servicio = original(app, partida, k)
        usados.append(servicio.linea_tiempo.k)
        return servicio
    monkeypatch.setattr(aplicacion, "_crear_servicio", espia)
    app = AppFalsa("v1", "v1")
    app.checkpoint_cada = 11
    Aplicacion.reproducir(app, LectorFalso(1, ["w"], "v1", "v1"))
    assert usados == [11]


# ---------------------------------------------------------------- US6-8: el K guardado gana (FR-017, FR-019)

def test_k_para_carga_gana_el_guardado_y_avisa_solo_si_la_opcion_se_escribio_y_difiere():
    """FR-017, FR-019 · US6-8 · la regla: el K guardado gana; aviso solo si la opción se escribió y difiere"""
    assert k_para_carga(7, None) == (7, None)
    assert k_para_carga(7, 7) == (7, None)
    k, aviso = k_para_carga(7, 20)
    assert k == 7 and "--checkpoint-cada" in aviso and "K=7" in aviso
    assert k_para_carga(None, 20) == (20, None)        #un archivo sin K: el de la opción
    assert k_para_carga(None, None) == (None, None)    #ni archivo ni opción: el por defecto


class _VistaQueAnota(VistaGuionada):
    def __init__(self, comandos):
        super().__init__(comandos)
        self.mensajes = []

    def mostrar_mensaje(self, texto):
        self.mensajes.append(texto)


def _cargar_con_k_guardado(tmp_path, monkeypatch, k_guardado, k_opcion):
    """Guarda una partida, carga con un K guardado `k_guardado` en la cabecera y la opción `k_opcion`."""
    monkeypatch.chdir(tmp_path)
    usados = []
    original = aplicacion._crear_servicio

    def espia(app, partida, k=None):
        servicio = original(app, partida, k)
        usados.append(servicio.linea_tiempo.k)
        return servicio
    monkeypatch.setattr(aplicacion, "_crear_servicio", espia)
    app = AppDePrueba()
    app.checkpoint_cada = k_opcion
    assert app._sesion(VistaGuionada(JUGADA), None) is None
    guardado = tmp_path / "saves" / "partida1.sav"
    leer = aplicacion.GuardadoBinario.leer_cabecera

    def con_k(self, archivo):
        #la cabecera v2 (Fase 8) trae el K; aquí se simula para probar solo el camino de carga
        cabecera = leer(self, archivo)
        cabecera.k = k_guardado
        return cabecera
    monkeypatch.setattr(aplicacion.GuardadoBinario, "leer_cabecera", con_k)
    vista = _VistaQueAnota(["salir"])
    assert app._sesion(vista, guardado) is None
    return usados, vista.mensajes


def test_al_cargar_gana_el_k_guardado_y_se_avisa_que_la_opcion_se_ignora(tmp_path, monkeypatch):
    """FR-017, FR-019 · US6-8 · guardada con K=7 y cargada con `--checkpoint-cada 20`: K=7 y el aviso"""
    usados, mensajes = _cargar_con_k_guardado(tmp_path, monkeypatch, 7, 20)
    assert usados == [20, 7]                           #la partida nueva con la opción; la cargada con el guardado
    avisos = [m for m in mensajes if "--checkpoint-cada" in m]
    assert len(avisos) == 1 and "K=7" in avisos[0]


@pytest.mark.parametrize("k_opcion", [None, 7])
def test_al_cargar_sin_la_opcion_o_con_el_mismo_k_no_hay_aviso(k_opcion, tmp_path, monkeypatch):
    """FR-017, FR-019 · US6-8 · sin la opción escrita, o con el mismo K, no hay aviso"""
    usados, mensajes = _cargar_con_k_guardado(tmp_path, monkeypatch, 7, k_opcion)
    assert usados[-1] == 7
    assert not any("--checkpoint-cada" in m for m in mensajes)
