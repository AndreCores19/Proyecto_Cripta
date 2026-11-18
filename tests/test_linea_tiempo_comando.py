"""El comando `historia` y sus DTO (spec 005, Fase 6, US1 y US2).

`historia <t>` y `historia #<k>` pasan por `Controlador.ejecutar`, el servicio devuelve un
`RespuestaHistoriaDTO` y la vista imprime las líneas de `adapters/formato_historia.py`. La consulta
no deja rastro: ni en la bitácora, ni en los comandos guardados, ni en el deshacer, ni en el juego vivo.
Todo con datos falsos y sin red.
"""
import pytest

import adapters.salida_replay as salida_replay
from adapters.bitacora_partida import BitacoraPartida
from adapters.formato_historia import lineas_historia, lineas_mapa
from controller.controlador import Controlador
from dto.estado_vista_dto import EnemigoVistaDTO, JugadorVistaDTO
from dto.inventario_vista_dto import ObjetoInventarioDTO
from dto.mapa_vista_dto import MapaVistaDTO
from dto.resumen_historia_dto import RespuestaHistoriaDTO, ResumenHistoriaDTO
from linea_tiempo_apoyo import armar_mundo, jugar_semilla, resumen_plano
from model.linea_tiempo_logica import LineaTiempoPartida
from service.juego_service import JuegoService
from view.vista_consola import VistaConsola
from view.vista_silenciosa import VistaSilenciosa

MUNDO = dict(salas=7, enemigos=5, cazadores=2)
CAMPOS_RESUMEN = {"reloj", "id_sala", "nombre_sala", "jugador", "inventario", "enemigos", "mapa"}


def _armar(semilla=3, k=3, vida=5000, con_linea=True, **mundo):
    parametros = dict(MUNDO)
    parametros.update(mundo)
    m = armar_mundo(semilla, vida_jugador=vida, **parametros)
    if not con_linea:
        return m, JuegoService(m.partida, m.fabrica)
    linea = LineaTiempoPartida()
    linea.iniciar(m.partida, m.constructor, k)
    return m, JuegoService(m.partida, m.fabrica, linea_tiempo=linea)


class VistaGrabadora(VistaSilenciosa):
    """Anota lo que el controlador le pide mostrar."""

    def __init__(self):
        self.historias = []
        self.mensajes = []

    def mostrar_historia(self, resumen):
        self.historias.append(resumen)

    def mostrar_mensaje(self, texto):
        self.mensajes.append(texto)


class PersistenciaFalsa:
    def __init__(self):
        self.guardados = []

    def guardar_partida(self, semilla, comandos, nombre):
        self.guardados.append((semilla, list(comandos), nombre))
        return f"saves/{nombre}.sav"


def _huella(partida):
    """Todo lo que una consulta no puede tocar del juego vivo."""
    agenda = tuple((e.tiempo, e.num_sec, e.tipo) for e in partida.agenda.heap)
    return (partida.reloj, partida.acciones_jugador, partida.retrocesos, partida.terminada,
            resumen_plano(partida), agenda, partida.agenda.num_sec, partida.azar.getstate(),
            len(partida.historial))


def _jugado(n=40, **kwargs):
    m, servicio = _armar(**kwargs)
    jugar_semilla(servicio, 5, n)
    return m, servicio


# ---------------------------------------------------------------- parte 1: los DTO (FR-004, FR-029)

def test_historia_por_instante_y_por_accion_devuelven_el_dto_con_exactamente_sus_campos():
    """FR-004, FR-029 · US1-1, US1-2 · `RespuestaHistoriaDTO` con un `ResumenHistoriaDTO` de campos
    reloj, id_sala, nombre_sala, jugador, inventario, enemigos y mapa, hechos con las clases de la vista"""
    _, servicio = _jugado(40)
    p = servicio.partida
    t = p.reloj // 2
    for r in (servicio.historia_por_instante(t), servicio.historia_por_accion(5)):
        assert isinstance(r, RespuestaHistoriaDTO)
        assert (r.aceptada, r.motivo, r.termino_antes, r.reloj_final) == (True, None, False, None)
        resumen = r.resumen
        assert isinstance(resumen, ResumenHistoriaDTO)
        assert set(vars(resumen)) == CAMPOS_RESUMEN
        assert isinstance(resumen.jugador, JugadorVistaDTO)
        assert all(isinstance(o, ObjetoInventarioDTO) for o in resumen.inventario)
        assert all(isinstance(e, EnemigoVistaDTO) for e in resumen.enemigos)
        assert isinstance(resumen.mapa, MapaVistaDTO)
        assert resumen.mapa.id_sala_actual == resumen.id_sala
        assert isinstance(resumen.nombre_sala, str) and resumen.nombre_sala
    assert servicio.historia_por_instante(t).resumen.reloj == t          #el instante pedido
    assert servicio.historia_por_accion(5).resumen.reloj == servicio.linea_tiempo.relojes[4]  #la decisión


def test_el_resumen_del_instante_actual_es_el_estado_vivo():
    """FR-004 · US1-1 · `historia <reloj>` muestra lo mismo que la partida viva, campo por campo"""
    _, servicio = _jugado(40)
    p = servicio.partida
    resumen = servicio.historia_por_instante(p.reloj).resumen
    assert resumen_plano(resumen) == resumen_plano(p)
    assert resumen.nombre_sala == p.jugador.sala.nombre
    assert resumen.jugador.nombre == p.jugador.nombre


def test_las_consultas_rechazadas_devuelven_el_dto_sin_resumen():
    """FR-005, FR-029 · US1-3, US1-8 · rechazos con su motivo y sin resumen"""
    _, servicio = _jugado(20)
    p = servicio.partida
    casos = ((servicio.historia_por_instante(p.reloj + 1), "despues_del_reloj"),
             (servicio.historia_por_accion(p.acciones_jugador + 1), "accion_inexistente"),
             (servicio.historia_por_instante(-1), "argumento_invalido"),
             (servicio.historia_por_accion(0), "argumento_invalido"))
    for r, motivo in casos:
        assert isinstance(r, RespuestaHistoriaDTO)
        assert (r.aceptada, r.motivo, r.resumen) == (False, motivo, None)


def test_el_dto_no_importa_nada_de_model():
    """FR-029 · los DTO de la historia son clases simples, sin dependencias de model/"""
    import dto.resumen_historia_dto as modulo
    with open(modulo.__file__, encoding="utf-8") as f:
        texto = f.read()
    importados = [linea.split()[1].split(".")[0] for linea in texto.splitlines()
                  if linea.startswith(("import ", "from "))]
    assert "model" not in importados


# ---------------------------------------------------------------- parte 2: el comando (FR-005, US1-8)

@pytest.mark.parametrize("texto", ["historia", "historia abc", "historia -3", "historia #0",
                                   "historia #x", "historia 1.5", "historia 3 4", "historia #",
                                   "historia #-2", "historia +4", "historia # 3"])
def test_formas_mal_escritas_se_rechazan_con_las_formas_aceptadas_y_nada_cambia(texto):
    """FR-005 · US1-8 · sin argumento, no numérico, negativo, `#0`, `#x`, decimal o de más: mensaje con
    las formas aceptadas; no se muestra ningún resumen y el juego no cambia"""
    _, servicio = _jugado(20)
    vista = VistaGrabadora()
    controlador = Controlador(servicio, vista, None, None)
    antes = _huella(servicio.partida)
    controlador.ejecutar(texto)
    assert vista.historias == []
    assert len(vista.mensajes) == 1
    assert "historia <instante>" in vista.mensajes[0] and "historia #<acción>" in vista.mensajes[0]
    assert _huella(servicio.partida) == antes
    assert controlador.comandos == []


def test_un_instante_posterior_al_reloj_y_una_accion_inexistente_se_rechazan_con_su_motivo():
    """FR-005, FR-003 · US1-3 · `historia t` con t > reloj y `historia #k` más allá de las acciones"""
    _, servicio = _jugado(20)
    p = servicio.partida
    vista = VistaGrabadora()
    controlador = Controlador(servicio, vista, None, None)
    antes = _huella(p)
    controlador.ejecutar(f"historia {p.reloj + 1}")
    controlador.ejecutar(f"historia #{p.acciones_jugador + 1}")
    assert vista.historias == []
    assert "todavía no ha ocurrido" in vista.mensajes[0]
    assert "no existe" in vista.mensajes[1]
    assert _huella(p) == antes


def test_las_consultas_aceptadas_se_muestran_por_mostrar_historia():
    """FR-004, FR-005 · US1-1, US1-2 · `historia <t>` y `historia #<k>` llegan a la vista como resumen"""
    _, servicio = _jugado(30)
    p = servicio.partida
    vista = VistaGrabadora()
    controlador = Controlador(servicio, vista, None, None)
    controlador.ejecutar("historia 0")
    controlador.ejecutar(f"historia {p.reloj}")
    controlador.ejecutar("historia #3")
    controlador.ejecutar("HISTORIA   #3")                               #como los demás comandos
    assert vista.mensajes == []
    assert [type(r) for r in vista.historias] == [ResumenHistoriaDTO] * 4
    assert [r.reloj for r in vista.historias] == [0, p.reloj, servicio.linea_tiempo.relojes[2],
                                                 servicio.linea_tiempo.relojes[2]]
    assert resumen_plano(vista.historias[1]) == resumen_plano(p)
    assert resumen_plano(vista.historias[2]) == resumen_plano(servicio.historia_por_accion(3).resumen)


def test_sin_vista_el_comando_no_falla():
    """FR-016 · con vista=None (--replay) `historia` no imprime nada ni rompe la ejecución"""
    _, servicio = _jugado(20)
    avisos = []
    controlador = Controlador(servicio, None, None, None, avisar=avisos.append)
    antes = _huella(servicio.partida)
    controlador.ejecutar("historia 5")
    controlador.ejecutar("historia zz")
    assert len(avisos) == 1 and "historia <instante>" in avisos[0]
    assert _huella(servicio.partida) == antes


# ---------------------------------------------------------------- parte 3: bitácora y comandos guardados (FR-007, FR-017)

def _comandos_de_prueba():
    _, servicio = _armar()
    return jugar_semilla(servicio, 9, 50)


def _jugar_con_bitacora(carpeta, comandos, con_consultas):
    m, servicio = _armar()
    bitacora = BitacoraPartida(carpeta)
    bitacora.abrir("prueba", "1", "1", m.semilla)
    persistencia = PersistenciaFalsa()
    controlador = Controlador(servicio, VistaGrabadora(), bitacora, persistencia)
    for i, comando in enumerate(comandos):
        if servicio.terminada():
            break
        if con_consultas:
            p = servicio.partida
            controlador.ejecutar(f"historia {p.reloj // 2}")                 #aceptada
            controlador.ejecutar(f"historia {p.reloj + 10}")                 #rechazada
            controlador.ejecutar(f"historia #{max(1, p.acciones_jugador)}")  #aceptada (o rechazada al inicio)
            controlador.ejecutar("historia #x")                              #rechazada
        controlador.ejecutar(comando)
        if i == 20:
            if con_consultas:
                controlador.ejecutar("historia 0")
            controlador.ejecutar("guardar prueba")                           #justo después de una consulta
    bitacora.cerrar()
    return controlador, persistencia, servicio


def test_la_consulta_no_queda_en_la_bitacora_ni_en_los_comandos_guardados(tmp_path):
    """FR-007, FR-017 · US2-2, US2-4 · con consultas aceptadas y rechazadas intercaladas, `partida.log` es
    byte a byte el del mismo juego sin ellas, `comandos` no tiene `historia` y `guardar` justo después de una
    consulta escribe los mismos comandos"""
    comandos = _comandos_de_prueba()
    sin, guardado_sin, servicio_sin = _jugar_con_bitacora(tmp_path / "sin", comandos, False)
    con, guardado_con, servicio_con = _jugar_con_bitacora(tmp_path / "con", comandos, True)
    log_sin = (tmp_path / "sin").glob("*.log").__next__().read_bytes()
    log_con = (tmp_path / "con").glob("*.log").__next__().read_bytes()
    assert log_con == log_sin
    assert b"historia" not in log_con
    assert con.comandos == sin.comandos
    assert not any(c.startswith("historia") for c in con.comandos)
    assert guardado_con.guardados == guardado_sin.guardados and len(guardado_con.guardados) == 1
    assert _huella(servicio_con.partida) == _huella(servicio_sin.partida)


# ---------------------------------------------------------------- parte 4: deshacer y juego vivo intactos (FR-006, FR-008)

def _dar_pergaminos(m, cantidad):
    inv = m.partida.jugador.inventario
    inv.capacidad_max += cantidad
    for _ in range(cantidad):
        inv.agregar(m.fabrica.objeto_desde_id("perg"))


def _traza_de_retrocesos(controlador, servicio, con_consultas):
    traza = []
    while True:
        if con_consultas:
            controlador.ejecutar(f"historia {servicio.partida.reloj}")
            controlador.ejecutar("historia #1")
        retrocesos = servicio.partida.retrocesos
        controlador.ejecutar("retroceder")
        if servicio.partida.retrocesos == retrocesos:
            break
        p = servicio.partida
        traza.append((p.acciones_jugador, p.reloj, resumen_plano(p)))
    return traza


def test_tras_las_consultas_el_pergamino_revierte_las_mismas_acciones_en_el_mismo_orden():
    """FR-006, FR-008 · US2-3, US2-4 · con `historia` por el controlador (aceptadas y rechazadas) el estado,
    el reloj y la agenda no cambian, y el pergamino revierte lo mismo que sin consultas"""
    comandos = _comandos_de_prueba()
    trazas = []
    for con_consultas in (False, True):
        m, servicio = _armar()
        controlador = Controlador(servicio, VistaGrabadora(), None, None)
        for comando in comandos:
            if servicio.terminada():
                break
            if con_consultas:
                antes = _huella(servicio.partida)
                for texto in ("historia 0", f"historia {servicio.partida.reloj + 3}", "historia #1",
                              f"historia #{servicio.partida.acciones_jugador + 1}", "historia ?"):
                    controlador.ejecutar(texto)
                assert _huella(servicio.partida) == antes, comando
            controlador.ejecutar(comando)
        _dar_pergaminos(m, 3)
        trazas.append((_traza_de_retrocesos(controlador, servicio, con_consultas), _huella(servicio.partida)))
    assert len(trazas[0][0]) >= 3
    assert trazas[0] == trazas[1]


# ---------------------------------------------------------------- parte 5: el mismo texto (FR-004, FR-014)

def _resumen_de_ejemplo():
    _, servicio = _jugado(60, salas=5, enemigos=6, cazadores=1)
    p = servicio.partida
    #un instante con inventario y, si lo hay, con enemigos en la sala
    mejor = None
    for t in range(0, p.reloj + 1, 37):
        resumen = servicio.historia_por_instante(t).resumen
        puntos = (len(resumen.inventario) > 0) + (len(resumen.enemigos) > 0)
        if mejor is None or puntos > mejor[0]:
            mejor = (puntos, resumen)
    return mejor[1]


def test_la_vista_de_consola_imprime_las_lineas_del_formato(capsys):
    """FR-004, FR-014 · `VistaConsola.mostrar_historia` imprime exactamente `lineas_historia`"""
    resumen = _resumen_de_ejemplo()
    VistaConsola().mostrar_historia(resumen)
    assert capsys.readouterr().out == "".join(linea + "\n" for linea in lineas_historia(resumen))


def test_la_salida_de_replay_imprime_las_mismas_lineas_que_la_vista(capsys):
    """FR-014 · US4-1 · `salida_replay.imprimir_historia` y `VistaConsola.mostrar_historia` dan el mismo texto
    para la misma respuesta (las dos usan adapters/formato_historia.py)"""
    if not hasattr(salida_replay, "imprimir_historia"):
        pytest.skip("salida_replay.imprimir_historia llega con T050 (Fase 7)")
    resumen = _resumen_de_ejemplo()
    VistaConsola().mostrar_historia(resumen)
    de_la_vista = capsys.readouterr().out
    salida_replay.imprimir_historia(RespuestaHistoriaDTO(True, None, resumen))
    assert capsys.readouterr().out == de_la_vista


def test_el_texto_tiene_reloj_sala_vida_efectos_inventario_enemigos_y_mapa():
    """FR-004, FR-014 · el texto tiene el reloj, la sala, vida y estadísticas, efectos, el inventario con lo
    equipado marcado, los enemigos con vida/vida_max y el mapa con el formato del comando `mapa`"""
    jugador = JugadorVistaDTO("Ana", 30, 40, 9, 2, 100, "Espada", None, ["veneno", "velocidad"])
    inventario = [ObjetoInventarioDTO(4, "Espada", 5, 30, True, False),
                  ObjetoInventarioDTO(7, "Poción de vida", 1, 10, False, True)]
    enemigos = [EnemigoVistaDTO("Lobo", "c1", 12, 25, ["veneno"], True),
                EnemigoVistaDTO("Rata", "e2", 5, 12, [], False)]
    _, servicio = _jugado(30)
    mapa = servicio.mapa_vista()
    resumen = ResumenHistoriaDTO(812, mapa.id_sala_actual, "Sala de prueba", jugador, inventario, enemigos, mapa)
    lineas = lineas_historia(resumen)
    texto = "\n".join(lineas)
    assert "812" in lineas[1]
    assert f"Sala {mapa.id_sala_actual}: Sala de prueba" in texto
    assert "Vida: 30/40" in texto and "Ataque: 9" in texto and "Defensa: 2" in texto and "Velocidad: 100" in texto
    assert "Arma: Espada" in texto and "Armadura: ninguna" in texto
    assert "Efectos: veneno, velocidad" in texto
    assert "  [4] Espada (equipado)" in lineas and "  [7] Poción de vida" in lineas
    assert "  Lobo (cazador) [c1] (Vida: 12/25) [veneno]" in lineas
    assert "  Rata [e2] (Vida: 5/12)" in lineas
    inicio = lineas.index("Mapa conocido:")
    assert lineas[inicio:inicio + len(lineas_mapa(mapa))] == lineas_mapa(mapa)


def test_el_mapa_del_resumen_tiene_el_formato_del_comando_mapa(capsys):
    """FR-004, FR-014 · las líneas del mapa del resumen son las que imprime el comando `mapa`"""
    _, servicio = _jugado(30)
    mapa = servicio.mapa_vista()
    VistaConsola().mostrar_mapa(mapa)
    assert capsys.readouterr().out == "".join(linea + "\n" for linea in lineas_mapa(mapa))


def test_la_vista_silenciosa_no_imprime_nada(capsys):
    """FR-004 · la vista silenciosa también acepta `mostrar_historia` y no imprime nada"""
    VistaSilenciosa().mostrar_historia(_resumen_de_ejemplo())
    assert capsys.readouterr().out == ""


def test_el_formato_no_importa_model_ni_view():
    """FR-014, FR-029 · adapters/formato_historia.py es puro: sin model/ ni view/, sin print"""
    import adapters.formato_historia as modulo
    with open(modulo.__file__, encoding="utf-8") as f:
        texto = f.read()
    for prohibido in ("from model", "import model", "from view", "import view", "print("):
        assert prohibido not in texto
