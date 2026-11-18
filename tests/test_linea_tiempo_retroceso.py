"""El pergamino de retroceso y la línea de tiempo (spec 005, Fase 5, US3).

Tras un pergamino la línea de tiempo describe el juego tal como quedó: recorta desde el final, no toma
ningún punto de control nuevo y guarda en un libro los efectos que el deshacer de la parte uno omite
a propósito (investigación R6). Todo con datos falsos y sin red. Cada guion es un generador de
comandos que puede mirar el estado vivo entre uno y otro; los mismos comandos se repiten en un segundo
juego instrumentado que no usa nada de la línea de tiempo y que sirve de oráculo.
"""
import pytest

from controller.controlador import Controlador
from dto.contenido_sala_dto import InstanciaEnemigoDTO
from linea_tiempo_apoyo import (PartidaInstrumentada, VistaMuda, armar_mundo, con_reloj,
                                ejecutar_comandos, oraculo, partida_consultada, registrar_vivo,
                                resumen_plano)
from model.linea_tiempo_logica import LineaTiempoPartida
from model.partida_logica import Partida
from service.juego_service import JuegoService


def _armar(k, preparar=None, clase=Partida, con_linea=True, vida=5000, **mundo):
    parametros = dict(salas=6, enemigos=0, cazadores=0, con_pergaminos=True)
    parametros.update(mundo)
    m = armar_mundo(3, clase_partida=clase, vida_jugador=vida, **parametros)
    if preparar is not None:
        preparar(m)
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
        return resumen_plano(r.resumen)
    return consultar


class Corrida:
    def __init__(self, servicio, linea, mundo, vivos, instantaneas, comandos):
        self.servicio = servicio
        self.partida = servicio.partida
        self.linea = linea
        self.mundo = mundo
        self.vivos = vivos
        self.instantaneas = instantaneas
        self.comandos = comandos

    def oraculo(self):
        """Cada `#k` y cada instante de 0 al reloj dan lo que mostró el juego vivo."""
        oraculo(self.servicio, self.vivos, self.instantaneas, _consultar(self.servicio))

    def consultar(self, modo, valor):
        return _consultar(self.servicio)(modo, valor)


def _correr(guion, k=3, preparar=None, vida=5000, **mundo):
    """Ejecuta el guion (un generador de comandos) con la línea de tiempo y repite los mismos comandos en
    un segundo juego instrumentado, sin línea de tiempo."""
    m, servicio, linea = _armar(k, preparar, vida=vida, **mundo)
    controlador = Controlador(servicio, VistaMuda(), None, None)
    vivos, comandos = [], []
    for comando in guion(servicio):
        registrar_vivo(vivos, servicio)
        controlador.ejecutar(comando)
        comandos.append(comando)
    registrar_vivo(vivos, servicio)
    m2, servicio2, _ = _armar(k, preparar, clase=PartidaInstrumentada, con_linea=False, vida=vida, **mundo)
    ejecutar_comandos(servicio2, comandos)
    assert resumen_plano(m2.partida) == resumen_plano(m.partida)
    return Corrida(servicio, linea, m, vivos, m2.partida.instantaneas, comandos)


#el mundo: sala 1 tiene la llave (id 1) y dos pergaminos (ids 8 y 9); la sala 2 puede tener más
def _seis_pergaminos_en_la_sala_2(m):
    m.contenidos[1].objetos.extend(["perg"] * 6)


def _pergaminos_del_suelo(servicio):
    return [o.id_instancia for o in servicio.objetos_en_sala() if o.nombre == "Pergamino"]


def _ids_del_inventario(servicio):
    return [o.id_instancia for o in servicio.inventario_vista().objetos]


def _estado_vivo(corrida):
    return resumen_plano(corrida.partida)


def _guion_basico(s):
    yield "recoger 8"
    yield "recoger 9"
    yield "w"                                   #sala 2
    yield "esperar"
    yield "esperar"
    yield "esperar"
    yield "retroceder"                          #revierte el último `esperar` y gasta un pergamino
    yield "esperar"
    yield "esperar"
    yield "s"                                   #de vuelta a la sala 1
    yield "w"


# ---------------------------------------------------------------- US3-1, US3-3: nada revertido se ve

@pytest.mark.parametrize("k", [1, 3, 1000])
def test_tras_un_pergamino_ninguna_consulta_muestra_lo_revertido_ni_lo_nuevo_falta(k):
    """FR-010 · US3-1, US3-3 · cada instante y cada `#k` de un juego con un pergamino y acciones nuevas
    después da lo que el juego vivo mostró; el número de la acción revertida se reutiliza"""
    c = _correr(_guion_basico, k=k)
    assert c.partida.retrocesos == 1
    assert len(c.linea) == c.partida.acciones_jugador == 9
    assert c.linea.tipos[5:9] == ["esperar", "esperar", "mover", "mover"]   #lo nuevo, no lo revertido
    c.oraculo()


def _guion_hasta_el_pergamino(s):
    yield "recoger 8"
    yield "w"
    yield "esperar"
    yield "esperar"
    yield "retroceder"


def test_tras_el_pergamino_un_instante_posterior_y_una_accion_revertida_se_rechazan():
    """FR-003, FR-005, FR-010 · US3-2, US3-4 · el reloj bajó: `t` mayor se rechaza; `#k` más allá de las
    acciones que quedaron se rechaza y la numeración sigue desde la última que sobrevivió"""
    antes = {}

    def guion(s):
        yield from _guion_hasta_el_pergamino_con_marca(s, antes)
    c = _correr(guion)
    p = c.partida
    assert p.reloj < antes["reloj"] and p.acciones_jugador == antes["acciones"] - 1
    assert c.servicio.historia_por_instante(antes["reloj"]).motivo == "despues_del_reloj"
    assert c.servicio.historia_por_instante(p.reloj + 1).motivo == "despues_del_reloj"
    assert c.servicio.historia_por_instante(p.reloj).aceptada
    assert c.servicio.historia_por_accion(antes["acciones"]).motivo == "accion_inexistente"
    assert c.servicio.historia_por_accion(p.acciones_jugador).aceptada
    c.oraculo()


def _guion_hasta_el_pergamino_con_marca(s, marca):
    yield "recoger 8"
    yield "w"
    yield "esperar"
    yield "esperar"
    marca["reloj"], marca["acciones"] = s.partida.reloj, s.partida.acciones_jugador
    yield "retroceder"


def test_la_numeracion_sigue_desde_la_ultima_accion_que_sobrevivio():
    """FR-003, FR-010 · US3-4 · tras el pergamino la próxima acción recibe el número de la revertida"""
    def guion(s):
        yield from _guion_hasta_el_pergamino(s)
        yield "s"
    c = _correr(guion)
    assert len(c.linea) == 4 and c.linea.tipos[3] == "mover"
    assert c.servicio.historia_por_accion(5).motivo == "accion_inexistente"
    assert c.servicio.historia_por_accion(4).aceptada
    c.oraculo()


# ---------------------------------------------------------------- US3-6: el límite de 5 y el pergamino por `usar`

def _guion_seis_lecturas(s):
    yield "w"                                   #sala 2, con seis pergaminos en el suelo
    for _ in range(6):
        yield f"recoger {_pergaminos_del_suelo(s)[0]}"
    for _ in range(6):
        yield "esperar"
    for _ in range(6):                          #cada lectura revierte una acción: la sexta se niega
        yield "retroceder"


def test_el_pergamino_sigue_revirtiendo_como_maximo_cinco_y_la_linea_responde_lo_mas_viejo():
    """FR-012 · US3-6 · seis lecturas seguidas revierten cinco; la sexta se niega y no recorta nada;
    la línea de tiempo responde instantes mucho más viejos que esas cinco acciones"""
    c = _correr(_guion_seis_lecturas, preparar=_seis_pergaminos_en_la_sala_2)
    p = c.partida
    assert p.retrocesos == 5
    assert p.acciones_jugador == 13 - 5 and len(c.linea) == 8
    assert c.servicio.retroceder() is False                          #"no hay acciones que retroceder"
    assert len(c.linea) == 8 and p.acciones_jugador == 8
    assert c.servicio.historia_por_accion(1).aceptada
    assert c.servicio.historia_por_instante(0).aceptada
    c.oraculo()


def test_un_pergamino_leido_con_usar_recorta_igual_que_retroceder_y_no_se_graba_como_accion():
    """FR-010, FR-012 · el comando `usar` con el cursor sobre el pergamino recorta como `retroceder`"""
    def guion(s):
        yield "recoger 8"
        yield "w"
        yield "esperar"
        for _ in range(10):                      #el cursor sobre el pergamino
            ids = [o.id_instancia for o in s.inventario_vista().objetos if o.actual]
            if ids == [8]:
                break
            yield "sig"
        yield "usar"
        yield "esperar"
    c = _correr(guion)
    assert c.partida.retrocesos == 1
    assert c.linea.tipos == ["recoger", "mover", "esperar"] and len(c.linea) == c.partida.acciones_jugador == 3
    c.oraculo()


def test_con_menos_de_cinco_acciones_recorta_solo_lo_revertido_y_los_pergaminos_seguidos_recortan_por_turno():
    """FR-010, FR-011 · un pergamino con dos acciones hechas recorta una; dos seguidos recortan en orden"""
    def guion(s):
        yield "recoger 8"
        yield "recoger 9"
        yield "retroceder"                       #revierte `recoger 9`; gasta el pergamino 8
        yield "retroceder"                       #revierte `recoger 8`; gasta el pergamino 9 (que sigue en la mano)
        yield "esperar"
    c = _correr(guion)
    assert c.partida.retrocesos == 2
    assert len(c.linea) == c.partida.acciones_jugador == 1 and c.linea.tipos == ["esperar"]
    c.oraculo()


def test_un_pergamino_que_revierte_la_recogida_de_otro_pergamino():
    """FR-010 · un pergamino que revierte la recogida de un pergamino: queda en la mano y el suelo ya no lo tiene"""
    def guion(s):
        yield "recoger 8"
        yield "recoger 9"
        yield "esperar"
        yield "retroceder"
        yield "esperar"
    c = _correr(guion)
    c.oraculo()


# ---------------------------------------------------------------- US3-5: el trabajo del recorte no depende del largo

def _operaciones_de_un_pergamino(largo):
    def guion(s):
        yield "recoger 8"
        for _ in range(largo):
            yield "esperar"
        yield "retroceder"
    m, servicio, linea = _armar(50)
    controlador = Controlador(servicio, VistaMuda(), None, None)
    for comando in guion(servicio):
        controlador.ejecutar(comando)
    return linea.linea.operaciones_retroceso, len(linea)


def test_el_trabajo_de_un_pergamino_no_depende_del_largo_del_juego():
    """FR-011 · US3-5 · pergamino en la acción 1 000 y en la 5 000 del mismo mundo: igual trabajo (±r)"""
    corto, acciones_cortas = _operaciones_de_un_pergamino(1000)
    largo, acciones_largas = _operaciones_de_un_pergamino(5000)
    assert acciones_largas > 4 * acciones_cortas
    assert corto >= 1 and abs(largo - corto) <= 1
    assert largo <= 10


# ---------------------------------------------------------------- el libro de efectos omitidos (investigación R6)

def _guion_pergamino_consumido(s):
    yield "recoger 8"
    yield "recoger 9"
    yield "w"
    yield "esperar"
    yield "retroceder"
    yield "esperar"


def test_libro_1_el_pergamino_gastado_falta_despues_del_retroceso_y_sigue_antes():
    """FR-010, FR-023 · R6 fila 1 · el pergamino leído no está tras el punto de retroceso y sí antes"""
    c = _correr(_guion_pergamino_consumido)
    vivo = _estado_vivo(c)
    assert _ids_del_inventario(c.servicio) == [9]                    #el 8 se gastó
    assert c.consultar("t", c.partida.reloj) == con_reloj(vivo, c.partida.reloj)
    antes = c.servicio.historia_por_accion(3).resumen                #justo antes de `w`: el 8 aún no se gastó
    assert [o.id_instancia for o in antes.inventario] == [8, 9]
    despues = c.servicio.historia_por_accion(4).resumen              #tras el pergamino: ya no está
    assert [o.id_instancia for o in despues.inventario] == [9]
    c.oraculo()


def test_libro_2_un_pergamino_recogido_por_una_accion_revertida_queda_en_la_mano_y_no_en_el_suelo():
    """FR-010, FR-023 · R6 fila 2 · el deshacer deja el pergamino recogido en el inventario"""
    def guion(s):
        yield "recoger 8"
        yield "w"
        yield f"recoger {_pergaminos_del_suelo(s)[0]}"
        yield "retroceder"                                           #gasta el 8, revierte la recogida
        yield "esperar"
    c = _correr(guion, preparar=_seis_pergaminos_en_la_sala_2)
    inv = _ids_del_inventario(c.servicio)
    assert len(inv) == 1 and inv[0] != 8
    assert inv[0] not in _pergaminos_del_suelo(c.servicio)
    consulta = partida_consultada(c.servicio, "t", c.partida.reloj)
    assert [o.id_instancia for o in consulta.jugador.inventario.a_lista()] == inv
    assert inv[0] not in [o.id_instancia for o in consulta.jugador.sala.objetos]
    c.oraculo()


def test_libro_3_un_pergamino_soltado_por_una_accion_revertida_esta_en_el_suelo_y_no_en_la_mano():
    """FR-010, FR-023 · R6 fila 3 · el deshacer deja el pergamino soltado en el suelo"""
    def guion(s):
        yield "recoger 8"
        yield "recoger 9"
        yield "soltar"                                               #suelta el 8
        yield "retroceder"                                           #gasta el 9, revierte el soltar
        yield "esperar"
    c = _correr(guion)
    assert _ids_del_inventario(c.servicio) == []
    assert 8 in _pergaminos_del_suelo(c.servicio)
    consulta = partida_consultada(c.servicio, "t", c.partida.reloj)
    assert consulta.jugador.inventario.a_lista() == []
    assert 8 in [o.id_instancia for o in consulta.jugador.sala.objetos]
    c.oraculo()


def _con_rata_en_la_sala_2(m):
    m.contenidos[1].enemigos.append(InstanciaEnemigoDTO("x1", "rata", None))


def _matar_a_x1(s):
    while any(e.id_enemigo == "x1" and e.vida > 0 for e in s.partida.enemigos):
        yield "atacar"


def test_libro_4_el_contador_de_instancias_avanza_con_el_botin_de_una_muerte_revertida():
    """FR-010, FR-023 · R6 fila 4 · el botín de una muerte revertida avanza el contador: el objeto que se
    crea después tiene el mismo id en el juego vivo y en la consulta"""
    def guion(s):
        yield "recoger 8"
        yield "w"                                                    #sala 2 con una rata que suelta una poción
        yield from _matar_a_x1(s)
        yield "retroceder"                                           #revierte el golpe que la mató
        yield from _matar_a_x1(s)                                    #la mata otra vez: botín con id nuevo
        ids = [o.id_instancia for o in s.objetos_en_sala() if o.nombre == "Poción de vida"]
        yield f"recoger {ids[-1]}"
    c = _correr(guion, preparar=_con_rata_en_la_sala_2)
    vivo = _estado_vivo(c)
    assert c.consultar("t", c.partida.reloj) == con_reloj(vivo, c.partida.reloj)
    c.oraculo()


def _guion_sala_poblada_por_un_movimiento_revertido(s):
    yield "recoger 8"
    yield "recoger 1"                                                #la llave de la puerta forzada
    yield "w"                                                        #sala 2 (con una rata)
    yield "abrir w"
    yield "w"                                                        #sala 3: el movimiento que se revierte
    yield "retroceder"                                               #gasta el 8; la sala 3 sigue poblada
    yield from _matar_a_x1(s)                                        #el botín toma el id que sigue al de la sala 3
    ids = [o.id_instancia for o in s.objetos_en_sala() if o.nombre == "Poción de vida"]
    yield f"recoger {ids[-1]}"
    yield "abrir w"                                                  #la puerta se cerró sola
    yield "w"                                                        #entra de nuevo a la sala 3 (ya poblada)
    for id_objeto in _pergaminos_del_suelo(s)[:1]:
        yield f"recoger {id_objeto}"


def _preparar_sala_3(m):
    _con_rata_en_la_sala_2(m)
    m.contenidos[2].objetos.append("perg")                          #un pergamino creado por esa población


def test_libro_5_y_6_la_sala_poblada_por_un_movimiento_revertido_y_sus_pergaminos_tienen_los_mismos_ids():
    """FR-010, FR-023 · R6 filas 5 y 6 · una sala poblada por un movimiento revertido conserva su población
    (objetos, ids y pergaminos) y el botín posterior sale con el mismo id en la consulta que en el juego"""
    c = _correr(_guion_sala_poblada_por_un_movimiento_revertido, k=4, preparar=_preparar_sala_3)
    vivo = _estado_vivo(c)
    assert c.consultar("t", c.partida.reloj) == con_reloj(vivo, c.partida.reloj)
    assert c.partida.jugador.sala.id == 3 and len(_ids_del_inventario(c.servicio)) >= 2
    c.oraculo()


def test_un_punto_de_control_que_el_recorte_conserva_no_se_refresca_y_se_le_aplican_las_entradas():
    """FR-019, FR-020 · con K=4 el recorte deja el punto de la frontera 4 sin tocar; la consulta que parte de él
    aplica las entradas de esa frontera; no hay ningún punto fuera de la cuadrícula de K"""
    c = _correr(_guion_sala_poblada_por_un_movimiento_revertido, k=4, preparar=_preparar_sala_3)
    linea = c.linea.linea
    assert len(linea.puntos) <= c.partida.acciones_jugador // 4 + 1
    punto4 = linea.puntos[1]
    assert punto4.acciones_jugador == 4
    sala3 = [s for s in punto4.salas if s.id_sala == 3]
    assert not sala3 or not sala3[0].poblada                        #se tomó antes de poblar la sala 3
    kept = [e for e in linea.omitidos if e.reaplicar]
    assert kept and all(e.etiqueta <= c.partida.acciones_jugador for e in kept)
    assert any(e.tipo == "poblar" and e.etiqueta == 4 for e in kept)
    c.oraculo()


@pytest.mark.parametrize("k", [1, 2, 3, 4, 7])
def test_nunca_hay_un_punto_fuera_de_la_cuadricula_de_k_tras_cada_pergamino(k):
    """FR-019 · `len(puntos) <= ⌊A/K⌋ + 1` y la frontera de cada punto es múltiplo de K, tras cada comando"""
    def guion(s):
        yield from _guion_seis_lecturas(s)
        yield "esperar"
    m, servicio, linea = _armar(k, _seis_pergaminos_en_la_sala_2)
    controlador = Controlador(servicio, VistaMuda(), None, None)
    for comando in guion(servicio):
        controlador.ejecutar(comando)
        a = servicio.partida.acciones_jugador
        assert len(linea.puntos) <= a // k + 1, comando
        for i, punto in enumerate(linea.puntos):
            assert punto.acciones_jugador == i * k, comando
        assert len(linea) == a


# ---------------------------------------------------------------- reglas del libro (data-model, "EfectoOmitido")

def test_las_entradas_del_libro_van_en_orden_y_una_de_la_ventana_vieja_se_descarta():
    """FR-010, FR-011, FR-021 · las etiquetas no bajan; la entrada de una acción más vieja que la
    capacidad del historial (5) se descarta tras registrar la acción que la deja fuera"""
    m, servicio, linea = _armar(50)
    c = Controlador(servicio, VistaMuda(), None, None)
    c.ejecutar("recoger 8")
    assert [e.etiqueta for e in linea.linea.omitidos] == [1, 1]
    assert [e.reaplicar for e in linea.linea.omitidos] == [False, False]
    for _ in range(3):
        c.ejecutar("esperar")
    assert len(linea.linea.omitidos) == 2                            #acciones 1..4: aún se puede revertir
    c.ejecutar("esperar")                                            #acción 5: la 1 todavía cuenta
    assert len(linea.linea.omitidos) == 2
    c.ejecutar("esperar")                                            #acción 6: la 1 ya no se puede revertir
    assert linea.linea.omitidos == []


def test_tras_un_pergamino_las_entradas_guardadas_tienen_la_etiqueta_n_y_reaplicar():
    """FR-010 · las entradas de la ventana revertida y las del propio pergamino quedan con etiqueta n y
    `reaplicar`; las de acciones que sobrevivieron siguen como candidatas"""
    def guion(s):
        yield "recoger 8"
        yield "recoger 9"
        yield "soltar"
        yield "retroceder"
    c = _correr(guion)
    n = c.partida.acciones_jugador
    entradas = c.linea.linea.omitidos
    guardadas = [e for e in entradas if e.reaplicar]
    candidatas = [e for e in entradas if not e.reaplicar]
    assert guardadas and all(e.etiqueta == n for e in guardadas)
    assert all(e.etiqueta <= n for e in candidatas)
    assert [e.tipo for e in guardadas][-1] == "contador"
    tags = [e.etiqueta for e in entradas]
    assert tags == sorted(tags)


def test_un_segundo_pergamino_reetiqueta_primero_lo_guardado_antes_y_conserva_el_orden():
    """FR-010 · el segundo pergamino a n2 < n reetiqueta a n2 lo que había guardado y la nueva ventana,
    sin cambiar el orden de ocurrencia"""
    def guion(s):
        yield "w"
        for _ in range(4):
            yield f"recoger {_pergaminos_del_suelo(s)[0]}"
        yield "soltar"
        yield "retroceder"
        yield "retroceder"
    c = _correr(guion, preparar=_seis_pergaminos_en_la_sala_2)
    assert c.partida.retrocesos == 2
    n2 = c.partida.acciones_jugador
    entradas = c.linea.linea.omitidos
    guardadas = [e for e in entradas if e.reaplicar]
    assert all(e.etiqueta == n2 for e in guardadas)
    #en el orden en que ocurrieron: la recogida revertida por el segundo pergamino, lo del soltar revertido
    #por el primero, el pergamino gastado y el contador de cada lectura
    assert [e.tipo for e in guardadas] == ["suelo_quitar", "inv_agregar", "inv_quitar", "suelo_poner",
                                            "inv_quitar", "contador", "inv_quitar", "contador"]
    assert all(e.etiqueta <= n2 and not e.reaplicar for e in entradas if e not in guardadas)
    c.oraculo()


def test_el_libro_no_crece_con_el_largo_del_juego_sin_pergaminos():
    """FR-011, FR-021 · tras 5 000 acciones sin pergamino el libro tiene a lo más las entradas de las últimas 5"""
    m, servicio, linea = _armar(50)
    c = Controlador(servicio, VistaMuda(), None, None)
    c.ejecutar("recoger 8")
    mayor = 0
    for i in range(2500):
        c.ejecutar("soltar")
        c.ejecutar("recoger 8")
        mayor = max(mayor, len(linea.linea.omitidos))
    assert servicio.partida.acciones_jugador == 5001
    assert len(linea.linea.omitidos) <= 10 and mayor <= 10          #dos entradas por acción, cinco acciones
