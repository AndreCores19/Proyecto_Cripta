
class InstanciaTrampaDTO:
    def __init__(self, instancia, tipo):
        self.instancia = instancia
        self.tipo = tipo

    @classmethod
    def desde_json(cls, datos):
        return cls(
            instancia=datos["instancia"],
            tipo=datos["tipo"]
        )

class InstanciaEnemigoDTO:
    def __init__(self, instancia, tipo, vida):
        self.instancia = instancia
        self.tipo = tipo
        self.vida = vida

    @classmethod
    def desde_json(cls, datos):
        return cls(
            instancia=datos["instancia"],
            tipo=datos["tipo"],
            vida=datos.get("vida"),
        )

class ContenidoSalaDTO:
    def __init__(self, id_sala, enemigos, objetos, trampas):
        self.id_sala = id_sala
        self.enemigos = enemigos
        self.objetos = objetos
        self.trampas = trampas


    @classmethod
    def desde_json(cls, datos):
        enemigos = [InstanciaEnemigoDTO.desde_json(enemigo) for enemigo in datos.get("enemigos", [])]
        trampas = [InstanciaTrampaDTO.desde_json(trampa) for trampa in datos.get("trampas", [])]
        return cls(enemigos=enemigos, trampas=trampas, objetos=list(datos.get("objetos", [])), id_sala=datos["sala"])

