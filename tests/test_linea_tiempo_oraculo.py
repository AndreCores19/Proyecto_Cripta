"""El oráculo de la línea de tiempo (spec 005, SC-002).

Modo 1, sin pergaminos (Fase 4): se juega una partida con semilla anotando el resumen vivo antes de
cada acción del jugador; un segundo juego vivo, instrumentado, anota una foto tras cada evento. Luego
cada `#k` y cada instante t se consulta y se compara con lo que esos juegos mostraron.
Los modos 2 (con pergaminos) y 3 (tras guardar y cargar) los agregan las fases 5 y 8.
"""
import random

import pytest

from controller.controlador import Controlador
from linea_tiempo_apoyo import (PartidaInstrumentada, VistaMuda, _elegir_comando, armar_mundo, con_reloj,
                                ejecutar_comandos, instantes_clave, jugar_semilla, oraculo,
                                registrar_vivo, resumen_plano)
from model.linea_tiempo_logica import LineaTiempoPartida
from service.juego_service import JuegoService

MUNDO = dict(salas=9, enemigos=6, cazadores=2)


def _juego_vivo(k, semilla_mundo, semilla_juego, n, vida, clase=None, con_linea=True, preparar=None, **mundo):
    parametros = dict(MUNDO)
    parametros.update(mundo)
    if clase is not None:
        parametros["clase_partida"] = clase
    m = armar_mundo(semilla_mundo, vida_jugador=vida, **parametros)
    if preparar is not None:
        preparar(m)
    if not con_linea:
        return m, JuegoService(m.partida, m.fabrica)
    linea = LineaTiempoPartida()
    linea.iniciar(m.partida, m.constructor, k)
    return m, JuegoService(m.partida, m.fabrica, linea_tiempo=linea)


def _consultar(servicio):
    def consultar(modo, valor):
        r = (servicio.historia_por_instante(valor) if modo == "t"
             else servicio.historia_por_accion(valor))
        assert r.aceptada, f"{modo} {valor} rechazada: {r.motivo}"
        return con_reloj(resumen_plano(r.partida), r.reloj)
    return consultar


def _correr(k, semilla_mundo, semilla_juego, n, vida, **mundo):
    m, servicio = _juego_vivo(k, semilla_mundo, semilla_juego, n, vida, **mundo)
    vivos = []
    comandos = jugar_semilla(servicio, semilla_juego, n, vivos=vivos)
    m2, servicio2 = _juego_vivo(k, semilla_mundo, semilla_juego, n, vida,
                                clase=PartidaInstrumentada, con_linea=False, **mundo)
    ejecutar_comandos(servicio2, comandos)
    assert resumen_plano(m2.partida) == resumen_plano(m.partida)
    return servicio, vivos, m2.partida.instantaneas


@pytest.mark.parametrize("k, acciones", [(1, 400), (3, 400), (7, 400), (100000, 150)])
def test_oraculo_modo_1_sin_pergaminos_con_cazadores_veneno_trampas_y_puertas(k, acciones):
    """SC-002, FR-001, FR-002, FR-003, FR-004 · `#k` y cada instante de una partida de 400 acciones
    (150 con K mayor que el juego, que reproduce todo desde el cero) dan lo que el juego vivo mostró"""
    servicio, vivos, instantaneas = _correr(k, 4, 11, acciones, vida=600)
    p = servicio.partida
    assert p.acciones_jugador >= min(acciones, 100)
    consultar = _consultar(servicio)
    paso = 97 if k < 100 else 331
    oraculo(servicio, vivos, instantaneas, consultar,
            instantes=instantes_clave(vivos, instantaneas, p.reloj, paso))
    #los ingredientes del juego están: efectos activos y más de una sala conocida
    planos = [v[2] for v in vivos]
    assert any(plano[2][7] for plano in planos), "hubo un efecto activo (veneno o velocidad)"
    assert max(len(plano[5][1]) for plano in planos) >= 4


def test_oraculo_modo_1_con_una_muerte():
    """SC-002, FR-002 · un juego que termina con la muerte del jugador: cada instante hasta el final coincide"""
    servicio, vivos, instantaneas = _correr(3, 4, 23, 400, vida=90)
    p = servicio.partida
    assert p.terminada and not p.victoria
    oraculo(servicio, vivos, instantaneas, _consultar(servicio),
            instantes=instantes_clave(vivos, instantaneas, p.reloj, 53))


# ---------------------------------------------------------------- modo 2: con pergaminos (SC-002, SC-004)

def _pergaminos_en_todas_las_salas(m):
    for contenido in m.contenidos[1:]:
        contenido.objetos.append("perg")


def _tiene_pergamino(servicio):
    return any(o.nombre == "Pergamino" for o in servicio.inventario_vista().objetos)


def _paso_hacia_un_pergamino(servicio):
    """`sig`, `ant` o `usar` según donde esté el cursor respecto de un pergamino del inventario."""
    objetos = servicio.inventario_vista().objetos
    for i, o in enumerate(objetos):
        if o.actual:
            if o.nombre == "Pergamino":
                return "usar"
            for j, otro in enumerate(objetos):
                if otro.nombre == "Pergamino":
                    return "sig" if j > i else "ant"
    return "esperar"


def _jugar_con_lecturas(servicio, semilla, n):
    """Juega n comandos con semilla y lee pergaminos en momentos sembrados: justo después de entrar por
    primera vez a una sala, justo después de recoger un pergamino, dos veces seguidas y con `usar`.
    Devuelve (comandos, vivos, lecturas) con lecturas = [(índice del comando, comando)]."""
    azar = random.Random(semilla)
    controlador = Controlador(servicio, VistaMuda(), None, None)
    p = servicio.partida
    comandos, vivos, lecturas, cola = [], [], [], []
    for _ in range(n):
        if servicio.terminada():
            break
        if cola and cola[0] == "LEER_CON_USAR":
            cola.pop(0)
            if _tiene_pergamino(servicio):
                comando = _paso_hacia_un_pergamino(servicio)
                if comando != "usar":
                    cola.insert(0, "LEER_CON_USAR")
            else:
                comando = "esperar"
        elif cola:
            comando = cola.pop(0)
        else:
            comando = _elegir_comando(azar, servicio, False)
        recoge_pergamino = (comando.startswith("recoger ") and
                            any(o.nombre == "Pergamino" and str(o.id_instancia) == comando.split()[1]
                                for o in servicio.objetos_en_sala()))
        exploradas = len(p.conocidas)
        retrocesos = p.retrocesos
        registrar_vivo(vivos, servicio)
        controlador.ejecutar(comando)
        comandos.append(comando)
        leyo = p.retrocesos > retrocesos
        if leyo:
            lecturas.append((len(comandos) - 1, comando))
        if servicio.terminada() or cola:
            continue
        en_el_suelo = [o.id_instancia for o in servicio.objetos_en_sala() if o.nombre == "Pergamino"]
        if en_el_suelo and azar.random() < 0.6:
            cola.append(f"recoger {en_el_suelo[0]}")         #para tener más de uno a mano
            continue
        if not _tiene_pergamino(servicio):
            continue
        if leyo and azar.random() < 0.8:
            cola.append("retroceder")                       #dos seguidas
        elif recoge_pergamino and azar.random() < 0.7:
            cola.append("retroceder")                       #revierte la recogida de un pergamino
        elif len(p.conocidas) > exploradas and azar.random() < 0.7:
            cola.append("retroceder")                       #justo después de entrar a una sala nueva
        elif azar.random() < 0.05:
            cola.append("LEER_CON_USAR")
    registrar_vivo(vivos, servicio)
    return comandos, vivos, lecturas


def _correr_con_pergaminos(k, semilla_mundo, semilla_juego, n, vida=5000):
    parametros = dict(MUNDO)
    parametros["con_pergaminos"] = True
    m, servicio = _juego_vivo(k, semilla_mundo, semilla_juego, n, vida, preparar=_pergaminos_en_todas_las_salas,
                              **parametros)
    comandos, vivos, lecturas = _jugar_con_lecturas(servicio, semilla_juego, n)
    m2, servicio2 = _juego_vivo(k, semilla_mundo, semilla_juego, n, vida, clase=PartidaInstrumentada,
                                con_linea=False, preparar=_pergaminos_en_todas_las_salas, **parametros)
    ejecutar_comandos(servicio2, comandos)
    assert resumen_plano(m2.partida) == resumen_plano(m.partida)
    return servicio, vivos, m2.partida.instantaneas, lecturas


@pytest.mark.parametrize("k, acciones, semilla", [(1, 300, 29), (3, 300, 29), (7, 300, 29), (100000, 150, 33)])
def test_oraculo_modo_2_tras_pergaminos(k, acciones, semilla):
    """SC-002, SC-004, FR-010 · una partida con al menos cinco lecturas de pergamino (una por `usar`, dos
    seguidas): cada `#k` que sobrevive y cada instante hasta el reloj dan lo que mostró el juego vivo, y los
    números de acciones revertidas se rechazan"""
    servicio, vivos, instantaneas, lecturas = _correr_con_pergaminos(k, 4, semilla, acciones)
    p = servicio.partida
    assert p.retrocesos >= 5, f"solo {p.retrocesos} lecturas"
    assert any(c == "usar" for _, c in lecturas), "alguna lectura por `usar` con el cursor sobre el pergamino"
    assert any(b - a == 1 for (a, _), (b, _) in zip(lecturas, lecturas[1:])), "dos lecturas seguidas"
    consultar = _consultar(servicio)
    paso = 97 if k < 100 else 331
    oraculo(servicio, vivos, instantaneas, consultar,
            instantes=instantes_clave(vivos, instantaneas, p.reloj, paso))
    n = p.acciones_jugador
    assert servicio.historia_por_accion(n + 1).motivo == "accion_inexistente"
    assert servicio.historia_por_instante(p.reloj + 1).motivo == "despues_del_reloj"
