from dto.reporte_verificacion_dto import (EslabonCicloDTO, PuertaFronteraDTO, ReporteVerificacionDTO,
                                          UbicacionLlaveDTO)
from model.solvabilidad_logica import LlaveLogica, Verificador


class VerificacionService:
    """Verifica si una cripta se puede ganar (FR-008) y arma el reporte como DTO.

    Trabaja sobre el repositorio de cripta que se le da: el juego le da el suyo, cuyo esqueleto ya se bajó,
    así que la verificación nunca vuelve a bajarlo. No lee el conocimiento del jugador (FR-001).
    """

    def __init__(self, repo_cripta, repo_llaves):
        self.repo_cripta = repo_cripta
        self.repo_llaves = repo_llaves

    def verificar(self):
        datos = self.repo_cripta.datos
        fuente = self.repo_llaves.fuente
        antes = fuente.solicitudes_realizadas()
        dtos = self.repo_llaves.cargar(datos.id_cripta, datos.version)
        llaves = [LlaveLogica(d.id_llave, d.id_sala, d.id_enemigo) for d in dtos]
        resultado = Verificador().verificar(self.repo_cripta.salas, datos.sala_inicial, datos.sala_salida,
                                            datos.llave_salida, llaves)
        solicitudes = fuente.solicitudes_realizadas() - antes
        if resultado.resoluble:
            return ReporteVerificacionDTO(datos.id_cripta, True, list(resultado.orden), [], [], [], solicitudes)
        inalcanzables = [UbicacionLlaveDTO(k.id, k.id_sala, k.id_enemigo) for k in resultado.inalcanzables]
        frontera = [self._puerta(s) for s in resultado.frontera]
        ciclos = [[EslabonCicloDTO(e.id_llave, e.id_sala, e.id_guardia, self._puerta(e.puerta)) for e in ciclo]
                  for ciclo in resultado.ciclos]
        return ReporteVerificacionDTO(datos.id_cripta, False, list(resultado.orden), inalcanzables, frontera,
                                      ciclos, solicitudes)

    @staticmethod
    def _puerta(salida):
        return PuertaFronteraDTO(salida.origen.id, salida.destino.id, salida.direccion, salida.llave)
