from model.solvabilidad_logica import Verificador
from model.trampa_logica import Trampa
from tests.mapas_solvabilidad import (armar_vector, barajar, cadena_de_llaves, cripta, cripta_aleatoria_con_llaves,
                                      id_llave, logicas, resolver_referencia, resumen)


def verificar(salas, inicial, salida, llave_salida, llaves):
    """Corre la verificación sobre una copia de la lista de llaves (cada llamada arma llaves nuevas)."""
    return Verificador().verificar(armar_vector(salas), inicial, salida, llave_salida, logicas(llaves))


def test_oraculo_cadena_de_dos_llaves_da_el_orden_k1_k2():
    """FR-008, FR-009 · el oráculo ordena dos llaves encadenadas: k1 en la sala 1 abre la puerta 1-2, k2 en la sala 2 abre la 2-3"""
    salas = cripta(3, [(1, 2, "k1"), (2, 3, "k2")])
    llaves = [("k1", 1, None), ("k2", 2, None)]
    ref = resolver_referencia(salas, 1, 3, "k2", llaves)
    assert ref.resoluble is True
    assert ref.orden == ["k1", "k2"]
    assert ref.inalcanzables == [] and ref.frontera == [] and ref.ciclos == []


def test_oraculo_llave_de_salida_tras_su_propia_puerta_no_es_resoluble():
    """FR-008, FR-012 · la llave de salida está detrás de la única puerta que ella abre: no resoluble, una puerta en la frontera"""
    salas = cripta(2, [(1, 2, "k")])
    llaves = [("k", 2, None)]
    ref = resolver_referencia(salas, 1, 2, "k", llaves)
    assert ref.resoluble is False
    assert ref.orden == []
    assert ref.inalcanzables == [("k", 2, None)]
    assert len(ref.frontera) == 1 and ref.frontera[0][3] == "k"
    assert len(ref.ciclos) == 1 and [e[0] for e in ref.ciclos[0]] == ["k"]


def test_cadena_de_llaves_el_orden_respeta_cada_dependencia_y_es_el_del_oraculo():
    """FR-008, FR-009, FR-010 · US2-1"""
    for k in (1, 2, 5, 12):
        salas, inicial, salida, llave_salida, llaves = cadena_de_llaves(k)
        resultado = verificar(salas, inicial, salida, llave_salida, llaves)
        assert resultado.resoluble is True
        assert resultado.orden == [id_llave(j) for j in range(1, k + 1)]    # la llave j abre la puerta de la llave j+1
        ref = resolver_referencia(salas, inicial, salida, llave_salida, llaves)
        assert resultado.orden == ref.orden


def _dos_llaves_a_la_vez():
    """La sala 1 tiene ka y kb; ka abre 1-2, kb abre 1-3; la salida (sala 4) está tras kc, que está en la sala 3."""
    salas = cripta(4, [(1, 2, "ka"), (1, 3, "kb"), (2, 4, "kc")])
    llaves = [("kb", 1, None), ("ka", 1, None), ("kc", 3, None)]    # kb listada antes que ka
    return salas, 1, 4, "kc", llaves


def test_con_varias_llaves_obtenibles_a_la_vez_va_primero_la_de_menor_id_y_dos_corridas_dan_lo_mismo():
    """FR-010, FR-011 · US2-2 (escenario 3 del encargo)"""
    salas, inicial, salida, llave_salida, llaves = _dos_llaves_a_la_vez()
    primero = verificar(salas, inicial, salida, llave_salida, llaves)
    segundo = verificar(salas, inicial, salida, llave_salida, llaves)
    assert primero.resoluble is True
    assert primero.orden == ["ka", "kb", "kc"]
    assert segundo.orden == primero.orden


def test_el_orden_no_depende_del_orden_de_las_llaves_ni_de_las_salidas():
    """FR-010 · US2-3"""
    for semilla in range(30):
        salas, inicial, salida, llave_salida, llaves = cripta_aleatoria_con_llaves(semilla, 12, 6)
        base = resumen(verificar(salas, inicial, salida, llave_salida, llaves))
        for otra in range(4):
            barajadas = barajar(salas, llaves, semilla * 10 + otra)
            nuevo = resumen(verificar(salas, inicial, salida, llave_salida, barajadas))
            assert (nuevo.resoluble, nuevo.orden) == (base.resoluble, base.orden)


def test_supuestos_puerta_con_cierre_automatico_trampa_y_llave_que_no_se_consume():
    """FR-007, FR-008 · una puerta con cierre automático y una sala con trampa no bloquean; la llave abre dos puertas"""
    salas = cripta(5, [(1, 2, "k"), (2, 3, "k"), (3, 4, None), (4, 5, "j")])
    for sala in salas:
        for s in sala.salidas:
            if s.llave == "k":
                s.cierre_automatico = 500            # se vuelve a cerrar sola: se vuelve a abrir con la misma llave
    salas[2].trampas.append(Trampa(1, "Pinchos", 5))    # la trampa tampoco bloquea
    llaves = [("k", 1, None), ("j", 3, None)]
    resultado = verificar(salas, 1, 5, "j", llaves)
    assert resultado.resoluble is True
    assert resultado.orden == ["j", "k"] or resultado.orden == ["k", "j"]
    assert resultado.orden == resolver_referencia(salas, 1, 5, "j", llaves).orden


def test_la_llave_de_salida_tomada_pero_sin_puerta_que_la_exija_no_es_resoluble():
    """FR-008 · se necesita una puerta que exija la llave y lleve a la sala de salida"""
    salas = cripta(2, [(1, 2, None)])                 # la salida es la sala 2, sin puerta con llave
    resultado = verificar(salas, 1, 2, "k", [("k", 1, None)])
    assert resultado.orden == ["k"]
    assert resultado.resoluble is False


def test_la_misma_llave_listada_dos_veces_cuenta_en_la_sala_de_menor_id():
    """FR-002 · solo cuenta la entrada con la menor sala"""
    salas = cripta(3, [(1, 2, "k"), (2, 3, None)])
    # la sala 3 solo se alcanza con k; la entrada de la sala 1 es la de menor id: se toma y se llega a la 3
    assert verificar(salas, 1, 3, "k", [("k", 3, None), ("k", 1, None)]).orden == ["k"]
    # con la entrada de la sala 3 sola, k queda detrás de su propia puerta
    assert verificar(salas, 1, 3, "k", [("k", 3, None)]).orden == []
    # la lista lleva las dos: gana la sala 1 (menor id) y la otra se ignora, en cualquier orden
    assert verificar(salas, 1, 3, "k", [("k", 1, None), ("k", 3, None)]).orden == ["k"]


def test_aleatorio_200_criptas_contra_el_oraculo():
    """FR-008, FR-009, FR-010, FR-011 · la verificación y el oráculo coinciden en el veredicto y en el orden"""
    for semilla in range(200):
        salas, inicial, salida, llave_salida, llaves = cripta_aleatoria_con_llaves(semilla, 4 + semilla % 17, 1 + semilla % 7)
        resultado = verificar(salas, inicial, salida, llave_salida, llaves)
        ref = resolver_referencia(salas, inicial, salida, llave_salida, llaves)
        assert (resultado.resoluble, resultado.orden) == (ref.resoluble, ref.orden), semilla
