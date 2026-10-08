from dto.salida_dto import SalidaDTO

class SalaDTO:
    def __init__(self, id_sala, nombre, salidas):
        self.id_sala = id_sala
        self.nombre = nombre
        self.salidas = salidas

    @classmethod
    def desde_json(cls, datos):
        salidas = []
        for direccion, salida_datos in datos.get("salidas", {}).items():
            salida = SalidaDTO.desde_json(direccion, salida_datos)
            salidas.append(salida)

        return cls(
            id_sala=datos["id"],
            nombre=datos["nombre"],
            salidas=salidas
        )




