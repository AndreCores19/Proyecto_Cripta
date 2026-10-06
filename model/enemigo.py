from model.entidad import Entidad
#hola

class Enemigo(Entidad):
    def __init__(self, id_enemigo, tipo, nombre, vida, vida_max, ataque, defensa,
                 velocidad, comportamiento, sala):
        super().__init__(nombre, vida, vida_max, ataque, defensa, velocidad, sala)
        self.id_enemigo = id_enemigo
        self.tipo = tipo
        self.comportamiento = comportamiento