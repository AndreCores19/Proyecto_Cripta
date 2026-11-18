"""DTO del mapa conocido (FR-015). Solo valores simples y listas; no importa nada de model/."""


class SalidaConocidaDTO:
    def __init__(self, direccion, id_destino, nombre_destino, costo, puerta):
        self.direccion = direccion
        self.id_destino = id_destino            # None si la sala destino solo está avistada
        self.nombre_destino = nombre_destino    # None si la sala destino solo está avistada
        self.costo = costo
        self.puerta = puerta                    # "abierta", "cerrada" o "sin observar"


class SalaConocidaDTO:
    def __init__(self, id_sala, nombre, salidas):
        self.id_sala = id_sala
        self.nombre = nombre
        self.salidas = salidas                  # lista de SalidaConocidaDTO


class MapaVistaDTO:
    def __init__(self, id_sala_actual, salas):
        self.id_sala_actual = id_sala_actual
        self.salas = salas                      # salas exploradas, ordenadas por id
