import random
from contextlib import contextmanager
from structures.agenda import AgendaEventos
from structures.bitacora import Bitacora
from structures.historial import Historial
from model.objeto_logica import PERGAMINO_RETROCESO
from model.tiempo_logica import (intervalo, COSTO_ESPERAR, COSTO_ATACAR, COSTO_ABRIR, COSTO_RECOGER, COSTO_SOLTAR, COSTO_EQUIPAR, COSTO_USAR)
from model.efectos_logica import Efectos

RASTRO_VIGENCIA = 400


class Partida:
    def __init__(self, jugador, semilla=None, sala_salida=None):
        if semilla is None:
            semilla = random.SystemRandom().randrange(2 ** 32)
        self.semilla = semilla
        self.reloj = 0
        self.historial = Historial(5)
        self.agenda = AgendaEventos(self.historial)
        self.azar = random.Random(semilla)
        self.jugador = jugador
        self.enemigos = []
        self.enemigos_derrotados = 0
        self.acciones_jugador = 0
        self.terminada = False
        self.victoria = False
        self.sala_salida = sala_salida
        self.abrio_puerta_salida = False
        self.bitacora = Bitacora()
        self.creador_objetos = None
        self.efectos = Efectos(self)
        jugador.inventario.historial = self.historial
        jugador.evento = self.agenda.programar(0, "accion", jugador)
        self._entrar_en_sala(jugador.sala)
        self.avanzar_hasta_jugador()

    #historial
    @contextmanager
    def _accion_jugador(self):
        with self.historial.accion():
            reloj = self.reloj
            num_sec = self.agenda.num_sec
            estado_azar = self.azar.getstate()
            self.historial.registrar(lambda: setattr(self, "reloj", reloj))
            self.historial.registrar(lambda: setattr(self.agenda, "num_sec", num_sec))
            self.historial.registrar(lambda: self.azar.setstate(estado_azar))
            yield

    def _sumar_accion(self):
        self.historial.asignar(self, "acciones_jugador", self.acciones_jugador + 1)

    def retroceder(self):
        if self.terminada or not self.historial.deshacer():
            return False
        self.bitacora.agregar(f"t={self.reloj}: retrocedes en el tiempo")
        return True

    #inventario
    def _quitar_del_suelo(self, sala, objeto):
        if objeto.clase == PERGAMINO_RETROCESO:
            sala.objetos.remove(objeto)        # excluido del historial (§2.11)
        else:
            self.historial.lista_quitar(sala.objetos, objeto)

    def _poner_en_suelo(self, sala, objeto):
        if objeto.clase == PERGAMINO_RETROCESO:
            sala.objetos.append(objeto)        # excluido del historial (§2.11)
        else:
            self.historial.lista_agregar(sala.objetos, objeto)

    def recoger(self, objeto):
        inv = self.jugador.inventario
        sala = self.jugador.sala
        if self.terminada or objeto not in sala.objetos or inv.esta_lleno():
            return False                         # no consume tiempo
        with self._accion_jugador():
            self._refrescar_rastro()
            self._sumar_accion()
            self._quitar_del_suelo(sala, objeto)
            inv.agregar(objeto)
            self.bitacora.agregar(f"t={self.reloj}: recoges {objeto.nombre}")
            self._programar_siguiente(self.jugador, COSTO_RECOGER)
            self.avanzar_hasta_jugador()
        return True

    def soltar(self):
        inv = self.jugador.inventario
        nodo = inv.actual
        if self.terminada or nodo is None:
            return False
        objeto = nodo.objeto
        with self._accion_jugador():
            self._refrescar_rastro()
            self._sumar_accion()
            inv.desequipar(objeto, self.jugador)   # un objeto soltado no puede seguir equipado
            inv.quitar_nodo(nodo)
            self._poner_en_suelo(self.jugador.sala, objeto)
            self.bitacora.agregar(f"t={self.reloj}: sueltas {objeto.nombre}")
            self._programar_siguiente(self.jugador, COSTO_SOLTAR)
            self.avanzar_hasta_jugador()
        return True

    def equipar(self):
        inv = self.jugador.inventario
        if self.terminada or not inv.puede_equipar_actual():
            return False
        objeto = inv.obtener_actual()
        with self._accion_jugador():
            self._refrescar_rastro()
            self._sumar_accion()
            inv.equipar_actual(self.jugador)
            self.bitacora.agregar(f"t={self.reloj}: equipas {objeto.nombre}")
            self._programar_siguiente(self.jugador, COSTO_EQUIPAR)
            self.avanzar_hasta_jugador()
        return True

    def usar(self):
        inv = self.jugador.inventario
        nodo = inv.actual
        if self.terminada or nodo is None:
            return False
        objeto = nodo.objeto
        if objeto.clase == PERGAMINO_RETROCESO:
            return self.usar_pergamino()
        if objeto.clase not in ("pocion", "antidoto", "antorcha"):
            return False
        with self._accion_jugador():
            self._refrescar_rastro()
            self._sumar_accion()
            if objeto.clase == "pocion":
                if objeto.cura:
                    self.historial.guardar(self.jugador, "vida")
                    self.jugador.curar(objeto.cura)
                if objeto.modificador_velocidad:
                    self.efectos.aplicar_velocidad(
                        self.jugador, objeto.modificador_velocidad, objeto.duracion)
            elif objeto.clase == "antidoto":
                self.efectos.cancelar_veneno(self.jugador)
            else:
                self.efectos.encender_antorcha(self.jugador, objeto.duracion)
            inv.quitar_nodo(nodo)
            self.bitacora.agregar(f"t={self.reloj}: usas {objeto.nombre}")
            self._programar_siguiente(self.jugador, COSTO_USAR)
            self.avanzar_hasta_jugador()
        return True

    def usar_pergamino(self):
        inv = self.jugador.inventario
        nodo = inv.actual
        if (self.terminada or nodo is None
                or nodo.objeto.clase != PERGAMINO_RETROCESO):
            return False
        if len(self.historial) == 0:
            self.bitacora.agregar(f"t={self.reloj}: no hay acciones que retroceder")
            return False                         # el pergamino no se gasta
        pergamino = nodo.objeto
        self.retroceder()
        inv.quitar_nodo(inv.nodo_de(pergamino))
        return True
    #salas
    def _entrar_en_sala(self, sala):
        self.historial.asignar(sala, "rastro", self.reloj)
        for e in sala.inactivos:
            self.activar_enemigo(e)
        self.historial.asignar(sala, "inactivos", [])

    def _refrescar_rastro(self):
        self.historial.asignar(self.jugador.sala, "rastro", self.reloj)

    def activar_enemigo(self, enemigo):
        self.historial.lista_agregar(self.enemigos, enemigo)
        self._programar_siguiente(enemigo, COSTO_ESPERAR)
        self.efectos.iniciar_regeneracion(enemigo)

    #acciones
    def mover(self, direccion):
        if self.terminada:
            return False
        salida = self.jugador.sala.salida(direccion)
        if salida is None or salida.cerrada:
            return False
        with self._accion_jugador():
            self._refrescar_rastro()
            self._sumar_accion()
            self.historial.asignar(self.jugador, "sala", salida.destino)
            self._entrar_en_sala(salida.destino)
            if self.efectos.activar_trampas(salida.destino):
                return True                      #el jugador se murió en una trampa
            if self._hay_victoria():
                self.terminada = True
                self.victoria = True
                self.bitacora.agregar(f"t={self.reloj}: el jugador llega a la salida. ¡Victoria!")
                return True
            self._programar_movimiento(self.jugador, salida)
            self.avanzar_hasta_jugador()
        return True

    def abrir_puerta(self, direccion):
        if self.terminada:
            return False
        salida = self.jugador.sala.salida(direccion)
        if salida is None or not salida.cerrada:
            return False
        if not self.jugador.tiene_llave(salida.llave):
            return False                         # sin llave: no consume tiempo
        with self._accion_jugador():
            self._refrescar_rastro()
            self._sumar_accion()
            self._poner_cerrada(salida, False)
            if self.sala_salida is not None and salida.destino is self.sala_salida:
                self.historial.asignar(self, "abrio_puerta_salida", True)
            self.bitacora.agregar(f"t={self.reloj}: se abre la puerta hacia {direccion}")
            if salida.cierre_automatico is not None:
                self.agenda.programar(self.reloj + salida.cierre_automatico,
                                      "cierre_puerta", None, salida)
            self._programar_siguiente(self.jugador, COSTO_ABRIR)
            self.avanzar_hasta_jugador()
        return True

    def _soltar_botin(self, enemigo):
        #Los objetos que suelta quedan en el suelo de la sala donde murio
        if self.creador_objetos is None:
            return
        for id_ficha in enemigo.suelta:
            objeto = self.creador_objetos(id_ficha)
            self.historial.lista_agregar(enemigo.sala.objetos, objeto)
            self.bitacora.agregar(f"t={self.reloj}: {enemigo.nombre} suelta {objeto.nombre}")

    def atacar(self, enemigo):
        if self.terminada or enemigo.sala != self.jugador.sala:
            return False
        with self._accion_jugador():
            self._refrescar_rastro()
            self._sumar_accion()
            dano = self._calcular_dano(self.jugador, enemigo)
            self.historial.guardar(enemigo, "vida")
            enemigo.recibir_dano(dano)
            self.bitacora.agregar(
                f"t={self.reloj}: Jugador ataca a {enemigo.nombre}. "
                f"Daño {dano}. Vida enemigo: {enemigo.vida}"
            )
            if not enemigo.esta_vivo():
                self.agenda.cancelar(enemigo.evento)
                self.historial.lista_quitar(self.enemigos, enemigo)
                self.efectos.cancelar_todos(enemigo)
                self.historial.asignar(self, "enemigos_derrotados",
                                       self.enemigos_derrotados + 1)
                self.bitacora.agregar(f"t={self.reloj}: {enemigo.nombre} muere")
                self._soltar_botin(enemigo)
            self._programar_siguiente(self.jugador, COSTO_ATACAR)
            self.avanzar_hasta_jugador()
        return True

    def esperar_jugador(self):
        if self.terminada:
            return False
        with self._accion_jugador():
            self._refrescar_rastro()
            self._sumar_accion()
            self._programar_siguiente(self.jugador, COSTO_ESPERAR)
            self.avanzar_hasta_jugador()
        return True

    #reloj
    def _programar_siguiente(self, actor, costo):
        tiempo = self.reloj + intervalo(costo, actor.velocidad)
        evento = self.agenda.programar(tiempo, "accion", actor)
        self.historial.asignar(actor, "evento", evento)

    def _programar_movimiento(self, actor, salida):
        #la siguiente acción de quien cruzó la salida tarda lo que cuesta esa salida
        self._programar_siguiente(actor, salida.costo)

    def _calcular_dano(self, atacante, defensor):
        return max(1, atacante.ataque + self.azar.randint(0, 4) - defensor.defensa)

    def _hay_victoria(self):
        return (self.sala_salida is not None
                and self.jugador.sala is self.sala_salida
                and self.abrio_puerta_salida)

    def avanzar_hasta_jugador(self):
        if not self.terminada and self.jugador.evento.pos < 0:
            raise RuntimeError("El jugador no tiene una acción programada")
        while not self.terminada:
            ev = self.agenda.extraer()
            if ev is None:
                break
            self.reloj = ev.tiempo
            if ev.tipo == "accion":
                if ev.dueno is self.jugador:
                    return
                self._actuar_enemigo(ev.dueno)
            elif ev.tipo == "cierre_puerta":
                self._cerrar_puerta(ev.datos)
            elif self.efectos.maneja(ev.tipo):
                self.efectos.ejecutar(ev)
            else:
                raise ValueError(f"Tipo de evento sin manejador: {ev.tipo}")

    def _poner_cerrada(self, salida, valor):
        #abre o cierra la puerta y su opuesta
        self.historial.asignar(salida, "cerrada", valor)
        if salida.opuesta is not None:
            self.historial.asignar(salida.opuesta, "cerrada", valor)

    def _cerrar_puerta(self, salida):
        self._poner_cerrada(salida, True)
        self.bitacora.agregar(f"t={self.reloj}: una puerta se cierra automáticamente")

    #enemigos
    def _actuar_enemigo(self, enemigo):
        if enemigo.sala is self.jugador.sala:
            dano = self._calcular_dano(enemigo, self.jugador)
            self.historial.guardar(self.jugador, "vida")
            self.jugador.recibir_dano(dano)
            self.bitacora.agregar(
                f"t={self.reloj}: {enemigo.nombre} ataca. Daño {dano}. "
                f"Vida jugador: {self.jugador.vida}"
            )
            if not self.jugador.esta_vivo():
                self.terminada = True
                self.bitacora.agregar(f"t={self.reloj}: el jugador ha muerto.")
                return
            self._programar_siguiente(enemigo, COSTO_ATACAR)
            return

        salida = None
        if enemigo.comportamiento == "errante":
            salida = self._decidir_errante(enemigo)
        elif enemigo.comportamiento == "rastreador":
            salida = self._decidir_rastreador(enemigo)

        if salida is not None:
            self.historial.asignar(enemigo, "sala", salida.destino)
            self.bitacora.agregar(
                f"t={self.reloj}: {enemigo.nombre} se mueve hacia {salida.direccion}")
            #moverse cuesta lo que cuesta la salida cruzada
            self._programar_movimiento(enemigo, salida)
        else:
            self.bitacora.agregar(f"t={self.reloj}: {enemigo.nombre} espera")
            #atacar y esperar cuestan 100
            self._programar_siguiente(enemigo, COSTO_ESPERAR)

    def _salidas_abiertas(self, sala):
        return [s for s in sala.salidas if not s.cerrada]

    def _decidir_errante(self, enemigo):
        abiertas = self._salidas_abiertas(enemigo.sala)
        if not abiertas:
            return None
        return self.azar.choice(abiertas)

    def _decidir_rastreador(self, enemigo):
        mejor = None
        mejor_rastro = -1
        mejor_id = -1
        for s in self._salidas_abiertas(enemigo.sala):
            rastro = s.destino.rastro
            if rastro is None or self.reloj - rastro >= RASTRO_VIGENCIA:
                continue
            id_vecina = s.destino.id
            if (mejor is None
                    or rastro > mejor_rastro
                    or (rastro == mejor_rastro and id_vecina < mejor_id)):
                mejor, mejor_rastro, mejor_id = s, rastro, id_vecina
        return mejor