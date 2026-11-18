from tests.mapas_solvabilidad import cripta, resolver_referencia


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
