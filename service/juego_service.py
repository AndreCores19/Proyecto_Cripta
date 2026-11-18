from model.objeto_logica import PERGAMINO_RETROCESO
from model.sala_logica import ABIERTA, CERRADA, EXPLORADA
from dto.estado_vista_dto import (EstadoVistaDTO, JugadorVistaDTO, SalidaVistaDTO,
                                  EnemigoVistaDTO, TrampaVistaDTO, ObjetoVistaDTO)
from dto.mapa_vista_dto import MapaVistaDTO, SalaConocidaDTO, SalidaConocidaDTO
from dto.inventario_vista_dto import InventarioVistaDTO, ObjetoInventarioDTO
from dto.resumen_final_dto import ResumenFinalDTO
from dto.viaje_dto import ViajeResultadoDTO
from structures.ordenamientos import ordenar
from model.viaje_logica import Viaje


class JuegoService:

    def __init__(self, partida, fabrica, linea_tiempo=None):
        self.partida = partida
        self.fabrica = fabrica
        self.linea_tiempo = linea_tiempo      #LineaTiempoPartida o None (sin línea de tiempo)

    def _registrar(self, tipo, argumento, reloj_antes, acciones_antes, retrocesos_antes):
        #Una llamada es una acción solo si las acciones subieron exactamente una y no hubo retroceso
        if self.linea_tiempo is None:
            return
        p = self.partida
        if p.acciones_jugador == acciones_antes + 1 and p.retrocesos == retrocesos_antes:
            self.linea_tiempo.registrar_accion(p, tipo, argumento, reloj_antes)

    def _marca(self):
        p = self.partida
        return p.reloj, p.acciones_jugador, p.retrocesos

    def _bajo_el_cursor(self):
        nodo = self.partida.jugador.inventario.actual
        return nodo.objeto.id_instancia if nodo is not None else None

    def recoger_objeto(self, id_instancia):
        resultado = False
        marca = self._marca()
        for objeto in self.partida.jugador.sala.objetos:
            if objeto.id_instancia == id_instancia:
                resultado = self.partida.recoger(objeto)
                break
        if resultado:
            self._registrar("recoger", id_instancia, *marca)
        self.actualizar_fichas()
        return resultado

    def soltar_objeto(self):
        marca = self._marca()
        objetivo = self._bajo_el_cursor()
        resultado = self.partida.soltar()
        if resultado:
            self._registrar("soltar", objetivo, *marca)
        self.actualizar_fichas()
        return resultado

    def equipar_objeto(self):
        marca = self._marca()
        objetivo = self._bajo_el_cursor()
        resultado = self.partida.equipar()
        if resultado:
            self._registrar("equipar", objetivo, *marca)
        return resultado

    def usar_objeto(self):
        marca = self._marca()
        objetivo = self._bajo_el_cursor()
        resultado = self.partida.usar()
        if resultado:
            self._registrar("usar", objetivo, *marca)
        self.actualizar_fichas()
        return resultado

    def mover(self, direccion):
        salida = self.partida.jugador.sala.salida(direccion)
        if salida is None or salida.cerrada:
            return False
        marca = self._marca()
        self.fabrica.poblar_sala(salida.destino)
        resultado = self.partida.mover(direccion)
        if resultado:
            self._registrar("mover", direccion, *marca)
        self.actualizar_fichas()
        return resultado

    def ir_a(self, id_sala):
        #viaje automático: cada paso es un movimiento normal (self.mover)
        destino = None
        for sala in self.partida.conocidas:
            if str(sala.id).lower() == str(id_sala).lower():
                destino = sala
                break
        if destino is None or destino.conocimiento != EXPLORADA:
            return ViajeResultadoDTO(False, "no_explorada", 0)
        viaje = Viaje(self.partida, destino, self.mover)
        while True:
            motivo = viaje.paso()
            if motivo is not None:
                break
        return ViajeResultadoDTO(True, motivo, len(viaje.direcciones), viaje.direcciones)

    def atacar(self, id_enemigo):
        jugador = self.partida.jugador
        objetivo = None
        for e in self.partida.enemigos:
            if (str(e.id_enemigo).lower() == str(id_enemigo).lower()
                    and e.sala is jugador.sala and e.esta_vivo()):
                objetivo = e
                break
        if objetivo is None:
            return False
        marca = self._marca()
        resultado = self.partida.atacar(objetivo)
        if resultado:
            self._registrar("atacar", objetivo.id_enemigo, *marca)
        self.actualizar_fichas()
        return resultado

    def esperar(self):
        marca = self._marca()
        resultado = self.partida.esperar_jugador()
        if resultado:
            self._registrar("esperar", None, *marca)
        self.actualizar_fichas()
        return resultado

    def abrir_puerta(self, direccion):
        marca = self._marca()
        resultado = self.partida.abrir_puerta(direccion)
        if resultado:
            self._registrar("abrir", direccion, *marca)
        return resultado

    def retroceder(self):
        ## el comando retroceder usa un pergamino del inventario
        inv = self.partida.jugador.inventario
        nodo = inv.cabeza
        while nodo is not None and nodo.objeto.clase != PERGAMINO_RETROCESO:
            nodo = nodo.siguiente
        if nodo is None:
            return False
        inv.actual = nodo
        resultado = self.partida.usar_pergamino()
        self.actualizar_fichas()
        return resultado

    def siguiente_objeto(self):
        return self.partida.jugador.inventario.siguiente()

    def anterior_objeto(self):
        return self.partida.jugador.inventario.anterior()

    def _ids_en_uso(self):
        sala = self.partida.jugador.sala
        ids = []
        for enemigo in self.partida.enemigos:
            ids.append(enemigo.tipo)
        for enemigo in sala.inactivos:
            ids.append(enemigo.tipo)
        for objeto in sala.objetos:
            ids.append(objeto.id_catalogo)
        for objeto in self.partida.jugador.inventario.a_lista():
            ids.append(objeto.id_catalogo)
        for trampa in sala.trampas:
            ids.append(trampa.id_catalogo)
        return ids

    def actualizar_fichas(self):
        self.fabrica.marcar_en_uso(self._ids_en_uso())

    def vista_ordenada(self, criterio):
        inv = self.partida.jugador.inventario
        return [self._objeto_inventario(o, False) for o in inv.vista_ordenada(criterio)]

    @staticmethod
    def _objeto_inventario(objeto, actual):
        return ObjetoInventarioDTO(objeto.id_instancia, objeto.nombre, objeto.peso,
                                   objeto.valor, bool(objeto.equipado), actual)

    def inventario_vista(self):
        inv = self.partida.jugador.inventario
        objetos = []
        nodo = inv.cabeza
        while nodo is not None:
            objetos.append(self._objeto_inventario(nodo.objeto, nodo is inv.actual))
            nodo = nodo.siguiente
        return InventarioVistaDTO(inv.tamano, inv.capacidad_max, objetos)

    def resumen_final(self):
        p = self.partida
        return ResumenFinalDTO(p.jugador.nombre, p.reloj, p.victoria, p.terminada,
                               p.acciones_jugador, p.enemigos_derrotados,
                               list(p.bitacora.obtener_todos()[-20:]))

    def objetos_en_sala(self):
        return [ObjetoVistaDTO(o.id_instancia, o.nombre)
                for o in self.partida.jugador.sala.objetos]

    def enemigos_en_sala(self):
        sala = self.partida.jugador.sala
        return [EnemigoVistaDTO(e.nombre, e.id_enemigo, e.vida, e.vida_max,
                                [ef.tipo for ef in e.efectos], e.es_cazador())
                for e in self.partida.enemigos if e.sala is sala and e.esta_vivo()]

    def terminada(self):
        return self.partida.terminada

    def semilla(self):
        return self.partida.semilla

    def mapa_vista(self):
        #Solo lee el conocimiento del jugador; no cambia nada ni consume tiempo
        partida = self.partida
        exploradas = [s for s in partida.conocidas if s.conocimiento == EXPLORADA]
        salas = []
        for sala in ordenar(exploradas, lambda s: s.id):
            salidas = []
            for s in sala.salidas:
                recordada = partida.puerta_recordada(s)
                puerta = "abierta" if recordada == ABIERTA else "cerrada" if recordada == CERRADA else "sin observar"
                if s.destino.conocimiento == EXPLORADA:
                    salidas.append(SalidaConocidaDTO(s.direccion, s.destino.id, s.destino.nombre, s.costo, puerta))
                else:
                    salidas.append(SalidaConocidaDTO(s.direccion, None, None, s.costo, puerta))
            salas.append(SalaConocidaDTO(sala.id, sala.nombre, salidas))
        return MapaVistaDTO(partida.jugador.sala.id, salas)

    def estado_vista(self):
        #Solo lee el estado; nunca lo cambia
        partida = self.partida
        sala = partida.jugador.sala
        j = partida.jugador
        inv = j.inventario
        jugador = JugadorVistaDTO(
            j.nombre, j.vida, j.vida_max, j.ataque, j.defensa, j.velocidad,
            inv.arma_equipada.nombre if inv.arma_equipada is not None else None,
            inv.armadura_equipada.nombre if inv.armadura_equipada is not None else None,
            [e.tipo for e in j.efectos])
        salidas = [SalidaVistaDTO(s.direccion,
                                s.destino.nombre if s.destino.conocimiento == EXPLORADA else None,
                                s.cerrada, s.costo)
                   for s in sala.salidas]
        enemigos = [EnemigoVistaDTO(e.nombre, e.id_enemigo, e.vida, e.vida_max,
                                    [ef.tipo for ef in e.efectos], e.es_cazador())
                    for e in partida.enemigos if e.sala is sala]
        trampas = [TrampaVistaDTO(t.nombre, t.dano, t.armada) for t in sala.trampas]
        objetos = [ObjetoVistaDTO(o.id_instancia, o.nombre) for o in sala.objetos]
        return EstadoVistaDTO(sala.id, sala.nombre, partida.reloj, jugador, salidas,
                              enemigos, trampas, objetos,
                              list(partida.bitacora.obtener_todos()[-20:]))
