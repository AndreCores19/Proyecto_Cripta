class ObjetoInventarioDTO:
    """Un objeto del inventario tal como lo muestra la vista (FR-010, FR-014)."""

    def __init__(self, id_instancia, nombre, peso, valor, equipado, actual):
        self.id_instancia = id_instancia
        self.nombre = nombre
        self.peso = peso
        self.valor = valor
        self.equipado = equipado
        self.actual = actual


class InventarioVistaDTO:
    def __init__(self, tamano, capacidad_max, objetos):
        self.tamano = tamano
        self.capacidad_max = capacidad_max
        self.objetos = objetos
