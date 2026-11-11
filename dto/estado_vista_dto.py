"""DTO de la vista de sala (FR-010). Clases simples y listas simples; no importa nada de model/."""


class JugadorVistaDTO:
    def __init__(self, nombre, vida, vida_max, ataque, defensa, velocidad, arma, armadura, efectos):
        self.nombre = nombre
        self.vida = vida
        self.vida_max = vida_max
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.arma = arma                # nombre o None
        self.armadura = armadura        # nombre o None
        self.efectos = efectos          # lista de str (tipo)


class SalidaVistaDTO:
    def __init__(self, direccion, nombre_destino, cerrada, costo):
        self.direccion = direccion
        self.nombre_destino = nombre_destino
        self.cerrada = cerrada
        self.costo = costo              # int ya resuelto: declarado o 100


class EnemigoVistaDTO:
    def __init__(self, nombre, id_enemigo, vida, vida_max, efectos):
        self.nombre = nombre
        self.id_enemigo = id_enemigo
        self.vida = vida
        self.vida_max = vida_max
        self.efectos = efectos


class TrampaVistaDTO:
    def __init__(self, nombre, dano, armada):
        self.nombre = nombre
        self.dano = dano
        self.armada = armada


class ObjetoVistaDTO:
    def __init__(self, id_instancia, nombre):
        self.id_instancia = id_instancia
        self.nombre = nombre


class EstadoVistaDTO:
    def __init__(self, id_sala, nombre_sala, reloj, jugador, salidas, enemigos,
                 trampas, objetos, bitacora):
        self.id_sala = id_sala
        self.nombre_sala = nombre_sala
        self.reloj = reloj
        self.jugador = jugador
        self.salidas = salidas
        self.enemigos = enemigos
        self.trampas = trampas
        self.objetos = objetos
        self.bitacora = bitacora
