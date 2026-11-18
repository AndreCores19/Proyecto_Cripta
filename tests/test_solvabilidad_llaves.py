"""La consulta de llaves: solicitud contada, archivo guardado por versión, paquete sin conexión y grabación (US7).

Todo con clientes falsos y carpetas temporales; no usa la red.
"""
import json
import os

import pytest

import grabar_offline
from adapters import cliente_http
from adapters.almacen_llaves import AlmacenLlaves
from adapters.cliente_http import ClienteHttp, ErrorCliente
from adapters.cliente_offline import ClienteOffline, ErrorOffline
from data.repositorio_llaves import RepositorioLlaves

LLAVES = [{"id": "llave-a", "sala": 2}, {"id": "llave-b", "sala": 5, "enemigo": "enemigo-1"}]


class RespuestaFalsa:
    def __init__(self, cuerpo, codigo=200):
        self.cuerpo = cuerpo
        self.status_code = codigo

    def json(self):
        return self.cuerpo


def _falso_get(monkeypatch, cuerpo):
    llamadas = []

    def get(url, params=None, headers=None, timeout=None):
        llamadas.append((url, params, headers))
        return RespuestaFalsa(cuerpo)

    monkeypatch.setattr(cliente_http.requests, "get", get)
    return llamadas


def test_la_consulta_de_llaves_cuenta_una_solicitud_y_respeta_el_presupuesto(monkeypatch):
    """FR-002, FR-004 · US7-1"""
    llamadas = _falso_get(monkeypatch, {"llaves": LLAVES})
    cliente = ClienteHttp("http://servicio/v1", timeout=1)
    cliente.asignar_presupuesto(2)
    assert cliente.llaves("cripta-x") == {"llaves": LLAVES}
    assert cliente.solicitudes_realizadas() == 1
    url, params, cabeceras = llamadas[0]
    assert url == "http://servicio/v1/criptas/cripta-x/llaves"
    assert "X-Cripta-Client-Id" in cabeceras
    cliente.llaves("cripta-x")
    with pytest.raises(ErrorCliente):                          # presupuesto agotado: la tercera no sale
        cliente.llaves("cripta-x")
    assert len(llamadas) == 2


class FuenteFalsa:
    """Cliente falso con las llaves y un contador de solicitudes."""

    def __init__(self, llaves=None):
        self.respuesta = {"llaves": LLAVES if llaves is None else llaves}
        self.solicitudes = 0

    def llaves(self, id_cripta):
        self.solicitudes += 1
        return self.respuesta


def _datos(llaves):
    return [(x.id_llave, x.id_sala, x.id_enemigo) for x in llaves]


def test_otra_version_vuelve_a_preguntar_y_el_archivo_queda_con_la_version_nueva(tmp_path):
    """FR-005 · US7-2"""
    almacen = AlmacenLlaves(tmp_path)
    repo = RepositorioLlaves(FuenteFalsa(), almacen)
    primera = repo.cargar("cripta-x", "v1")
    assert repo.fuente.solicitudes == 1
    assert almacen.leer("cripta-x")[0] == "v1"
    repo.fuente.respuesta = {"llaves": [{"id": "llave-c", "sala": 9}]}
    segunda = repo.cargar("cripta-x", "v2")                    # la versión cambió: se pregunta otra vez
    assert repo.fuente.solicitudes == 2
    assert _datos(segunda) == [("llave-c", 9, None)]
    assert _datos(primera) == [("llave-a", 2, None), ("llave-b", 5, "enemigo-1")]
    version, guardadas = almacen.leer("cripta-x")
    assert version == "v2" and guardadas == [{"id": "llave-c", "sala": 9}]


def test_la_misma_version_usa_lo_guardado_sin_hacer_solicitud(tmp_path):
    """FR-005, FR-004 · US7-3"""
    AlmacenLlaves(tmp_path).guardar("cripta-x", "v1", LLAVES)           # de una corrida anterior
    repo = RepositorioLlaves(FuenteFalsa(), AlmacenLlaves(tmp_path))
    llaves = repo.cargar("cripta-x", "v1")
    assert repo.fuente.solicitudes == 0
    assert _datos(llaves) == [("llave-a", 2, None), ("llave-b", 5, "enemigo-1")]


def test_un_archivo_danado_o_incompleto_se_trata_como_si_faltara(tmp_path):
    """FR-005 · el archivo roto no da un veredicto falso: se vuelve a preguntar"""
    almacen = AlmacenLlaves(tmp_path)
    (tmp_path / "cripta-x.json").write_text("{no es json", encoding="utf-8")
    assert almacen.leer("cripta-x") is None
    (tmp_path / "cripta-x.json").write_text(json.dumps({"version": "v1"}), encoding="utf-8")
    assert almacen.leer("cripta-x") is None
    repo = RepositorioLlaves(FuenteFalsa(), almacen)
    repo.cargar("cripta-x", "v1")
    assert repo.fuente.solicitudes == 1
    assert almacen.leer("cripta-x")[0] == "v1"


def test_el_archivo_guarda_version_y_llaves_y_el_enemigo_falta_si_la_llave_esta_en_una_sala(tmp_path):
    """FR-002, FR-005 · formato de cache-llaves.md"""
    AlmacenLlaves(tmp_path).guardar("cripta-x", "v1", LLAVES)
    contenido = json.loads((tmp_path / "cripta-x.json").read_text(encoding="utf-8"))
    assert contenido == {"version": "v1", "llaves": LLAVES}
    assert "enemigo" not in contenido["llaves"][0] and contenido["llaves"][1]["enemigo"] == "enemigo-1"


def test_el_almacen_rechaza_ids_con_separadores_de_ruta(tmp_path):
    """FR-005 · el id de cripta no puede salir de la carpeta"""
    with pytest.raises(ValueError):
        AlmacenLlaves(tmp_path).guardar("../fuera", "v1", [])


def _paquete(tmp_path, ids):
    for id_cripta in ids:
        carpeta = tmp_path / id_cripta
        carpeta.mkdir()
        (carpeta / "datos.json").write_text("{}", encoding="utf-8")


def test_el_cliente_sin_conexion_lee_llaves_json_y_no_cuenta_solicitudes(tmp_path):
    """FR-006 · leer el paquete sin conexión"""
    _paquete(tmp_path, ["cripta-x"])
    (tmp_path / "cripta-x" / "llaves.json").write_text(json.dumps({"llaves": LLAVES}), encoding="utf-8")
    cliente = ClienteOffline(str(tmp_path))
    assert cliente.llaves("cripta-x") == {"llaves": LLAVES}
    assert cliente.solicitudes_realizadas() == 0
    _paquete(tmp_path, ["cripta-y"])                            # sin llaves.json: un paquete grabado antes de esta función
    with pytest.raises(ErrorOffline):
        cliente.llaves("cripta-y")


class ClienteGrabador:
    """Cliente HTTP falso para grabar: sirve las criptas de `SERVIDAS`; puede fallar en una."""

    SERVIDAS = ["cripta-a", "cripta-b"]
    FALLA_EN = None
    LISTADO_VACIO = False

    def __init__(self, url=None, timeout=None):
        self.solicitudes = 0

    def listar_criptas(self):
        if ClienteGrabador.LISTADO_VACIO:
            return {"criptas": []}
        return {"criptas": [{"id": i} for i in ClienteGrabador.SERVIDAS]}

    def version_catalogo(self):
        return {"version": "c1"}

    def datos_cripta(self, id_cripta):
        if id_cripta == ClienteGrabador.FALLA_EN:
            raise ErrorCliente("falló la red")
        self.solicitudes += 1
        return {"id": id_cripta, "version": "v1", "llave_salida": "llave-a"}

    def pagina_esqueleto(self, id_cripta, pagina):
        return {"pagina": 1, "total_paginas": 1, "salas": [{"id": 1, "nombre": "S1", "salidas": {}}]}

    def contenido_salas(self, id_cripta, ids):
        return {"contenido": [{"sala": 1, "enemigos": [], "objetos": [], "trampas": []}]}

    def catalogo(self, ids):
        return {"entidades": []}

    def llaves(self, id_cripta):
        return {"llaves": [{"id": "llave-a", "sala": 1}]}


@pytest.fixture
def paquete(tmp_path, monkeypatch):
    monkeypatch.setattr(grabar_offline, "CARPETA", str(tmp_path))
    monkeypatch.setattr(grabar_offline, "ClienteHttp", ClienteGrabador)
    ClienteGrabador.SERVIDAS = ["cripta-a", "cripta-b"]
    ClienteGrabador.FALLA_EN = None
    ClienteGrabador.LISTADO_VACIO = False
    _paquete(tmp_path, ["cripta-vieja"])                        # una cripta que el servicio ya no sirve
    return tmp_path


def test_grabar_escribe_llaves_json_por_cripta_y_quita_las_criptas_que_el_servicio_no_lista(paquete):
    """FR-006 · el paquete tiene solo criptas servidas, cada una con sus llaves"""
    grabar_offline.grabar()
    for id_cripta in ("cripta-a", "cripta-b"):
        contenido = json.loads((paquete / id_cripta / "llaves.json").read_text(encoding="utf-8"))
        assert contenido == {"llaves": [{"id": "llave-a", "sala": 1}]}
    assert not (paquete / "cripta-vieja").exists()


def test_con_un_listado_vacio_no_se_borra_nada(paquete):
    """FR-006 · un listado correcto pero vacío no borra el paquete"""
    ClienteGrabador.LISTADO_VACIO = True
    grabar_offline.grabar()
    assert (paquete / "cripta-vieja" / "datos.json").exists()


def test_si_falla_la_grabacion_de_una_cripta_no_se_borra_nada(paquete):
    """FR-006 · un fallo a mitad deja el paquete como está"""
    ClienteGrabador.FALLA_EN = "cripta-b"
    with pytest.raises(ErrorCliente):
        grabar_offline.grabar()
    assert (paquete / "cripta-vieja" / "datos.json").exists()


def test_solo_se_quitan_carpetas_de_criptas_no_archivos_ni_carpetas_ajenas(paquete):
    """FR-006 · se tocan solo subcarpetas directas que son criptas del paquete (tienen datos.json)"""
    (paquete / "otra-cosa").mkdir()
    (paquete / "otra-cosa" / "notas.txt").write_text("x", encoding="utf-8")
    (paquete / "suelto.json").write_text("{}", encoding="utf-8")
    grabar_offline.grabar()
    assert (paquete / "otra-cosa" / "notas.txt").exists() and (paquete / "suelto.json").exists()
    assert not (paquete / "cripta-vieja").exists()
