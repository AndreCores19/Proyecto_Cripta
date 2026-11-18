"""DTO del reporte de verificación de una cripta (FR-012, FR-014). Valores simples y listas;
no importa nada de model/."""


class UbicacionLlaveDTO:
    def __init__(self, id_llave, id_sala, id_enemigo=None):
        self.id_llave = id_llave
        self.id_sala = id_sala              # None si la llave no está en la lista de llaves
        self.id_enemigo = id_enemigo        # None si no la lleva un enemigo


class PuertaFronteraDTO:
    def __init__(self, id_sala, id_destino, direccion, id_llave):
        self.id_sala = id_sala              # sala de origen, alcanzada
        self.id_destino = id_destino
        self.direccion = direccion
        self.id_llave = id_llave            # None si la salida no nombra ninguna llave


class EslabonCicloDTO:
    def __init__(self, id_llave, id_sala, id_llave_guardia, puerta):
        self.id_llave = id_llave
        self.id_sala = id_sala              # sala donde está esa llave
        self.id_llave_guardia = id_llave_guardia
        self.puerta = puerta                # PuertaFronteraDTO que la guarda


class ReporteVerificacionDTO:
    def __init__(self, id_cripta, resoluble, orden, llaves_inalcanzables, puertas_frontera,
                 ciclos, solicitudes):
        self.id_cripta = id_cripta
        self.resoluble = resoluble
        self.orden = orden                              # ids de llaves en el orden en que se toman
        # si es resoluble, estas tres listas están vacías
        self.llaves_inalcanzables = llaves_inalcanzables    # UbicacionLlaveDTO, ordenadas por id
        self.puertas_frontera = puertas_frontera            # PuertaFronteraDTO, por (id_sala, direccion)
        self.ciclos = ciclos                                # lista de listas de EslabonCicloDTO
        self.solicitudes = solicitudes                      # solicitudes que hizo la verificación (informativo)
