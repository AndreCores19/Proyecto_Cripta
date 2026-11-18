"""Guardado v2: el K en la cabecera y la incompatibilidad con la parte uno (spec 005, Fase 8, US5).

Cómo se hicieron los archivos de tests/fixtures (T053):
- `guardado_v1.sav`: se sacaron de git, en el commit 0b0663a (la parte uno), `adapters/guardado_binario.py`,
  `dto/contenido_sala_dto.py` y `structures/vector_busqueda.py` a una carpeta temporal fuera del repo, y se
  corrió su `GuardadoBinario().guardar` (VERSION_FORMATO = 1) con una cabecera ("cripta-de-prueba", "v1",
  "c1", semilla 5), cuatro contenidos de sala (uno None) y siete comandos. Solo se copiaron los bytes.
- `guardado_v1_corto.sav`: los primeros 20 bytes del anterior (magic y versión intactos, más corto que la
  cabecera v2).

Las partidas se juegan por `Aplicacion._sesion` (el camino real de `guardar` y `cargar`) sobre un mundo de
prueba con fichas falsas y sin red; al cargar se arma un mundo nuevo y se vuelven a ejecutar los comandos.
"""
import random
from pathlib import Path

import pytest

import aplicacion
from adapters.guardado_binario import (CabeceraGuardado, ErrorGuardado, GuardadoBinario, MAGIC,
                                       VERSION_FORMATO)
from aplicacion import Aplicacion
from controller.controlador import Controlador
from linea_tiempo_apoyo import _elegir_comando, armar_mundo, registrar_vivo, resumen_plano
from model.linea_tiempo_logica import K_POR_DEFECTO
from view.vista_silenciosa import VistaSilenciosa

FIXTURES = Path(__file__).parent / "fixtures"
ID_CRIPTA = "cripta-de-prueba"
VERSION = "v1"
CATALOGO = "c1"
INCOMPATIBLE = "Formato de guardado incompatible: el archivo es v1 y este programa usa v2"


class _CatalogoInfo:
    def version(self):
        return CATALOGO


class AppDeGuardado:
    """Lo que `_sesion`, `guardar` y `cargar` leen de Aplicacion, con sus métodos reales, sobre mundos de
    prueba: cada sesión que carga arma un mundo nuevo (como `_reiniciar_salas`)."""

    _sesion = Aplicacion._sesion
    _reejecutar = Aplicacion._reejecutar
    guardar_partida = Aplicacion.guardar_partida
    ruta_guardado = Aplicacion.ruta_guardado
    validar_guardado = Aplicacion.validar_guardado

    def __init__(self, k=None, semilla=3, preparar=None, clase=None, **mundo):
        self.checkpoint_cada = k
        self.nombre_jugador = "Prueba"
        self.repo_catalogo = _CatalogoInfo()
        parametros = dict(salas=7, enemigos=5, cazadores=2, vida_jugador=5000)
        parametros.update(mundo)
        if clase is not None:
            parametros["clase_partida"] = clase
        self._semilla, self._parametros, self._preparar = semilla, parametros, preparar
        self.mundos = []
        self.servicios = []
        self._nuevo_mundo()

    def _nuevo_mundo(self):
        m = armar_mundo(self._semilla, **self._parametros)
        if self._preparar is not None:
            self._preparar(m)
        m.partida.sala_salida = None                 #sin victoria: la partida no termina sola
        m.datos.id_cripta, m.datos.version = ID_CRIPTA, VERSION
        m.fabrica.nueva_partida = lambda semilla: self._partida(m, semilla)
        self.mundo, self.fabrica, self.repo_cripta, self.dtos = m, m.fabrica, m.repo, m.dtos
        self.mundos.append(m)

    @staticmethod
    def _partida(m, semilla):
        assert semilla in (None, m.partida.semilla)
        return m.partida

    def _reiniciar_salas(self):
        self._nuevo_mundo()


class VistaGuion(VistaSilenciosa):
    """Da los comandos de una lista; anota los resúmenes de `historia` y los mensajes."""

    def __init__(self, comandos):
        self.comandos = list(comandos)
        self.historias = []
        self.mensajes = []

    def pedir_comando(self):
        return self.comandos.pop(0) if self.comandos else "salir"

    def mostrar_historia(self, resumen):
        self.historias.append(resumen)

    def mostrar_mensaje(self, texto):
        self.mensajes.append(texto)


@pytest.fixture
def espia_servicios(monkeypatch):
    """Anota cada servicio que arma la aplicación (para mirar la partida viva y su línea de tiempo)."""
    servicios = []
    original = aplicacion._crear_servicio

    def espia(app, partida, k=None):
        servicio = original(app, partida, k)
        servicios.append(servicio)
        return servicio
    monkeypatch.setattr(aplicacion, "_crear_servicio", espia)
    return servicios


def _comandos(n, semilla=5, con_pergaminos=False, **mundo):
    """n comandos deterministas sobre un mundo igual al de la app (sin línea de tiempo)."""
    app = AppDeGuardado(con_pergaminos=con_pergaminos, **mundo)
    servicio = aplicacion.JuegoService(app.mundo.partida, app.fabrica)
    azar = random.Random(semilla)
    controlador = Controlador(servicio, VistaSilenciosa(), None, None)
    comandos = []
    for _ in range(n):
        comando = _elegir_comando(azar, servicio, con_pergaminos)
        controlador.ejecutar(comando)
        comandos.append(comando)
    return comandos, app.mundo.partida


def _consultas(partida):
    """Todas las `#k` y un instante de cada 7 (más el último): lo que se compara antes y después."""
    pedidas = [f"historia #{k}" for k in range(1, partida.acciones_jugador + 1)]
    pedidas += [f"historia {t}" for t in range(0, partida.reloj + 1, 7)] + [f"historia {partida.reloj}"]
    return pedidas


def _respuestas(vista):
    return [resumen_plano(r) for r in vista.historias]


def _guardar_y_cargar(tmp_path, monkeypatch, espia_servicios, comandos, k=7, k_al_cargar=None, **mundo):
    """Juega, consulta todo, guarda; carga en otra app y vuelve a consultar. Devuelve
    (antes, después, app, app_cargada, vista de la carga)."""
    monkeypatch.chdir(tmp_path)
    app = AppDeGuardado(k=k, **mundo)
    primera = VistaGuion(comandos)
    #las consultas van después de jugar y antes de guardar, con el juego ya en su estado final
    primera.comandos.append("__consultas__")
    vista = primera
    original = vista.pedir_comando

    def pedir():
        comando = original()
        if comando == "__consultas__":
            vista.comandos = _consultas(espia_servicios[-1].partida) + ["guardar partida1", "salir"]
            return original()
        return comando
    vista.pedir_comando = pedir
    assert app._sesion(vista, None) is None
    antes = _respuestas(vista)
    partida = espia_servicios[-1].partida
    cargada = AppDeGuardado(k=k_al_cargar, **mundo)
    segunda = VistaGuion(_consultas(partida) + ["salir"])
    assert cargada._sesion(segunda, tmp_path / "saves" / "partida1.sav") is None
    return antes, _respuestas(segunda), app, cargada, segunda


# ---------------------------------------------------------------- US5-1, US5-2 (FR-017, FR-010)

def test_guardar_y_cargar_da_las_mismas_respuestas_de_historia(tmp_path, monkeypatch, espia_servicios):
    """FR-017 · US5-1 · una línea de tiempo larga (K=7): tras guardar y cargar, cada `historia #k` y cada
    instante consultado responde lo mismo que antes de guardar"""
    comandos, _ = _comandos(120)
    antes, despues, _, _, _ = _guardar_y_cargar(tmp_path, monkeypatch, espia_servicios, comandos)
    viva, recargada = espia_servicios[0], espia_servicios[1]
    assert viva.partida.acciones_jugador >= 70 and len(antes) >= 150
    assert despues == antes
    assert recargada.partida is not viva.partida
    assert resumen_plano(recargada.partida) == resumen_plano(viva.partida)
    assert recargada.linea_tiempo.k == 7
    assert list(recargada.linea_tiempo.relojes) == list(viva.linea_tiempo.relojes)


def test_guardar_tras_un_pergamino_y_cargar_sigue_sin_las_acciones_revertidas(tmp_path, monkeypatch,
                                                                              espia_servicios):
    """FR-010, FR-017 · US5-2 · guardado tras lecturas de pergamino: la línea cargada excluye lo revertido y
    los efectos del libro valen (pergamino gastado, sala poblada), así que las respuestas son las mismas"""
    comandos, partida = _comandos(150, semilla=8, con_pergaminos=True)
    assert partida.retrocesos >= 1
    #el último comando antes de guardar es una lectura de pergamino
    comandos = comandos + ["retroceder"]
    antes, despues, _, _, _ = _guardar_y_cargar(tmp_path, monkeypatch, espia_servicios, comandos,
                                                con_pergaminos=True)
    viva, recargada = espia_servicios[0], espia_servicios[1]
    assert viva.partida.retrocesos >= 1
    assert despues == antes
    n = recargada.partida.acciones_jugador
    assert n == viva.partida.acciones_jugador == len(recargada.linea_tiempo)
    assert recargada.historia_por_accion(n + 1).motivo == "accion_inexistente"
    assert resumen_plano(recargada.partida) == resumen_plano(viva.partida)


def test_el_archivo_no_guarda_consultas_ni_avisos(tmp_path, monkeypatch):
    """FR-007, FR-017 · un `guardar` justo después de una consulta escribe los mismos bytes que sin ella"""
    comandos, _ = _comandos(40)
    monkeypatch.chdir(tmp_path)
    AppDeGuardado(k=7)._sesion(VistaGuion(comandos + ["guardar sin", "salir"]), None)
    AppDeGuardado(k=7)._sesion(VistaGuion(comandos + ["historia 10", "historia #2", "historia zz",
                                                      "historia 999999", "guardar con", "salir"]), None)
    assert (tmp_path / "saves" / "con.sav").read_bytes() == (tmp_path / "saves" / "sin.sav").read_bytes()


# ---------------------------------------------------------------- US5-3, US5-4: la parte uno (FR-018)

@pytest.mark.parametrize("nombre", ["guardado_v1.sav", "guardado_v1_corto.sav"])
def test_un_archivo_v1_se_rechaza_como_incompatible(nombre):
    """FR-018 · US5-3 · el v1 escrito por la parte uno, también el de 20 bytes: incompatible, no truncado"""
    ruta = FIXTURES / nombre
    assert ruta.read_bytes()[:6] == MAGIC + b"\x01\x00"
    with pytest.raises(ErrorGuardado) as error:
        with open(ruta, "rb") as archivo:
            GuardadoBinario().leer_cabecera(archivo)
    assert str(error.value) == INCOMPATIBLE
    assert AppDeGuardado().validar_guardado(ruta) == f"No se puede cargar: {INCOMPATIBLE}"


@pytest.mark.parametrize("nombre", ["guardado_v1.sav", "guardado_v1_corto.sav", "vacio.sav", "aleatorio.sav"])
def test_una_carga_rechazada_no_cambia_el_juego_ni_el_archivo(nombre, tmp_path, monkeypatch, espia_servicios):
    """FR-018 · US5-4 · `cargar` de un archivo rechazado: nada se carga, la partida actual sigue igual (estado,
    reloj y comandos) y el archivo no cambia (bytes y fecha de modificación)"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "saves").mkdir()
    destino = tmp_path / "saves" / "viejo.sav"
    if nombre == "vacio.sav":
        destino.write_bytes(b"")
    elif nombre == "aleatorio.sav":
        destino.write_bytes(random.Random(1).randbytes(300))
    else:
        destino.write_bytes((FIXTURES / nombre).read_bytes())
    bytes_antes, fecha_antes = destino.read_bytes(), destino.stat().st_mtime_ns
    comandos, _ = _comandos(30)
    huellas = []

    vista = VistaGuion(comandos + ["__huella__", "cargar viejo", "__huella__", "salir"])
    original = vista.pedir_comando

    def pedir():
        comando = original()
        while comando == "__huella__":
            p = espia_servicios[-1].partida
            huellas.append((p.reloj, p.acciones_jugador, resumen_plano(p), len(espia_servicios)))
            comando = original()
        return comando
    vista.pedir_comando = pedir
    app = AppDeGuardado(k=7)
    assert app._sesion(vista, None) is None                   #no salió a cargar nada
    assert huellas[0] == huellas[1]
    assert vista.mensajes[-1].startswith("No se puede cargar:")
    assert len(app.mundos) == 1                               #ningún mundo nuevo armado
    assert destino.read_bytes() == bytes_antes and destino.stat().st_mtime_ns == fecha_antes


# ---------------------------------------------------------------- US5-5: archivos ilegibles (FR-018)

def _guardado_v2(tmp_path, k=7):
    ruta = tmp_path / "bueno.sav"
    from dto.contenido_sala_dto import ContenidoSalaDTO, InstanciaEnemigoDTO
    contenidos = [ContenidoSalaDTO(1, [], ["espada"], []),
                  ContenidoSalaDTO(2, [InstanciaEnemigoDTO("e1", "rata", None)], ["curar"], [])]
    GuardadoBinario().guardar(ruta, CabeceraGuardado(ID_CRIPTA, VERSION, CATALOGO, 5, k=k),
                              contenidos, ["w", "esperar", "atacar"])
    return ruta


def test_un_v2_bueno_se_valida_y_trae_su_k(tmp_path):
    """FR-017, FR-018 · el archivo v2 de ida y vuelta: versión 2, K guardado y comandos"""
    ruta = _guardado_v2(tmp_path, k=13)
    assert VERSION_FORMATO == 2 and ruta.read_bytes()[:6] == MAGIC + b"\x02\x00"
    cabecera = GuardadoBinario().validar(ruta)
    assert (cabecera.k, cabecera.semilla, cabecera.id_cripta) == (13, 5, ID_CRIPTA)
    assert GuardadoBinario().leer_comandos(ruta) == ["w", "esperar", "atacar"]
    assert AppDeGuardado().validar_guardado(ruta) is None


def _casos_ilegibles(tmp_path):
    bueno = _guardado_v2(tmp_path).read_bytes()
    casos = {"vacio": b"", "cinco_bytes": bueno[:5], "aleatorio": random.Random(7).randbytes(200)}
    for largo in (6, 10, 30, 45, len(bueno) - 20, len(bueno) - 1):
        casos[f"v2_cortado_{largo}"] = bueno[:largo]
    k_cero = tmp_path / "k_cero.sav"
    _guardado_v2(tmp_path, k=0).rename(k_cero)
    casos["k_cero"] = k_cero.read_bytes()
    return casos


def test_archivos_vacios_cortados_aleatorios_o_con_k_cero_son_ilegibles(tmp_path):
    """FR-018 · US5-5 · vacío, truncado (en la cabecera, las salas, los comandos o el índice), bytes al azar y
    K = 0: ErrorGuardado y nunca se cargan"""
    for nombre, datos in _casos_ilegibles(tmp_path).items():
        ruta = tmp_path / f"{nombre}.sav"
        ruta.write_bytes(datos)
        with pytest.raises(ErrorGuardado):
            GuardadoBinario().validar(ruta)
        mensaje = AppDeGuardado().validar_guardado(ruta)
        assert mensaje is not None and mensaje.startswith("No se puede cargar:"), nombre
        assert INCOMPATIBLE not in mensaje, nombre


def test_menos_de_seis_bytes_es_truncado_y_k_cero_no_es_un_entero_positivo(tmp_path):
    """FR-018 · los mensajes: menos de 6 bytes → truncado; K = 0 → no se puede leer"""
    casos = _casos_ilegibles(tmp_path)
    for nombre in ("vacio", "cinco_bytes", "v2_cortado_10"):
        ruta = tmp_path / f"{nombre}.sav"
        ruta.write_bytes(casos[nombre])
        with pytest.raises(ErrorGuardado, match="truncado"):
            GuardadoBinario().validar(ruta)
    ruta = tmp_path / "k0.sav"
    ruta.write_bytes(casos["k_cero"])
    with pytest.raises(ErrorGuardado, match="K=0"):
        GuardadoBinario().validar(ruta)


# ---------------------------------------------------------------- T055: el K guardado gana (FR-017, FR-019)

@pytest.mark.parametrize("k_al_cargar, aviso", [(20, True), (None, False), (7, False)])
def test_el_k_guardado_gana_y_solo_se_avisa_si_la_opcion_se_escribio_y_difiere(k_al_cargar, aviso, tmp_path,
                                                                              monkeypatch, espia_servicios):
    """FR-017, FR-019 · guardada con K=7 y cargada con K=20, sin opción o con 7: siempre K=7, los puntos de
    control en múltiplos de 7, y el aviso solo con 20"""
    comandos, _ = _comandos(60)
    antes, despues, _, _, segunda = _guardar_y_cargar(tmp_path, monkeypatch, espia_servicios, comandos,
                                                      k=7, k_al_cargar=k_al_cargar)
    assert GuardadoBinario().validar(tmp_path / "saves" / "partida1.sav").k == 7
    recargada = espia_servicios[1]
    linea = recargada.linea_tiempo
    assert linea.k == 7
    assert len(linea.puntos) == len(linea) // 7 + 1
    assert despues == antes
    avisos = [m for m in segunda.mensajes if "--checkpoint-cada" in m]
    if aviso:
        assert avisos == ["Se ignora --checkpoint-cada: esta partida se guardó con K=7."]
    else:
        assert avisos == []


def test_sin_la_opcion_se_guarda_el_k_por_defecto(tmp_path, monkeypatch):
    """FR-017, FR-019 · una partida jugada sin `--checkpoint-cada` guarda `K_POR_DEFECTO`"""
    comandos, _ = _comandos(10)
    monkeypatch.chdir(tmp_path)
    AppDeGuardado()._sesion(VistaGuion(comandos + ["guardar p", "salir"]), None)
    assert GuardadoBinario().validar(tmp_path / "saves" / "p.sav").k == K_POR_DEFECTO
