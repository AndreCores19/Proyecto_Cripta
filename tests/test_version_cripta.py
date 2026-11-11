"""US5 · Los costos de salida siempre están al día; guardados y logs viejos se rechazan por versión.

Solo se prueba el comportamiento que ya existía (FR-011, FR-012): no hay un
mecanismo nuevo de invalidación. Todo se hace con dobles de prueba y sin red.

Resultado de T026 (revisión de código, FR-011, FR-012)
------------------------------------------------------
Ninguna ruta de código escribe costos de salida en guardados, logs ni en el
caché del catálogo:

- adapters/guardado_binario.py: el guardado solo escribe la cabecera
  (id_cripta, version_cripta, version_catalogo, semilla), el contenido de las
  salas (enemigos, objetos, trampas) y los comandos. No recibe salas ni
  salidas, y la palabra "costo" no aparece en el archivo.
- adapters/bitacora_partida.py: el log solo escribe la línea de formato, la
  cripta, las dos versiones, la semilla y los comandos. Sin "costo".
- adapters/almacen_fichas.py: el caché guarda fichas del catálogo
  (enemigos, objetos, trampas) y version.txt. Los costos son de las salidas de
  la cripta, que no pasan por este caché.
- Búsqueda de "costo" en adapters/: sin coincidencias. Esta feature no
  modificó ningún archivo de adapters/ (git diff desde el primer commit de la
  feature, b82edfa^, vacío para adapters/).
- VERSION_FORMATO sigue en 1 en guardado_binario.py y en bitacora_partida.py,
  sin cambios.

Los costos viven solo en el esqueleto de la cripta (SalidaDTO.costo), que se
descarga al iniciar y se vuelve a enlazar con construir_salas.
"""
from adapters.guardado_binario import CabeceraGuardado, GuardadoBinario
from aplicacion import Aplicacion
from data.repositorio_cripta import RepositorioCripta


class FuenteFalsa:
    """Fuente en memoria: una cripta de dos salas cuya puerta E/O declara costo."""

    def __init__(self, version="v1", costo=300):
        self.version = version
        self.costo = costo
        self.paginas_pedidas = []
        self.presupuesto = None

    def asignar_presupuesto(self, n):
        self.presupuesto = n

    def datos_cripta(self, id_cripta):
        return {
            "id": id_cripta, "version": self.version, "salas_total": 2,
            "paginas": 1, "salas_por_pagina": 2, "sala_inicial": 1,
            "sala_salida": 2, "llave_salida": "llave", "presupuesto_solicitudes": 50,
            "inventario_max": 5,
            "jugador": {"vida_max": 10, "ataque": 1, "defensa": 1, "velocidad": 1},
        }

    def pagina_esqueleto(self, id_cripta, pagina):
        self.paginas_pedidas.append(pagina)
        return {"salas": [
            {"id": 1, "nombre": "A", "salidas": {"E": {"sala": 2, "costo": self.costo}}},
            {"id": 2, "nombre": "B", "salidas": {"O": {"sala": 1}}},
        ]}


class CatalogoFalso:
    def __init__(self, version):
        self._version = version

    def version(self):
        return self._version


class AppFalsa:
    def __init__(self, repo, version_catalogo="cat1"):
        self.repo_cripta = repo
        self.repo_catalogo = CatalogoFalso(version_catalogo)


class LectorFalso:
    def __init__(self, version_cripta, version_catalogo):
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo


def _repo_cargado(fuente):
    repo = RepositorioCripta(fuente)
    dtos = repo.cargar_esqueleto("c1")
    repo.construir_salas(dtos)
    return repo, dtos


def _guardar(ruta, version_cripta, version_catalogo="cat1"):
    cabecera = CabeceraGuardado("c1", version_cripta, version_catalogo, 7)
    GuardadoBinario().guardar(ruta, cabecera, [], [])


def test_costos_del_esqueleto_llegan_a_las_salas():
    """FR-011 · US5-1: las salas salen con los costos del esqueleto descargado."""
    fuente = FuenteFalsa(costo=300)
    repo, _ = _repo_cargado(fuente)
    assert fuente.paginas_pedidas == [1]
    assert repo.salas.buscar(1).salida("E").costo == 300
    assert repo.salas.buscar(2).salida("O").costo == 300


def test_guardado_de_otra_version_de_cripta_se_rechaza(tmp_path):
    """FR-012 · US5-2: version_cripta distinta → mensaje de otra cripta o versión."""
    repo, _ = _repo_cargado(FuenteFalsa(version="v2"))
    ruta = tmp_path / "viejo.sav"
    _guardar(ruta, "v1")
    mensaje = Aplicacion.validar_guardado(AppFalsa(repo), ruta)
    assert mensaje == "No se puede cargar: la partida es de otra cripta o versión."


def test_log_de_otra_version_de_cripta_no_coincide():
    """FR-012 · US5-3: un lector con otra version_cripta no coincide."""
    repo, _ = _repo_cargado(FuenteFalsa(version="v2"))
    app = AppFalsa(repo)
    assert Aplicacion._versiones_coinciden(app, LectorFalso("v1", "cat1")) is False
    assert Aplicacion._versiones_coinciden(app, LectorFalso("v2", "cat1")) is True


def test_recarga_de_salas_conserva_costos_y_acepta_guardado_vigente(tmp_path):
    """FR-011, FR-012 · US5-4: reconstruir desde los mismos DTOs da los mismos costos."""
    fuente = FuenteFalsa(costo=300)
    repo, dtos = _repo_cargado(fuente)
    repo.construir_salas(dtos)      # lo que hace _reiniciar_salas al cargar un guardado
    assert repo.salas.buscar(1).salida("E").costo == 300
    assert repo.salas.buscar(2).salida("O").costo == 300
    assert fuente.paginas_pedidas == [1]    # no se volvió a pedir el esqueleto

    ruta = tmp_path / "vigente.sav"
    _guardar(ruta, "v1")
    assert Aplicacion.validar_guardado(AppFalsa(repo), ruta) is None
