"""DTO de la ubicación de una llave (FR-002, FR-003). Valores simples; no importa nada de model/."""


class LlaveUbicacionDTO:
    def __init__(self, id_llave, id_sala, id_enemigo=None):
        self.id_llave = id_llave
        self.id_sala = id_sala              # sala donde está la llave; si la lleva un enemigo, la sala donde él empieza
        self.id_enemigo = id_enemigo        # None si la llave está en una sala

    @classmethod
    def desde_json(cls, datos):
        #«enemigo» no viene si la llave está en una sala
        return cls(datos["id"], datos["sala"], datos.get("enemigo"))
