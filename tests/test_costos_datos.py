"""Costos de salida desde los datos: lectura del DTO y enlace en el repositorio."""
import pytest

from data.repositorio_cripta import RepositorioCripta
from dto.sala_dto import SalaDTO
from dto.salida_dto import SalidaDTO


def _construir(salidas_a, salidas_b):
    repo = RepositorioCripta(fuente=None)
    repo.construir_salas([SalaDTO(1, "A", salidas_a), SalaDTO(2, "B", salidas_b)])
    return repo.salas.buscar(1), repo.salas.buscar(2)


def test_salida_dto_lee_el_costo_declarado():
    """FR-001 · el costo del JSON llega al DTO."""
    dto = SalidaDTO.desde_json("N", {"sala": 2, "costo": 300})
    assert dto.costo == 300


def test_salida_dto_sin_costo_queda_none():
    """FR-001, FR-002 · sin costo en el JSON el DTO guarda None, no 100."""
    dto = SalidaDTO.desde_json("N", {"sala": 2})
    assert dto.costo is None


def test_costo_declarado_en_un_solo_lado_llega_a_las_dos_salidas():
    """FR-005 · US1-7 al cargar: A→B declara 300 y B→A nada → las dos cuestan 300."""
    a, b = _construir([SalidaDTO("E", 2, costo=300)], [SalidaDTO("O", 1)])
    assert a.salida("E").costo == 300
    assert b.salida("O").costo == 300


def test_costos_distintos_en_los_dos_lados_son_puerta_inconsistente():
    """FR-013 · US1-6: un lado declara 100 y el otro 200 → ValueError."""
    with pytest.raises(ValueError, match="Puerta inconsistente") as error:
        _construir([SalidaDTO("E", 2, costo=100)], [SalidaDTO("O", 1, costo=200)])
    mensaje = str(error.value)
    for parte in ("sala 1", "sala 2", "salida E", "salida O", "100", "200"):
        assert parte in mensaje


def test_puerta_hacia_otra_sala_sigue_siendo_inconsistente():
    """FR-013 · el chequeo de la parte uno (salida opuesta a otra sala) se mantiene."""
    repo = RepositorioCripta(fuente=None)
    dtos = [
        SalaDTO(1, "A", [SalidaDTO("E", 2)]),
        SalaDTO(2, "B", [SalidaDTO("O", 3)]),
        SalaDTO(3, "C", []),
    ]
    with pytest.raises(ValueError, match="Puerta inconsistente"):
        repo.construir_salas(dtos)
