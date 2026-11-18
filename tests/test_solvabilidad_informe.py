from dto.llave_dto import LlaveUbicacionDTO
from model.solvabilidad_logica import Verificador
from tests.mapas_solvabilidad import armar_vector, cripta, logicas, resolver_referencia, resumen


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
