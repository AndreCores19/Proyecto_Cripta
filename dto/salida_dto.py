

class SalidaDTO:
    def __init__(self, direccion, id_destino, cerrada=False, llave=None, cierre_automatico=None, costo=None):
        self.direccion = direccion
        self.id_destino = id_destino
        self.cerrada = cerrada
        self.llave = llave
        self.cierre_automatico = cierre_automatico
        self.costo = costo      # None = no declarado. Sin chequeo de rango (FR-001)

    @classmethod
    def desde_json(cls, direccion, datos):
        return cls(
            direccion=direccion,
            id_destino=datos["sala"],
            cerrada=datos.get("cerrada", False),
            llave=datos.get("llave"),
            cierre_automatico=datos.get("cierre_automatico"),
            costo=datos.get("costo"),
        )
