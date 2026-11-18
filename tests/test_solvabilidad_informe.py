from dto.llave_dto import LlaveUbicacionDTO
from model.solvabilidad_logica import Verificador
from tests.mapas_solvabilidad import (armar_vector, barajar, cadena_de_llaves, cripta, cripta_aleatoria_con_llaves,
                                      logicas, resolver_referencia, resumen)


def verificar(salas, inicial, salida, llave_salida, llaves):
    """Corre la verificación con llaves nuevas (cada llamada arma las suyas)."""
    return Verificador().verificar(armar_vector(salas), inicial, salida, llave_salida, logicas(llaves))


def test_llave_que_suelta_un_enemigo_errante_se_ubica_en_su_sala_inicial():
    """FR-003 · US4-1 (escenario 2 del encargo)"""
    # la llave k abre la puerta 2-3 y la lleva un enemigo que empieza en la sala 1 (puede andar por donde quiera después)
    salas = cripta(3, [(1, 2, None), (2, 3, "k")])
    llaves = [("k", 1, "e-errante")]
    resultado = verificar(salas, 1, 3, "k", llaves)
    assert resultado.resoluble is True
    assert resultado.orden == ["k"]
    ref = resolver_referencia(salas, 1, 3, "k", llaves)
    assert (resultado.resoluble, resultado.orden) == (ref.resoluble, ref.orden)


def test_la_ubicacion_de_la_llave_no_la_mueve_el_enemigo():
    """FR-003 · US4-1: el enemigo no se simula; si su sala inicial no se alcanza, la llave no se obtiene"""
    salas = cripta(3, [(1, 2, "j"), (2, 3, "k")])
    llaves = [("k", 2, "e-errante"), ("j", 3, None)]          # j (sala 3) y k (sala 2) se esperan una a la otra
    resultado = verificar(salas, 1, 3, "k", llaves)
    assert resultado.resoluble is False
    assert resultado.orden == []


def test_dto_de_llave_conserva_el_enemigo_y_sin_enemigo_es_none():
    """FR-002, FR-003 · US4-1"""
    con = LlaveUbicacionDTO.desde_json({"id": "llave-x", "sala": 16, "enemigo": "enemigo-y"})
    assert (con.id_llave, con.id_sala, con.id_enemigo) == ("llave-x", 16, "enemigo-y")
    sin = LlaveUbicacionDTO.desde_json({"id": "llave-z", "sala": 2})
    assert (sin.id_llave, sin.id_sala, sin.id_enemigo) == ("llave-z", 2, None)


def _dir(salas, id_sala, indice=0):
    """Dirección de la salida `indice` de una sala (las asigna el constructor de criptas)."""
    return salas[id_sala - 1].salidas[indice].direccion


def test_la_llave_de_salida_tras_su_unica_puerta_no_es_resoluble_y_el_ciclo_es_de_largo_uno():
    """FR-008, FR-012 · US3-1 (escenario 1 del encargo)"""
    salas = cripta(2, [(1, 2, "k")])
    llaves = [("k", 2, None)]
    resultado = verificar(salas, 1, 2, "k", llaves)
    assert resultado.resoluble is False
    ref = resumen(resultado)
    assert ref.inalcanzables == [("k", 2, None)]
    assert ref.frontera == [(1, _dir(salas, 1), 2, "k")]
    assert ref.ciclos == [[("k", 2, "k", (1, _dir(salas, 1), 2))]]


def _dos_llaves_que_se_esperan():
    """1-2 abierta; 2-3 con kb; 2-4 con ka; ka está en la sala 5 (tras 3) y kb en la 6 (tras 4)."""
    salas = cripta(6, [(1, 2, None), (2, 3, "kb"), (2, 4, "ka"), (3, 5, None), (4, 6, None)])
    return salas, 1, 5, "ka", [("ka", 5, None), ("kb", 6, "enemigo-y")]


def test_el_informe_lista_las_llaves_las_puertas_de_la_frontera_y_donde_estan():
    """FR-012 · US3-2"""
    salas, inicial, salida, llave_salida, llaves = _dos_llaves_que_se_esperan()
    resultado = verificar(salas, inicial, salida, llave_salida, llaves)
    assert resultado.resoluble is False
    ref = resumen(resultado)
    assert ref.inalcanzables == [("ka", 5, None), ("kb", 6, "enemigo-y")]            # por id, con su ubicación
    d_kb = salas[1].salidas[1].direccion
    d_ka = salas[1].salidas[2].direccion
    assert ref.frontera == sorted([(2, d_kb, 3, "kb"), (2, d_ka, 4, "ka")], key=lambda x: (x[0], x[1]))
    assert ref.frontera == resolver_referencia(salas, inicial, salida, llave_salida, llaves).frontera


def _anillo_de_tres():
    """1 con tres puertas: k1 abre 1-2, k2 abre 1-3, k3 abre 1-4; k1 está en la sala 3, k2 en la 4 y k3 en la 2."""
    salas = cripta(4, [(1, 2, "k1"), (1, 3, "k2"), (1, 4, "k3")])
    return salas, 1, 2, "k1", [("k1", 3, None), ("k2", 4, None), ("k3", 2, None)]


def test_un_anillo_de_tres_llaves_da_el_ciclo_desde_su_llave_de_menor_id_igual_en_dos_corridas():
    """FR-012, FR-010 · US3-3"""
    salas, inicial, salida, llave_salida, llaves = _anillo_de_tres()
    primero = resumen(verificar(salas, inicial, salida, llave_salida, llaves))
    assert [[e[0] for e in ciclo] for ciclo in primero.ciclos] == [["k1", "k2", "k3"]]
    assert [e[2] for e in primero.ciclos[0]] == ["k2", "k3", "k1"]               # cada llave y su guardiana
    segundo = resumen(verificar(salas, inicial, salida, llave_salida, llaves))
    assert segundo.ciclos == primero.ciclos
    for semilla in range(5):
        barajadas = barajar(salas, llaves, semilla)
        assert resumen(verificar(salas, inicial, salida, llave_salida, barajadas)).ciclos == primero.ciclos


def test_varios_ciclos_independientes_se_informan_todos_cada_uno_desde_su_menor_id_y_ordenados():
    """FR-012 · cada ciclo, una vez"""
    salas = cripta(5, [(1, 2, "b"), (1, 3, "a"), (1, 4, "d"), (1, 5, "c")])
    llaves = [("b", 2, None), ("a", 3, None), ("d", 4, None), ("c", 5, None)]
    ref = resumen(verificar(salas, 1, 2, "b", llaves))
    assert [[e[0] for e in ciclo] for ciclo in ref.ciclos] == [["a"], ["b"], ["c"], ["d"]]
    assert ref.ciclos == resolver_referencia(salas, 1, 2, "b", llaves).ciclos


def test_una_sala_que_alcanzan_dos_llaves_de_la_frontera_tiene_por_guardiana_la_de_menor_id():
    """FR-012 (d), plan R5 · el desempate es la menor llave"""
    salas = cripta(4, [(1, 2, "kb"), (1, 3, "ka"), (2, 4, None), (3, 4, None)])
    llaves = [("ka", 4, None), ("kb", 4, None)]
    ref = resumen(verificar(salas, 1, 2, "ka", llaves))
    assert [[(e[0], e[2]) for e in ciclo] for ciclo in ref.ciclos] == [[("ka", "ka")]]
    assert ref.ciclos[0][0][3][2] == 3                                  # la puerta de ka lleva a la sala 3


def test_una_llave_cuya_sala_no_se_puede_alcanzar_ni_ignorando_cerraduras_no_tiene_guardiana_ni_ciclo():
    """FR-012 · sala suelta, sin salidas"""
    salas = cripta(3, [(1, 2, None)])                                   # la sala 3 no tiene ninguna salida
    ref = resumen(verificar(salas, 1, 2, "q", [("q", 3, None)]))
    assert ref.inalcanzables == [("q", 3, None)]
    assert ref.ciclos == []


def test_puerta_cerrada_con_llave_ausente_de_la_lista_o_sin_llave_va_a_la_frontera_con_ubicacion_desconocida():
    """FR-012 · una puerta que nadie puede abrir; sin inundación, así que sin guardiana"""
    salas = cripta(4, [(1, 2, "fantasma"), (1, 3, None), (1, 4, None)])
    for s in salas[0].salidas:
        if s.destino is salas[2]:
            s.cerrada = True                                              # cerrada y sin llave
            s.opuesta.cerrada = True
    resultado = verificar(salas, 1, 2, "fantasma", [])
    ref = resumen(resultado)
    assert resultado.resoluble is False
    assert ("fantasma", None, None) in ref.inalcanzables                  # nombrada por la puerta, ubicación desconocida
    assert sorted(str(x[3]) for x in ref.frontera) == ["None", "fantasma"]
    assert ref.ciclos == []


def test_la_llave_de_salida_ausente_de_la_lista_no_es_resoluble_y_se_informa_sin_ubicacion():
    """FR-012 · la llave de salida que la lista no da"""
    salas = cripta(2, [(1, 2, "zz")])
    ref = resumen(verificar(salas, 1, 2, "zz", []))
    assert ref.resoluble is False
    assert ref.inalcanzables == [("zz", None, None)]


def test_llave_de_enemigo_en_una_sala_inalcanzable_no_se_obtiene_y_se_informa_con_su_enemigo():
    """FR-003, FR-012 · US4-2"""
    salas = cripta(3, [(1, 2, None), (2, 3, "k")])
    llaves = [("k", 3, "e9")]
    ref = resumen(verificar(salas, 1, 3, "k", llaves))
    assert ref.resoluble is False
    assert ref.inalcanzables == [("k", 3, "e9")]
    assert ref.ciclos == [[("k", 3, "k", (2, _dir(salas, 2, 1), 3))]]


def test_una_sola_pasada_las_salas_y_salidas_visitadas_no_crecen_con_el_numero_de_llaves():
    """FR-013, FR-019 · US3-4"""
    for k in (10, 100, 1000):
        salas, inicial, salida, llave_salida, llaves = cadena_de_llaves(k)
        resultado = verificar(salas, inicial, salida, llave_salida, llaves)
        assert resultado.resoluble is True
        assert resultado.visitas_salas == len(salas)                      # cada sala se visita una vez
        assert resultado.examenes_salidas == sum(len(sala.salidas) for sala in salas)   # cada salida, una vez


def test_aleatorio_200_criptas_todas_las_listas_del_informe_coinciden_con_el_oraculo():
    """FR-012, FR-013 · inalcanzables, frontera y ciclos"""
    for semilla in range(200):
        salas, inicial, salida, llave_salida, llaves = cripta_aleatoria_con_llaves(
            semilla, 4 + semilla % 17, 1 + semilla % 7)
        ref = resolver_referencia(salas, inicial, salida, llave_salida, llaves)
        obtenido = resumen(verificar(salas, inicial, salida, llave_salida, llaves))
        assert obtenido.resoluble == ref.resoluble, semilla
        assert obtenido.orden == ref.orden, semilla
        assert obtenido.inalcanzables == ref.inalcanzables, semilla
        assert obtenido.frontera == ref.frontera, semilla
        assert obtenido.ciclos == ref.ciclos, semilla


def test_una_puerta_con_llave_ausente_entre_salas_ya_alcanzadas_no_es_frontera_ni_se_informa():
    """FR-012 · solo cuentan las puertas de la frontera bloqueada"""
    salas = cripta(3, [(1, 2, None), (1, 3, None), (2, 3, "fantasma")])
    resultado = verificar(salas, 1, 3, "k", [("k", 1, None)])
    ref = resumen(resultado)
    assert ref.frontera == []
    assert ref.inalcanzables == []
