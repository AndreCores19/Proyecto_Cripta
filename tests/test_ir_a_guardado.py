"""Guardar y cargar una partida con niebla, antorcha y un viaje de «ir a» (T056 · FR-012, SC-005).

Se juega por Aplicacion._sesion (el camino real de `guardar` y `cargar`), con una fábrica falsa que arma
la cripta de nuevo en cada partida y sin red. Se guarda con GuardadoBinario y se carga con la misma
_sesion, que reconstruye las salas y reejecuta los comandos guardados.
"""
from aplicacion import Aplicacion
from adapters.guardado_binario import GuardadoBinario
from model.jugador_logica import Jugador
from model.objeto_logica import Objeto
from model.partida_logica import Partida
from tests.estado_fijo import FabricaFalsa, _RepoCatalogo, _RepoCripta
from tests.mapas_cazador import cadena
from tests.test_niebla_retroceso import instantanea_conocimiento
from view.vista_silenciosa import VistaSilenciosa

ID_CRIPTA = "cripta-de-prueba"


class FabricaDeCadena(FabricaFalsa):
    """Fábrica falsa: cada nueva_partida arma salas nuevas (cadena de 6, antorcha en la primera)."""

    def __init__(self):
        super().__init__()
        self.mundos = []                       # (salas, partida) de cada partida creada

    def iniciar(self):
        pass

    def nueva_partida(self, semilla=None):
        salas, _ = cadena([100] * 5)
        salas[0].objetos.append(Objeto(1, "antorcha", "Antorcha", "antorcha", 1, 1, duracion=10 ** 6))
        jugador = Jugador(vida_max=10 ** 6, ataque=10, defensa=10 ** 6, velocidad=100,
                          inventario_max=10, sala=salas[0])
        partida = Partida(jugador, semilla=semilla)
        self.mundos.append((salas, partida))
        return partida


class _RepoConSalas(_RepoCripta):
    contenidos = []

    def __init__(self, version):
        super().__init__(version)
        self.datos.id_cripta = ID_CRIPTA

    def construir_salas(self, dtos):
        pass


class AppDePrueba:
    """Lo mínimo que _sesion y los comandos guardar/cargar leen de Aplicacion, con sus métodos reales."""

    _sesion = Aplicacion._sesion
    _reejecutar = Aplicacion._reejecutar
    _reiniciar_salas = Aplicacion._reiniciar_salas
    guardar_partida = Aplicacion.guardar_partida
    ruta_guardado = Aplicacion.ruta_guardado
    validar_guardado = Aplicacion.validar_guardado

    def __init__(self):
        self.nombre_jugador = "Prueba"
        self.fabrica = FabricaDeCadena()
        self.repo_cripta = _RepoConSalas("v1")
        self.repo_catalogo = _RepoCatalogo("c1")
        self.dtos = []


class VistaGuionada(VistaSilenciosa):
    def __init__(self, comandos):
        self.comandos = list(comandos)

    def pedir_comando(self):
        return self.comandos.pop(0) if self.comandos else "salir"


# antorcha, dos entradas con ella, una puerta observada al salir, y un viaje de dos pasos
JUGADA = ["recoger", "usar", "d", "d", "a", "ir a 4", "guardar partida1", "salir"]


def test_guardar_y_cargar_reconstruye_el_conocimiento_y_guarda_pasos_no_la_orden(tmp_path, monkeypatch):
    """FR-012, FR-024 · SC-005 · T056"""
    monkeypatch.chdir(tmp_path)                 # BitacoraPartida("saves") y los guardados van a la carpeta temporal
    app = AppDePrueba()

    assert app._sesion(VistaGuionada(JUGADA), None) is None
    salas, partida = app.fabrica.mundos[0]
    original = instantanea_conocimiento(salas, partida)
    niveles, puertas, conocidas = original
    assert partida.jugador.sala is salas[3]                    # el viaje llegó a la sala 4
    assert [n for _, n in niveles] == [2, 2, 2, 2, 2, 1]       # la antorcha explora a las vecinas; la 6 solo se avista
    assert any(m != 0 for _, _, m in puertas)                  # hay puertas observadas
    assert len(conocidas) == 6

    guardado = tmp_path / "saves" / "partida1.sav"
    assert app.validar_guardado(guardado) is None
    comandos = GuardadoBinario().leer_comandos(guardado)
    assert comandos == ["recoger", "usar", "d", "d", "a", "d", "d"]   # los pasos del viaje como movimientos
    assert not any(c.startswith("ir") for c in comandos)              # la orden no se guarda

    # cargar: _sesion con la ruta del guardado reconstruye las salas y reejecuta los comandos guardados
    assert app._sesion(VistaGuionada(["guardar copia", "salir"]), guardado) is None
    salas2, partida2 = app.fabrica.mundos[1]
    assert salas2[0] is not salas[0]                           # salas reconstruidas, no las mismas
    assert partida2.semilla == partida.semilla
    assert instantanea_conocimiento(salas2, partida2) == original
    assert partida2.jugador.sala is salas2[3]
    assert partida2.reloj == partida.reloj
    # y lo que se vuelve a guardar tras cargar es la misma lista de comandos
    assert GuardadoBinario().leer_comandos(tmp_path / "saves" / "copia.sav") == comandos
