import random
from structures.agenda import AgendaEventos
from structures.bitacora import Bitacora
from model.tiempo import intervalo, COSTO_ESPERAR, COSTO_ATACAR, COSTO_MOVER
 
 
class Partida:
    def __init__(self, jugador, semilla):
        self.reloj = 0
        self.agenda = AgendaEventos()
        self.azar = random.Random(semilla)
        self.jugador = jugador
        self.enemigos = []
        self.enemigos_derrotados = 0
        self.terminada = False
        self.bitacora = Bitacora()
        jugador.evento = self.agenda.programar(0, "accion", jugador)
        self._entrar_en_sala(jugador.sala)
 
    def _entrar_en_sala(self, sala):
        sala.rastro = self.reloj
        for e in sala.inactivos:
            self.activar_enemigo(e)
        sala.inactivos = []
 
    def mover(self, direccion):
        salida = self.jugador.sala.salida(direccion)
        if salida is None or salida.cerrada:
            return False
        self.jugador.sala.rastro = self.reloj
        self.jugador.sala = salida.destino
        self._entrar_en_sala(salida.destino)
        self._programar_siguiente(self.jugador, COSTO_MOVER)
        self.avanzar_hasta_jugador()
        return True
 
    def activar_enemigo(self, enemigo):
        self.enemigos.append(enemigo)
        self._programar_siguiente(enemigo, COSTO_ESPERAR)
 
    def _programar_siguiente(self, actor, costo):
        tiempo = self.reloj + intervalo(costo, actor.velocidad)
        actor.evento = self.agenda.programar(tiempo, "accion", actor)
 
    def _calcular_dano(self, atacante, defensor):
        return max(1, atacante.ataque + self.azar.randint(0, 4) - defensor.defensa)
 
    def avanzar_hasta_jugador(self):
        while not self.terminada:
            ev = self.agenda.extraer()
            self.reloj = ev.tiempo
            if ev.dueno is self.jugador:
                return
            self._actuar_enemigo(ev.dueno)
 
    def _actuar_enemigo(self, enemigo):
        if enemigo.sala == self.jugador.sala:
            dano = self._calcular_dano(enemigo, self.jugador)
            self.jugador.recibir_dano(dano)
            self.bitacora.agregar(
                f"t={self.reloj}: {enemigo.nombre} ataca. Daño {dano}. Vida jugador: {self.jugador.vida}"
            )
            if not self.jugador.esta_vivo():
                self.terminada = True
                self.bitacora.agregar(f"t={self.reloj}: el jugador ha muerto.")
                return
            self._programar_siguiente(enemigo, COSTO_ATACAR)
        else:
            self.bitacora.agregar(f"t={self.reloj}: {enemigo.nombre} espera")
            self._programar_siguiente(enemigo, COSTO_ESPERAR)
 
    def atacar(self, enemigo):
        if enemigo.sala != self.jugador.sala:
            return False
        dano = self._calcular_dano(self.jugador, enemigo)
        enemigo.recibir_dano(dano)
        self.bitacora.agregar(
            f"t={self.reloj}: Jugador ataca a {enemigo.nombre}. Daño {dano}. Vida enemigo: {enemigo.vida}"
        )
        if not enemigo.esta_vivo():
            self.agenda.cancelar(enemigo.evento)
            self.enemigos.remove(enemigo)
            self.enemigos_derrotados += 1
            self.bitacora.agregar(f"t={self.reloj}: {enemigo.nombre} muere")
        self._programar_siguiente(self.jugador, COSTO_ATACAR)
        self.avanzar_hasta_jugador()
        return True
 
    def esperar_jugador(self):
        self._programar_siguiente(self.jugador, COSTO_ESPERAR)
        self.avanzar_hasta_jugador()
 