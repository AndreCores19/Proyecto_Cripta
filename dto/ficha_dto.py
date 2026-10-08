class FichaDTO:
    def __init__(self, id_ficha, nombre, descripcion):
        self.id_ficha = id_ficha
        self.nombre = nombre
        self.descripcion = descripcion


class FichaEnemigoDTO(FichaDTO):
    def __init__(self, id_ficha, nombre, descripcion, vida_max, ataque, defensa, velocidad, comportamiento, suelta = []):
        super().__init__(id_ficha, nombre, descripcion)
        self.vida_max = vida_max
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.comportamiento = comportamiento
        self.suelta = suelta

    @classmethod
    def desde_json(cls, datos):
        return cls(
            ...
        )