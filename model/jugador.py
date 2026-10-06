from model.entidad import Entidad
 
 
class Jugador(Entidad):
    def __init__(self, vida_max, ataque, defensa, velocidad, sala):
        super().__init__("Jugador", vida_max, vida_max, ataque, defensa, velocidad, sala)
        self.llaves = set()