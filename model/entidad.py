
class Entidad:
    def __init__(self, nombre, vida, vida_max, ataque, defensa, velocidad, sala):
        self.nombre = nombre
        self.vida = vida
        self.vida_max = vida_max
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.sala = sala
        self.evento = None

    def esta_vivo(self):
        return self.vida > 0

    def recibir_dano(self, cantidad):
        self.vida = max(0, self.vida - cantidad)

    def curar(self, cantidad):
        self.vida = min(self.vida_max, self.vida + cantidad)