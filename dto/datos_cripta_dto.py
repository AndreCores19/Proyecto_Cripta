from dto.sala_dto import SalaDTO


class EstadisticasJugadorDTO:
    def __init__(self,vida_max,ataque, defensa, velocidad):
        self.vida_max = vida_max
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad

    @classmethod
    def desde_json(cls, datos):
        return cls(
            vida_max=datos["vida_max"],
            ataque=datos["ataque"],
            defensa=datos["defensa"],
            velocidad=datos["velocidad"]
        )

class DatosCriptaDTO:
    def __init__(self, id_cripta, version, salas_total, paginas,
                 salas_por_pagina, sala_inicial, sala_salida,
                 llave_salida, presupuesto_solicitudes, inventario_max, jugador):
        self.id_cripta = id_cripta
        self.version = version
        self.salas_total = salas_total
        self.paginas = paginas
        self.salas_por_pagina = salas_por_pagina
        self.sala_inicial = sala_inicial
        self.sala_salida = sala_salida
        self.llave_salida = llave_salida
        self.presupuesto_solicitudes = presupuesto_solicitudes
        self.inventario_max = inventario_max
        self.jugador = jugador

    @classmethod
    def desde_json(cls, datos):
        return cls(
            id_cripta=datos["id"],
            version=datos["version"],
            salas_total=datos["salas_total"],
            paginas=datos["paginas"],
            salas_por_pagina=datos["salas_por_pagina"],
            sala_inicial=datos["sala_inicial"],
            sala_salida=datos["sala_salida"],
            llave_salida=datos["llave_salida"],
            presupuesto_solicitudes=datos["presupuesto_solicitudes"],
            inventario_max=datos["inventario_max"],
            jugador=EstadisticasJugadorDTO.desde_json(datos["jugador"])
        )
# probando la rama