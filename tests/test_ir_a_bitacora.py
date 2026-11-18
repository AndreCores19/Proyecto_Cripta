from adapters.bitacora_partida import BitacoraPartida
from adapters.lector_bitacora import LectorBitacora
from controller.controlador import Controlador
from tests.mapas_cazador import cadena
from tests.mapas_niebla import partida_en, servicio_en
from tests.test_niebla_retroceso import instantanea_conocimiento
from view.vista_silenciosa import VistaSilenciosa


class VistaDeMensajes(VistaSilenciosa):
    def __init__(self):
        self.mensajes = []

    def mostrar_mensaje(self, texto):
        self.mensajes.append(texto)


def _juego(carpeta, vista=None, costos=(100, 100, 100)):
    salas, pares = cadena(list(costos))
    partida = partida_en(salas, salas[0])
    bitacora = None
    if carpeta is not None:
        bitacora = BitacoraPartida(carpeta)
        bitacora.abrir("cripta-prueba", "v1", "v1", 1)
    controlador = Controlador(servicio_en(partida), vista or VistaSilenciosa(), bitacora, None)
    return salas, pares, partida, controlador


def _recorrer(controlador, largo=3):
    for _ in range(largo):
        controlador.ejecutar("d")
    for _ in range(largo):
        controlador.ejecutar("a")


def _cuerpo(ruta):
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    return lineas[lineas.index("---") + 1:]


def test_un_viaje_escribe_el_comentario_y_cada_paso_como_movimiento(tmp_path):
    """FR-016, FR-024 · US6-8"""
    salas, _, partida, controlador = _juego(tmp_path)
    _recorrer(controlador)
    controlador.bitacora.cerrar()
    controlador.bitacora.abrir("cripta-prueba", "v1", "v1", 2)         # un log limpio para el viaje
    controlador.comandos.clear()
    controlador.ejecutar("ir a 4")
    controlador.bitacora.cerrar()
    assert partida.jugador.sala is salas[3]
    assert _cuerpo(tmp_path / "partida_cripta-prueba_2.log") == ["# ir a 4", "d", "d", "d"]
    assert controlador.comandos == ["d", "d", "d"]


def test_una_orden_rechazada_deja_solo_el_comentario(tmp_path):
    """FR-016, FR-024 · US6-9"""
    vista = VistaDeMensajes()
    salas, _, partida, controlador = _juego(tmp_path, vista)
    reloj = partida.reloj
    controlador.ejecutar("ir a 3")                  # la sala 3 aún no está explorada
    controlador.bitacora.cerrar()
    assert _cuerpo(tmp_path / "partida_cripta-prueba_1.log") == ["# ir a 3"]
    assert controlador.comandos == []
    assert partida.reloj == reloj
    assert vista.mensajes == ["Esa sala no está explorada."]


def test_mensaje_de_parada_con_el_motivo(tmp_path):
    """FR-016, FR-023 · el motivo se muestra con una línea"""
    vista = VistaDeMensajes()
    salas, _, partida, controlador = _juego(tmp_path, vista)
    _recorrer(controlador)
    controlador.ejecutar("ir a 3")
    assert vista.mensajes == ["Viaje detenido: llegaste a tu destino"]


def test_uso_incorrecto_de_ir(tmp_path):
    """FR-016 · `ir` sin `a` o sin id muestra el uso y no escribe nada en el log"""
    vista = VistaDeMensajes()
    salas, _, partida, controlador = _juego(tmp_path, vista)
    for texto in ("ir", "ir a", "ir 3"):
        controlador.ejecutar(texto)
    assert vista.mensajes == ["Uso: ir a <id>"] * 3
    controlador.bitacora.cerrar()
    assert _cuerpo(tmp_path / "partida_cripta-prueba_1.log") == []
    assert controlador.comandos == []


def test_el_lector_omite_los_comentarios_y_un_log_viejo_se_lee_igual(tmp_path):
    """FR-024 · el lector solo devuelve movimientos"""
    ruta = tmp_path / "con.log"
    cabecera = "CRIPTA-LOG 1\ncripta: c\nversion_cripta: v1\nversion_catalogo: v1\nsemilla: 1\n---\n"
    ruta.write_text(cabecera + "d\n# ir a 3\nd\nd\n# ir a 1\n", encoding="utf-8")
    lector = LectorBitacora(ruta)
    lector.leer()
    assert lector.comandos == ["d", "d", "d"]
    viejo = tmp_path / "viejo.log"
    viejo.write_text(cabecera + "d\nesperar\na\n", encoding="utf-8")
    lector = LectorBitacora(viejo)
    lector.leer()
    assert lector.comandos == ["d", "esperar", "a"]


def test_viaje_detenido_por_sin_ruta_tras_un_paso_escribe_una_sola_linea_de_movimiento(tmp_path):
    """FR-020, FR-024 · los movimientos se escriben solo por los pasos dados"""
    vista = VistaDeMensajes()
    salas, pares, partida, controlador = _juego(tmp_path, vista)
    _recorrer(controlador)
    controlador.bitacora.cerrar()
    controlador.bitacora.abrir("cripta-prueba", "v1", "v1", 2)
    controlador.comandos.clear()
    partida._poner_cerrada(pares[1][0], True)       # se cierra sin que el jugador lo vea
    controlador.ejecutar("ir a 3")
    controlador.bitacora.cerrar()
    assert partida.jugador.sala is salas[1]
    assert _cuerpo(tmp_path / "partida_cripta-prueba_2.log") == ["# ir a 3", "d"]
    assert controlador.comandos == ["d"]
    assert vista.mensajes[-1] == "Viaje detenido: no hay ruta conocida"


def test_repetir_los_movimientos_del_log_llega_al_mismo_estado(tmp_path):
    """FR-016, FR-024 · replay de los movimientos de un viaje"""
    salas, _, partida, controlador = _juego(tmp_path)
    _recorrer(controlador)
    controlador.ejecutar("ir a 4")
    controlador.bitacora.cerrar()
    lector = LectorBitacora(tmp_path / "partida_cripta-prueba_1.log")
    lector.leer()
    assert "ir a 4" not in lector.comandos
    salas2, _, partida2, controlador2 = _juego(None)
    for comando in lector.comandos:
        controlador2.ejecutar(comando)
    final = controlador.servicio.resumen_final()
    final2 = controlador2.servicio.resumen_final()
    assert vars(final) == vars(final2)
    assert instantanea_conocimiento(salas2, partida2) == instantanea_conocimiento(salas, partida)
