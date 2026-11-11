from model.entidad_logica import Entidad

class Enemigo(Entidad):
    def __init__(self, id_enemigo, tipo, nombre, vida, vida_max, ataque, defensa, velocidad, comportamiento, sala, suelta=None, rango=0):
        super().__init__(nombre, vida, vida_max, ataque, defensa, velocidad, sala)
        self.id_enemigo = id_enemigo
        self.tipo = tipo
        self.comportamiento = comportamiento
        self.regeneracion = 0
        self.suelta = list(suelta) if suelta is not None else []
        self.rango = rango

    def es_cazador(self):
        return self.comportamiento == "cazador"
