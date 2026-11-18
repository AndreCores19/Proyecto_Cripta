from model.objeto_logica import PERGAMINO_RETROCESO
from model.sala_logica import EXPLORADA
from dto.estado_vista_dto import EstadoVistaDTO, SalidaVistaDTO, TrampaVistaDTO, ObjetoVistaDTO
from dto.inventario_vista_dto import InventarioVistaDTO
from dto.resumen_final_dto import ResumenFinalDTO
from dto.viaje_dto import ViajeResultadoDTO
from model.viaje_logica import Viaje
from data.fabrica_reproduccion import FabricaReproduccion
from data.grafo_reutilizable import GrafoReutilizable
from service.historia_service import HistoriaService
from service.lectura_partida import (enemigo_vista, enemigos_de_la_sala, jugador_vista, mapa_vista,
                                     objeto_inventario, objetos_del_inventario)


class JuegoService:

    def __init__(self, partida, fabrica, linea_tiempo=None):
        self.partida = partida
        self.fabrica = fabrica
        self.linea_tiempo = linea_tiempo      #LineaTiempoPartida o None (sin línea de tiempo)

    def _historia(self):
        #el servicio de consulta y su grafo aparte se arman una vez y se reusan mientras la línea de tiempo,
        #su constructor y la fábrica sean los mismos; no guarda nada de la partida viva
        if self.linea_tiempo is None:
            raise RuntimeError("Esta partida no tiene línea de tiempo")
        clave = (self.linea_tiempo, self.linea_tiempo.constructor_mundo, self.fabrica)
        cache = getattr(self, "_historia_cache", None)
        if cache is not None and all(a is b for a, b in zip(cache[0], clave)):
            return cache[1]
        grafo = GrafoReutilizable(self.linea_tiempo.constructor_mundo)

        def armar_mundo():
            return FabricaReproduccion.desde(self.fabrica, grafo.limpio()).armar_mundo()
        historia = HistoriaService(self.linea_tiempo, armar_mundo)
        self._historia_cache = (clave, historia)
        return historia

    def historia_por_instante(self, t):
        #RespuestaHistoriaDTO: el estado en el instante t, o el motivo del rechazo
        return self._historia().consultar_instante(t)

    def historia_por_accion(self, k):
        #RespuestaHistoriaDTO: el estado justo antes de la acción k, o el motivo del rechazo
        return self._historia().consultar_accion(k)

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

    def _tras_pergamino(self, retrocesos_antes):
        #si el contador de retrocesos cambió, se leyó un pergamino: la línea de tiempo se recorta (no es una acción)
        if self.linea_tiempo is not None and self.partida.retrocesos != retrocesos_antes:
            self.linea_tiempo.tras_retroceso(self.partida)

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
            self._tras_pergamino(marca[2])               #`usar` sobre un pergamino lo lee
        self.actualizar_fichas()
        return resultado

    def mover(self, direccion):
        salida = self.partida.jugador.sala.salida(direccion)
        if salida is None or salida.cerrada:
            return False
        marca = self._marca()
        contador_inicial = self.fabrica.poblar_sala(salida.destino)
        if contador_inicial is not None and self.linea_tiempo is not None:
            #por si este movimiento se revierte: la sala queda poblada aunque el deshacer no la despueble
            self.linea_tiempo.anotar_poblacion(salida.destino.id, contador_inicial, marca[1] + 1)
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
        retrocesos_antes = self.partida.retrocesos
        resultado = self.partida.usar_pergamino()
        self._tras_pergamino(retrocesos_antes)
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
        return objeto_inventario(objeto, actual)

    def inventario_vista(self):
        inv = self.partida.jugador.inventario
        return InventarioVistaDTO(inv.tamano, inv.capacidad_max, objetos_del_inventario(self.partida))

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
        return [enemigo_vista(e) for e in self.partida.enemigos if e.sala is sala and e.esta_vivo()]

    def terminada(self):
        return self.partida.terminada

    def semilla(self):
        return self.partida.semilla

    def mapa_vista(self):
        #Solo lee el conocimiento del jugador; no cambia nada ni consume tiempo
        return mapa_vista(self.partida)

    def estado_vista(self):
        #Solo lee el estado; nunca lo cambia
        partida = self.partida
        sala = partida.jugador.sala
        jugador = jugador_vista(partida)
        salidas = [SalidaVistaDTO(s.direccion,
                                s.destino.nombre if s.destino.conocimiento == EXPLORADA else None,
                                s.cerrada, s.costo)
                   for s in sala.salidas]
        enemigos = enemigos_de_la_sala(partida)
        trampas = [TrampaVistaDTO(t.nombre, t.dano, t.armada) for t in sala.trampas]
        objetos = [ObjetoVistaDTO(o.id_instancia, o.nombre) for o in sala.objetos]
        return EstadoVistaDTO(sala.id, sala.nombre, partida.reloj, jugador, salidas,
                              enemigos, trampas, objetos,
                              list(partida.bitacora.obtener_todos()[-20:]))
