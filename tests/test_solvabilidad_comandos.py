"""El servicio, el texto del reporte y el flujo de inicio de la verificación de resolubilidad (US1, US5, US6).

Con repositorios y clientes falsos y carpetas temporales; sin red y sin vistas reales salvo para comprobar el texto.
"""
import pytest

from adapters.almacen_llaves import AlmacenLlaves
from adapters.cliente_http import ErrorCliente
from adapters.salida_verificacion import lineas_reporte
from aplicacion import Aplicacion
from data.repositorio_cripta import RepositorioCripta
from data.repositorio_llaves import RepositorioLlaves
from dto.llave_dto import LlaveUbicacionDTO
from model.jugador_logica import Jugador
from model.partida_logica import Partida
from service.verificacion_service import VerificacionService
from tests.mapas_solvabilidad import armar_vector, cadena_de_llaves, cripta
from view.vista_consola import VistaConsola
from view.vista_silenciosa import VistaSilenciosa


class DatosFalsos:
    def __init__(self, id_cripta, version, inicial, salida, llave_salida):
        self.id_cripta, self.version = id_cripta, version
        self.sala_inicial, self.sala_salida, self.llave_salida = inicial, salida, llave_salida


class RepoCriptaFalso:
    """Lo que el servicio lee de RepositorioCripta: `datos` y `salas`."""

    def __init__(self, salas, inicial, salida, llave_salida, id_cripta="cripta-x"):
        self.datos = DatosFalsos(id_cripta, "v1", inicial, salida, llave_salida)
        self.salas = armar_vector(salas)


class FuenteContada:
    def __init__(self):
        self.contador = 0

    def solicitudes_realizadas(self):
        return self.contador


class RepoLlavesFalso:
    def __init__(self, llaves, consulta=1, falla=None):
        self.fuente = FuenteContada()
        self.llaves = [LlaveUbicacionDTO(i, s, e) for i, s, e in llaves]
        self.consulta = consulta
        self.falla = falla

    def cargar(self, id_cripta, version):
        if self.falla is not None:
            raise self.falla
        self.fuente.contador += self.consulta
        return list(self.llaves)


def _resoluble():
    salas, inicial, salida, llave_salida, llaves = cadena_de_llaves(3)
    return RepoCriptaFalso(salas, inicial, salida, llave_salida), RepoLlavesFalso(llaves)


def _no_resoluble():
    salas = cripta(6, [(1, 2, None), (2, 3, "kb"), (2, 4, "ka"), (3, 5, None), (4, 6, None)])
    llaves = [("ka", 5, None), ("kb", 6, "enemigo-y")]
    return RepoCriptaFalso(salas, 1, 5, "ka"), RepoLlavesFalso(llaves)


def test_el_servicio_da_el_orden_de_un_cripta_resoluble_con_las_listas_vacias_y_cuenta_la_consulta():
    """FR-009, FR-012, FR-014 · US1-1"""
    repo, llaves = _resoluble()
    reporte = VerificacionService(repo, llaves).verificar()
    assert reporte.id_cripta == "cripta-x" and reporte.resoluble is True
    assert reporte.orden == ["k0001", "k0002", "k0003"]
    assert reporte.llaves_inalcanzables == [] and reporte.puertas_frontera == [] and reporte.ciclos == []
    assert reporte.solicitudes == 1                       # la consulta de llaves


def test_el_servicio_arma_el_reporte_de_una_cripta_no_resoluble_con_valores_simples():
    """FR-012 · el reporte lista llaves, puertas, ubicaciones y ciclos como DTOs"""
    repo, llaves = _no_resoluble()
    reporte = VerificacionService(repo, llaves).verificar()
    assert reporte.resoluble is False and reporte.orden == []
    assert [(k.id_llave, k.id_sala, k.id_enemigo) for k in reporte.llaves_inalcanzables] == [
        ("ka", 5, None), ("kb", 6, "enemigo-y")]
    assert [(p.id_sala, p.id_destino, p.id_llave) for p in reporte.puertas_frontera] == [(2, 3, "kb"), (2, 4, "ka")] \
        or [(p.id_sala, p.id_destino, p.id_llave) for p in reporte.puertas_frontera] == [(2, 4, "ka"), (2, 3, "kb")]
    assert [[e.id_llave for e in ciclo] for ciclo in reporte.ciclos] == [["ka", "kb"]]
    # solo valores simples: ninguna referencia al modelo
    for p in reporte.puertas_frontera:
        assert isinstance(p.id_sala, int) and isinstance(p.direccion, str)


def test_el_texto_de_un_reporte_resoluble_es_el_del_contrato():
    """FR-014 · contrato reporte-verificacion.md"""
    repo, llaves = _resoluble()
    reporte = VerificacionService(repo, llaves).verificar()
    assert lineas_reporte(reporte) == [
        "Verificación de cripta-x: se puede ganar.",
        "Orden de llaves:",
        "  1. k0001",
        "  2. k0002",
        "  3. k0003",
    ]


def test_el_texto_de_un_reporte_no_resoluble_trae_solo_las_secciones_con_entradas():
    """FR-012 · contrato reporte-verificacion.md (sin ubicación, no tiene llave, sin ciclo)"""
    salas = cripta(3, [(1, 2, "fantasma"), (1, 3, None)])
    for s in salas[0].salidas:
        if s.destino is salas[2]:
            s.cerrada = s.opuesta.cerrada = True                   # cerrada y sin llave
    repo = RepoCriptaFalso(salas, 1, 2, "fantasma")
    reporte = VerificacionService(repo, RepoLlavesFalso([])).verificar()
    d_a, d_b = salas[0].salidas[0].direccion, salas[0].salidas[1].direccion
    assert lineas_reporte(reporte) == [
        "Verificación de cripta-x: NO se puede ganar.",
        "Llaves que no se pueden conseguir:",
        "  fantasma (sin ubicación)",
        "Puertas de la frontera bloqueada:",
        f"  sala 1, {d_a} -> sala 2: exige fantasma",
        f"  sala 1, {d_b} -> sala 3: no tiene llave",
    ]


def test_el_texto_del_ciclo_nombra_la_llave_su_sala_la_puerta_y_la_guardiana():
    """FR-012 · sección Ciclo del contrato, con la llave que la lleva un enemigo"""
    salas = cripta(2, [(1, 2, "k")])
    repo = RepoCriptaFalso(salas, 1, 2, "k")
    reporte = VerificacionService(repo, RepoLlavesFalso([("k", 2, "e1")])).verificar()
    d = salas[0].salidas[0].direccion
    assert lineas_reporte(reporte) == [
        "Verificación de cripta-x: NO se puede ganar.",
        "Llaves que no se pueden conseguir:",
        "  k (sala 2, la lleva el enemigo e1)",
        "Puertas de la frontera bloqueada:",
        f"  sala 1, {d} -> sala 2: exige k",
        "Ciclo:",
        f"  k (sala 2) está tras la puerta de la sala 1, {d}, que exige k",
    ]


def test_la_vista_de_consola_imprime_el_mismo_texto(capsys):
    """FR-014 · VistaConsola.mostrar_verificacion imprime las líneas del adaptador; VistaSilenciosa no hace nada"""
    repo, llaves = _resoluble()
    reporte = VerificacionService(repo, llaves).verificar()
    VistaConsola().mostrar_verificacion(reporte)
    assert capsys.readouterr().out.splitlines() == lineas_reporte(reporte)
    assert VistaSilenciosa().mostrar_verificacion(reporte) is None
    assert capsys.readouterr().out == ""


class VistaGrabadora(VistaSilenciosa):
    def __init__(self):
        self.reportes, self.mensajes = [], []

    def mostrar_verificacion(self, reporte):
        self.reportes.append(reporte)

    def mostrar_mensaje(self, texto):
        self.mensajes.append(texto)


class AppFalsa:
    """Lo que `_verificar_antes_de_jugar` lee de Aplicacion, con su método real."""

    _verificar_antes_de_jugar = Aplicacion._verificar_antes_de_jugar

    def __init__(self, servicio):
        self.servicio = servicio

    def _servicio_verificacion(self):
        return self.servicio


def test_cripta_resoluble_se_verifica_se_muestran_veredicto_y_orden_y_el_juego_arranca():
    """FR-014, FR-008 · US1-1"""
    repo, llaves = _resoluble()
    vista = VistaGrabadora()
    assert AppFalsa(VerificacionService(repo, llaves))._verificar_antes_de_jugar(vista, False) is True
    assert len(vista.reportes) == 1 and vista.reportes[0].resoluble is True
    assert vista.reportes[0].orden == ["k0001", "k0002", "k0003"]


def test_cripta_no_resoluble_sin_forzar_no_arranca_y_muestra_el_reporte():
    """FR-015 · US1-2 (escenario 4 del encargo)"""
    repo, llaves = _no_resoluble()
    vista = VistaGrabadora()
    assert AppFalsa(VerificacionService(repo, llaves))._verificar_antes_de_jugar(vista, False) is False
    assert len(vista.reportes) == 1 and vista.reportes[0].resoluble is False


def test_el_veredicto_no_cambia_con_lo_que_el_jugador_ya_exploro():
    """FR-001 · US1-3: el conocimiento del jugador no entra en la verificación"""
    salas = cripta(4, [(1, 2, None), (2, 3, "k"), (3, 4, None)])
    repo = RepoCriptaFalso(salas, 1, 4, "k")
    servicio = VerificacionService(repo, RepoLlavesFalso([("k", 4, None)]))
    antes = servicio.verificar()
    jugador = Jugador(vida_max=10, ataque=1, defensa=1, velocidad=100, inventario_max=5, sala=salas[0])
    partida = Partida(jugador, semilla=1)
    partida.jugador.sala = salas[1]                                    # el jugador explora salas
    for sala in salas:
        sala.conocimiento = 2
    despues = servicio.verificar()
    assert (antes.resoluble, antes.orden) == (despues.resoluble, despues.orden)
    assert [k.id_llave for k in antes.llaves_inalcanzables] == [k.id_llave for k in despues.llaves_inalcanzables]


def test_si_la_consulta_de_llaves_falla_se_muestra_el_error_no_hay_veredicto_y_el_juego_no_arranca():
    """FR-022 · la consulta falla"""
    repo = RepoCriptaFalso(*cadena_de_llaves(2)[:4])
    vista = VistaGrabadora()
    servicio = VerificacionService(repo, RepoLlavesFalso([], falla=ErrorCliente("falló la red")))
    assert AppFalsa(servicio)._verificar_antes_de_jugar(vista, False) is False
    assert vista.reportes == []
    assert vista.mensajes == ["Error de comunicación con el servicio: falló la red"]


class FuenteDeCripta:
    """Cliente falso que cuenta datos, páginas del esqueleto y la consulta de llaves en un solo contador."""

    def __init__(self, presupuesto):
        self.solicitudes = 0
        self.presupuesto = presupuesto
        self.paginas_pedidas = 0
        self.llaves_pedidas = 0

    def asignar_presupuesto(self, n):
        self.presupuesto = n

    def solicitudes_realizadas(self):
        return self.solicitudes

    def _contar(self):
        if self.solicitudes >= self.presupuesto:
            raise ErrorCliente("Presupuesto agotado")
        self.solicitudes += 1

    def datos_cripta(self, id_cripta):
        self._contar()
        return {"id": id_cripta, "version": "v1", "salas_total": 3, "paginas": 2, "salas_por_pagina": 2,
                "sala_inicial": 1, "sala_salida": 3, "llave_salida": "k", "presupuesto_solicitudes": self.presupuesto,
                "inventario_max": 5, "jugador": {"vida_max": 10, "ataque": 1, "defensa": 1, "velocidad": 100}}

    def pagina_esqueleto(self, id_cripta, pagina):
        self._contar()
        self.paginas_pedidas += 1
        if pagina == 1:
            salas = [{"id": 1, "nombre": "S1", "salidas": {"E": {"sala": 2}}},
                     {"id": 2, "nombre": "S2", "salidas": {"O": {"sala": 1}, "E": {"sala": 3, "cerrada": True, "llave": "k"}}}]
        else:
            salas = [{"id": 3, "nombre": "S3", "salidas": {"O": {"sala": 2, "cerrada": True, "llave": "k"}}}]
        return {"pagina": pagina, "total_paginas": 2, "salas": salas}

    def llaves(self, id_cripta):
        self._contar()
        self.llaves_pedidas += 1
        return {"llaves": [{"id": "k", "sala": 1}]}


class AppConRepos:
    """Aplicacion armada con su propio RepositorioCripta y el mismo cliente, como Aplicacion.__init__."""

    _verificar_antes_de_jugar = Aplicacion._verificar_antes_de_jugar
    _servicio_verificacion = Aplicacion._servicio_verificacion

    def __init__(self, cliente):
        self.cliente = cliente
        self.repo_cripta = RepositorioCripta(cliente)
        dtos = self.repo_cripta.cargar_esqueleto("cripta-x")            # lo que ya hace Aplicacion.__init__
        self.repo_cripta.construir_salas(dtos)


def test_el_esqueleto_se_baja_una_vez_y_la_consulta_de_llaves_cuenta_en_el_mismo_presupuesto(tmp_path, monkeypatch):
    """FR-004, FR-014 · el juego y la verificación comparten el esqueleto y el cliente"""
    monkeypatch.chdir(tmp_path)                                          # cache/llaves en la carpeta temporal
    cliente = FuenteDeCripta(presupuesto=4)
    app = AppConRepos(cliente)
    assert cliente.paginas_pedidas == 2 and cliente.solicitudes == 3       # datos + 2 páginas
    vista = VistaGrabadora()
    assert app._verificar_antes_de_jugar(vista, False) is True
    assert cliente.paginas_pedidas == 2                                    # no se vuelve a bajar el esqueleto
    assert cliente.llaves_pedidas == 1 and cliente.solicitudes == 4        # la consulta cuenta en el mismo contador
    assert vista.reportes[0].resoluble is True and vista.reportes[0].solicitudes == 1
    # otra corrida con el mismo archivo guardado (misma versión): no hay consulta
    otro = AppConRepos(FuenteDeCripta(presupuesto=4))
    assert otro._verificar_antes_de_jugar(VistaGrabadora(), False) is True
    assert otro.cliente.llaves_pedidas == 0


def test_el_presupuesto_agotado_en_la_consulta_muestra_el_error_y_no_da_veredicto(tmp_path, monkeypatch):
    """FR-004, FR-022 · la consulta de llaves pasa del presupuesto"""
    monkeypatch.chdir(tmp_path)
    app = AppConRepos(FuenteDeCripta(presupuesto=3))                      # se gasta todo en datos y esqueleto
    vista = VistaGrabadora()
    assert app._verificar_antes_de_jugar(vista, False) is False
    assert vista.reportes == [] and vista.mensajes[0].startswith("Error de comunicación con el servicio:")


def test_replay_y_cargar_una_partida_no_vuelven_a_verificar(tmp_path, monkeypatch):
    """FR-014 · --replay y cargar dentro de la sesión no verifican"""
    from tests.estado_fijo import AppFalsa as AppDeReplay, LectorFalso
    from tests.test_ir_a_guardado import AppDePrueba, JUGADA, VistaGuionada

    monkeypatch.chdir(tmp_path)

    def prohibido(self, *args, **kwargs):
        raise AssertionError("se verificó en replay o al cargar")

    class AppReplay(AppDeReplay):
        _verificar_antes_de_jugar = prohibido
        _servicio_verificacion = prohibido

    Aplicacion.reproducir(AppReplay("v1", "v1"), LectorFalso(1, ["w"], "v1", "v1"))

    class AppCarga(AppDePrueba):
        _verificar_antes_de_jugar = prohibido
        _servicio_verificacion = prohibido

    app = AppCarga()
    assert app._sesion(VistaGuionada(JUGADA), None) is None                # se juega y se guarda
    guardado = tmp_path / "saves" / "partida1.sav"
    assert app._sesion(VistaGuionada(["salir"]), guardado) is None         # se carga: no se verifica


# --- --forzar (T024) --------------------------------------------------------------------------------

def test_con_forzar_una_cripta_no_resoluble_muestra_el_reporte_y_el_juego_arranca():
    """FR-015, FR-016 · US5-1"""
    repo, llaves = _no_resoluble()
    vista = VistaGrabadora()
    assert AppFalsa(VerificacionService(repo, llaves))._verificar_antes_de_jugar(vista, True) is True
    assert len(vista.reportes) == 1 and vista.reportes[0].resoluble is False


def test_con_forzar_si_la_consulta_falla_se_muestra_el_error_sin_veredicto_y_el_juego_arranca():
    """FR-016, FR-022 · con --forzar se juega sin veredicto"""
    repo = RepoCriptaFalso(*cadena_de_llaves(2)[:4])
    vista = VistaGrabadora()
    servicio = VerificacionService(repo, RepoLlavesFalso([], falla=ErrorCliente("falló la red")))
    assert AppFalsa(servicio)._verificar_antes_de_jugar(vista, True) is True
    assert vista.reportes == []
    assert vista.mensajes == ["Error de comunicación con el servicio: falló la red"]


def _correr_main(monkeypatch, argumentos):
    """Corre main() con una Aplicacion espía y devuelve los `forzar` con que se llamó a jugar."""
    import sys

    import main

    llamadas = []

    class AplicacionEspia:
        def __init__(self, *args):
            pass

        def jugar(self, ruta_carga=None, forzar=False):
            llamadas.append(forzar)

    monkeypatch.setattr(main, "Aplicacion", AplicacionEspia)
    monkeypatch.setattr(sys, "argv", ["main.py"] + argumentos)
    main.main()
    return llamadas


def test_main_acepta_forzar_y_se_lo_pasa_a_jugar(monkeypatch):
    """FR-016 · US5-1: la opción --forzar llega a Aplicacion.jugar"""
    assert _correr_main(monkeypatch, ["cripta-x", "--offline", "--forzar"]) == [True]


def test_main_sin_forzar_juega_con_forzar_falso(monkeypatch):
    """FR-015 · sin la opción, una cripta no resoluble no arranca"""
    assert _correr_main(monkeypatch, ["cripta-x", "--offline"]) == [False]
