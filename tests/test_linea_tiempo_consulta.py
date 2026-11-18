"""La consulta del historial por instante y por número de acción (spec 005, Fase 4, US1 y US2).

Todo con datos falsos y sin red. Lo que se compara con la consulta es siempre lo que el juego vivo
mostró (capturado antes de cada acción) o lo que mostró un segundo juego vivo, instrumentado, que
no usa ningún código de la línea de tiempo (ver `linea_tiempo_apoyo.PartidaInstrumentada`).
"""
import pytest

from controller.controlador import Controlador
from linea_tiempo_apoyo import (PartidaInstrumentada, VistaMuda, armar_mundo, con_reloj,
                                ejecutar_comandos, instantes_clave, jugar_semilla, oraculo,
                                registrar_vivo, resumen_plano)
from model.linea_tiempo_logica import LineaTiempoPartida
from model.partida_logica import Partida
from model.registro_estado import restaurar
from service.juego_service import JuegoService

MUNDO = dict(salas=7, enemigos=5, cazadores=2)


def _armar(semilla=3, k=3, clase=Partida, vida=5000, con_linea=True, **mundo):
    """(mundo, servicio, linea). Sin `con_linea` el servicio no lleva línea de tiempo (segundo juego vivo)."""
    parametros = dict(MUNDO)
    parametros.update(mundo)
    m = armar_mundo(semilla, clase_partida=clase, vida_jugador=vida, **parametros)
    if not con_linea:
        return m, JuegoService(m.partida, m.fabrica), None
    linea = LineaTiempoPartida()
    linea.iniciar(m.partida, m.constructor, k)
    return m, JuegoService(m.partida, m.fabrica, linea_tiempo=linea), linea


def _consultar(servicio):
    def consultar(modo, valor):
        r = (servicio.historia_por_instante(valor) if modo == "t"
             else servicio.historia_por_accion(valor))
        assert r.aceptada, f"{modo} {valor} rechazada: {r.motivo}"
        return con_reloj(resumen_plano(r.partida), r.reloj)
    return consultar


def _ejecutar_con_vivos(servicio, comandos):
    """Ejecuta los comandos anotando la decisión antes de cada uno y una vez al final."""
    controlador = Controlador(servicio, VistaMuda(), None, None)
    vivos = []
    for comando in comandos:
        if servicio.terminada():
            break
        registrar_vivo(vivos, servicio)
        controlador.ejecutar(comando)
    registrar_vivo(vivos, servicio)
    return vivos


def _juego(k, semilla_mundo=3, semilla_juego=5, n=60, vida=5000, comandos=None, **mundo):
    """Juega con la línea de tiempo y repite los mismos comandos en un segundo juego instrumentado.

    Devuelve (servicio, vivos, instantaneas, comandos)."""
    m, servicio, _ = _armar(semilla_mundo, k, vida=vida, **mundo)
    vivos = []
    if comandos is None:
        comandos = jugar_semilla(servicio, semilla_juego, n, vivos=vivos)
    else:
        vivos = _ejecutar_con_vivos(servicio, comandos)
    m2, servicio2, _ = _armar(semilla_mundo, k, clase=PartidaInstrumentada, vida=vida,
                              con_linea=False, **mundo)
    ejecutar_comandos(servicio2, comandos)
    assert resumen_plano(m2.partida) == resumen_plano(m.partida)      #los dos juegos fueron el mismo
    return servicio, vivos, m2.partida.instantaneas, comandos


def _huella(partida):
    """Todo lo que una consulta no puede tocar del juego vivo."""
    agenda = tuple((e.tiempo, e.num_sec, e.tipo) for e in partida.agenda.heap)
    return (partida.reloj, partida.acciones_jugador, partida.retrocesos, partida.terminada,
            resumen_plano(partida), agenda, partida.agenda.num_sec, partida.azar.getstate(),
            len(partida.historial))


def _ultima_foto(instantaneas, t):
    ultima = None
    for foto in instantaneas:
        if foto[0] <= t:
            ultima = foto
    return ultima


# ---------------------------------------------------------------- US1 (FR-001..FR-005)

def test_cada_instante_da_el_estado_despues_de_todos_los_eventos_con_tiempo_menor_o_igual():
    """FR-001, FR-002, FR-004 · US1-1 · cada t de 0 al reloj da lo que mostró el juego vivo"""
    servicio, vivos, instantaneas, _ = _juego(3, n=18)
    p = servicio.partida
    assert p.reloj > 500 and p.acciones_jugador >= 12
    oraculo(servicio, vivos, instantaneas, _consultar(servicio))      #todos los instantes y todos los #k


def test_historia_por_accion_da_el_estado_justo_antes_de_esa_accion():
    """FR-003, FR-004 · US1-2 · `#k` da lo capturado antes de la acción k, con el reloj de su decisión"""
    servicio, vivos, _, _ = _juego(3, n=60)
    consultar = _consultar(servicio)
    revisadas = 0
    for numero, reloj, esperado in vivos:
        if numero > servicio.partida.acciones_jugador:
            continue
        r = servicio.historia_por_accion(numero)
        assert r.aceptada and r.motivo is None
        assert r.reloj == reloj                                      #el reloj de la decisión
        assert consultar("#", numero) == esperado, f"#{numero}"
        revisadas += 1
    assert revisadas == servicio.partida.acciones_jugador >= 40


@pytest.mark.parametrize("despues", [1, 2, 1000])
def test_un_instante_posterior_al_reloj_se_rechaza_y_no_cambia_nada(despues):
    """FR-005 · US1-3 · `t` mayor que el reloj: motivo `despues_del_reloj`, sin estado, nada cambia"""
    servicio, _, _, _ = _juego(3, n=30)
    p = servicio.partida
    antes = _huella(p)
    r = servicio.historia_por_instante(p.reloj + despues)
    assert (r.aceptada, r.motivo, r.partida) == (False, "despues_del_reloj", None)
    assert _huella(p) == antes


def test_varios_eventos_en_el_mismo_instante_se_ven_todos():
    """FR-001 · US1-4 · sin decisión del jugador en t, el estado en t incluye todos los eventos de t"""
    servicio, vivos, instantaneas, _ = _juego(3, n=120, semilla_juego=5)
    decisiones = {r for _, r, _ in vivos}
    cuentas = {}
    for reloj, _, _ in instantaneas:
        cuentas[reloj] = cuentas.get(reloj, 0) + 1
    candidatos = [t for t in sorted(cuentas) if cuentas[t] >= 2 and t not in decisiones]
    assert candidatos, "el juego de prueba debe tener un instante con dos eventos y sin decisión"
    consultar = _consultar(servicio)
    distintos = 0
    for t in candidatos:
        todas = [f for f in instantaneas if f[0] == t]
        assert consultar("t", t) == con_reloj(todas[-1][1], t)       #con todos los eventos de t
        if todas[0][1][1:] != todas[-1][1][1:]:
            distintos += 1                                           #y se distingue del estado tras el primero
    assert distintos >= 1


def test_con_decision_del_jugador_en_t_gana_la_decision():
    """FR-001, FR-009 · US1-5, US1-9 · el estado en t es el de justo antes de la decisión: no se ven
    los eventos de t que van después de ella en el orden de la agenda"""
    servicio, vivos, instantaneas, _ = _juego(3, n=200, semilla_juego=5)
    consultar = _consultar(servicio)
    con_eventos_despues = 0
    for numero, reloj, esperado in vivos:
        if numero > servicio.partida.acciones_jugador:
            continue
        assert consultar("t", reloj) == esperado, f"t={reloj} (decisión {numero})"
        #eventos de ese mismo instante que corrieron DESPUÉS de la acción: la foto de la acción y alguna más
        despues = [f for f in instantaneas if f[0] == reloj and f[2] == numero]
        if len(despues) >= 2:
            con_eventos_despues += 1
            assert consultar("t", reloj) != con_reloj(despues[-1][1], reloj)
    assert con_eventos_despues >= 1, "el juego de prueba debe tener una decisión con eventos después en t"


def test_el_resumen_tiene_los_campos_y_el_mapa_no_muestra_lo_desconocido():
    """FR-004 · US1-6 · una sala vista por primera vez en el reloj c no aparece en el mapa de t < c"""
    servicio, vivos, _, _ = _juego(3, n=60)
    consultar = _consultar(servicio)
    comprobada = False
    for i in range(len(vivos) - 1):
        _, reloj, plano = vivos[i]
        _, reloj_sig, plano_sig = vivos[i + 1]
        ids = {s[0] for s in plano[5][1]}
        ids_sig = {s[0] for s in plano_sig[5][1]}
        if ids_sig - ids and reloj_sig > reloj + 1:
            nueva = next(iter(ids_sig - ids))
            assert nueva not in {s[0] for s in consultar("t", reloj)[5][1]}
            for t in range(reloj + 1, reloj_sig + 1):               #desde que se hace el movimiento
                assert nueva in {s[0] for s in consultar("t", t)[5][1]}, t
            comprobada = True
            break
    assert comprobada
    resumen = servicio.historia_por_instante(servicio.partida.reloj).partida
    #los campos del FR-004: reloj, sala, vida y estadísticas, equipo, inventario, efectos, enemigos y mapa
    plano = resumen_plano(resumen)
    assert len(plano) == 6
    reloj, id_sala, jugador, inventario, enemigos, mapa = plano
    assert (reloj, id_sala) == (resumen.reloj, resumen.jugador.sala.id)
    assert jugador[:2] == (resumen.jugador.vida, resumen.jugador.vida_max)
    assert mapa[0] == id_sala


def test_el_instante_cero_es_el_estado_inicial():
    """FR-002, FR-004 · US1-7 · `historia 0` es el estado de antes de toda acción"""
    m, servicio, _ = _armar(3, 3)
    inicial = resumen_plano(m.partida)
    jugar_semilla(servicio, 5, 40)
    r = servicio.historia_por_instante(0)
    assert r.aceptada and r.reloj == 0
    assert con_reloj(resumen_plano(r.partida), 0) == con_reloj(inicial, 0)
    assert resumen_plano(servicio.historia_por_accion(1).partida) == inicial


@pytest.mark.parametrize("argumento", ["abc", "-3", -3, -1, 1.5, "1.5", None, True, "", "#2", [1]])
def test_instantes_mal_formados_se_rechazan_con_argumento_invalido(argumento):
    """FR-005 · US1-8 · malformado, negativo o faltante: `argumento_invalido` y nada cambia"""
    servicio, _, _, _ = _juego(3, n=20)
    antes = _huella(servicio.partida)
    r = servicio.historia_por_instante(argumento)
    assert (r.aceptada, r.motivo, r.partida) == (False, "argumento_invalido", None)
    assert _huella(servicio.partida) == antes


@pytest.mark.parametrize("argumento", ["x", 0, -2, 1.5, None, False, "", [3]])
def test_numeros_de_accion_mal_formados_se_rechazan_con_argumento_invalido(argumento):
    """FR-005 · US1-8 · `#0`, `#x`, `#-2`, `#` sin número: `argumento_invalido` y nada cambia"""
    servicio, _, _, _ = _juego(3, n=20)
    antes = _huella(servicio.partida)
    r = servicio.historia_por_accion(argumento)
    assert (r.aceptada, r.motivo, r.partida) == (False, "argumento_invalido", None)
    assert _huella(servicio.partida) == antes


# ---------------------------------------------------------------- casos de borde (FR-002, FR-003, FR-005, FR-019, FR-020)

def test_el_instante_igual_al_reloj_es_el_estado_vivo_y_k_mas_uno_no_existe():
    """FR-002, FR-003, FR-005 · `t` igual al reloj se acepta y es el estado vivo; `#(acciones+1)` se rechaza"""
    servicio, _, _, _ = _juego(3, n=40)
    p = servicio.partida
    r = servicio.historia_por_instante(p.reloj)
    assert r.aceptada and r.reloj == p.reloj
    assert resumen_plano(r.partida) == resumen_plano(p)
    r = servicio.historia_por_accion(p.acciones_jugador + 1)
    assert (r.aceptada, r.motivo, r.partida) == (False, "accion_inexistente", None)
    r = servicio.historia_por_accion(p.acciones_jugador + 500)
    assert (r.aceptada, r.motivo) == (False, "accion_inexistente")
    assert servicio.historia_por_accion(p.acciones_jugador).aceptada


def test_un_juego_sin_acciones_solo_tiene_el_instante_cero():
    """FR-002, FR-003, FR-005 · sin acciones: solo `t=0`; `#1` no existe y `t=1` es posterior al reloj"""
    m, servicio, _ = _armar(3, 3)
    assert servicio.partida.acciones_jugador == 0 and servicio.partida.reloj == 0
    r = servicio.historia_por_instante(0)
    assert r.aceptada and resumen_plano(r.partida) == resumen_plano(m.partida)
    assert servicio.historia_por_instante(1).motivo == "despues_del_reloj"
    assert servicio.historia_por_accion(1).motivo == "accion_inexistente"


def test_un_juego_terminado_acepta_todos_los_instantes_hasta_el_final():
    """FR-002, FR-005 · una partida que terminó (muerte) responde cada instante hasta su último reloj"""
    comandos = ["w"] + ["esperar"] * 300
    servicio, vivos, instantaneas, _ = _juego(3, vida=4, comandos=comandos, enemigos=0, cazadores=0)
    p = servicio.partida
    assert p.terminada and not p.victoria
    oraculo(servicio, vivos, instantaneas, _consultar(servicio))
    assert servicio.historia_por_instante(p.reloj).aceptada
    assert servicio.historia_por_instante(p.reloj + 1).motivo == "despues_del_reloj"


def test_k_uno_y_k_mayor_que_el_juego_dan_las_mismas_respuestas():
    """FR-019, FR-020 · el K solo cambia cuántas acciones se reproducen, no la respuesta"""
    k1, _, _, comandos = _juego(1, n=50)
    kg, _, _, _ = _juego(1000, comandos=comandos)
    k7, _, _, _ = _juego(7, comandos=comandos)
    reloj = k1.partida.reloj
    assert kg.partida.reloj == k7.partida.reloj == reloj
    a, b, c = _consultar(k1), _consultar(kg), _consultar(k7)
    for t in range(0, reloj + 1, 13):
        assert a("t", t) == b("t", t) == c("t", t), t
    for numero in range(1, k1.partida.acciones_jugador + 1):
        assert a("#", numero) == b("#", numero) == c("#", numero), numero


def test_un_instante_en_un_punto_de_control_y_k_acciones_despues_equivalen_a_reconstruir_desde_el_cero():
    """FR-019, FR-020 · con K=4 y con un solo punto (el 0): las mismas respuestas en los puntos y a K acciones"""
    cuatro, vivos, _, comandos = _juego(4, n=70)
    solo_cero, _, _, _ = _juego(1000, comandos=comandos)
    a, b = _consultar(cuatro), _consultar(solo_cero)
    relojes = cuatro.linea_tiempo.relojes
    assert len(cuatro.linea_tiempo.puntos) >= 8
    for frontera in (0, 4, 8, 12, 16, 8 + 4):
        decision = relojes[frontera]                                 #reloj de la acción frontera+1
        for t in (decision - 1, decision, decision + 1, decision + 37):
            if 0 <= t <= cuatro.partida.reloj:
                assert a("t", t) == b("t", t), (frontera, t)
        assert a("#", frontera + 1) == b("#", frontera + 1)


def test_una_consulta_repetida_da_lo_mismo_y_no_gasta_los_puntos_de_control():
    """FR-006, FR-023 · consultar dos veces lo mismo da lo mismo; los puntos de control quedan intactos"""
    servicio, _, _, _ = _juego(3, n=50)
    linea = servicio.linea_tiempo
    primero = [_consultar(servicio)("t", t) for t in (0, 100, 777, servicio.partida.reloj)]
    segundo = [_consultar(servicio)("t", t) for t in (0, 100, 777, servicio.partida.reloj)]
    assert primero == segundo
    assert len(linea.puntos) == servicio.partida.acciones_jugador // 3 + 1


# ---------------------------------------------------------------- US2 (FR-006, FR-008, FR-009)

def _dar_pergaminos(m, cantidad):
    inv = m.partida.jugador.inventario
    inv.capacidad_max += cantidad                                    #que quepan aunque el inventario esté lleno
    for _ in range(cantidad):
        inv.agregar(m.fabrica.objeto_desde_id("perg"))


def _traza_de_retrocesos(servicio):
    """Lee pergaminos hasta que se niegan; anota lo que quedó tras cada lectura."""
    traza = []
    while servicio.retroceder():
        p = servicio.partida
        traza.append((p.acciones_jugador, p.reloj, resumen_plano(p)))
    return traza


def test_las_consultas_no_cambian_el_juego_ni_el_historial_de_deshacer():
    """FR-006, FR-008, FR-009 · US2-1, US2-3, US2-4, US2-5 · con consultas intercaladas (aceptadas y
    rechazadas) el reloj, el estado, las acciones, la agenda, el azar y lo que el pergamino revierte son
    idénticos a los del mismo juego sin consultas"""
    m1, con_consultas, _ = _armar(3, 4)
    m2, sin_consultas, _ = _armar(3, 4)
    consultas = []

    def despues(comando):
        p = con_consultas.partida
        huella = _huella(p)
        for r in (con_consultas.historia_por_instante(p.reloj // 2),
                  con_consultas.historia_por_instante(p.reloj + 5),          #rechazada
                  con_consultas.historia_por_accion(max(1, p.acciones_jugador)),
                  con_consultas.historia_por_accion(p.acciones_jugador + 3),  #rechazada
                  con_consultas.historia_por_instante("x")):                 #rechazada
            consultas.append(r.aceptada)
        assert _huella(p) == huella, comando

    c1 = jugar_semilla(con_consultas, 8, 80, despues=despues)
    c2 = jugar_semilla(sin_consultas, 8, 80)
    assert c1 == c2 and consultas.count(True) >= 100 and consultas.count(False) >= 100
    assert _huella(con_consultas.partida) == _huella(sin_consultas.partida)   #US2-5: finales idénticos
    _dar_pergaminos(m1, 3)
    _dar_pergaminos(m2, 3)
    t1, t2 = _traza_de_retrocesos(con_consultas), _traza_de_retrocesos(sin_consultas)
    assert len(t1) == len(t2) >= 3                                          #el mismo número de acciones
    assert t1 == t2                                                         #y las mismas, en el mismo orden


# ---------------------------------------------------------------- US2: sin red (FR-006, FR-009; investigación R8)

def test_las_consultas_no_tocan_la_red_ni_el_catalogo_aunque_la_ficha_se_haya_desalojado():
    """FR-006, FR-009 · cien consultas sobre 1 000 acciones que entraron a muchas salas: ninguna llamada,
    el contador de solicitudes no se mueve y una ficha desalojada hace mucho se encuentra igual"""
    m, servicio, _ = _armar(7, 50, salas=40, enemigos=12, cazadores=3)
    m.partida.sala_salida = None                                     #sin victoria: el juego sigue
    jugar_semilla(servicio, 18, 1000)
    p = servicio.partida
    assert p.acciones_jugador >= 600
    entradas = sum(1 for s in p.conocidas if s.rastro is not None)
    assert entradas >= 30
    assert not m.catalogo.cache.contiene("espada")                   #desalojada de la caché de 2 fichas
    resoluciones, llamadas = m.catalogo.resoluciones, m.cliente.llamadas

    def prohibido(*args, **kwargs):
        raise AssertionError("la consulta usó el catálogo")
    m.catalogo.resolver = prohibido
    m.catalogo.ids_del_contenido = prohibido
    huella = _huella(p)
    consultar = _consultar(servicio)
    for i in range(100):
        consultar("t", p.reloj * i // 100)
        consultar("#", 1 + p.acciones_jugador * i // 100)
    r = servicio.historia_por_accion(1)                              #restaura la sala 1 con la espada del suelo
    assert any(o.id_catalogo == "espada" for o in r.partida.jugador.sala.objetos)
    assert (m.catalogo.resoluciones, m.cliente.llamadas) == (resoluciones, llamadas)
    assert m.cliente.solicitudes_realizadas() == 0
    assert _huella(p) == huella
