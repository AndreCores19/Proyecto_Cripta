"""Reproductor: reconstruye un instante pasado en un mundo aparte (spec 005, US1, US2).

Parte del punto de control más cercano, arma un grafo de salas NUEVO con la partida del registro y
reproduce hacia adelante, con las reglas reales de `Partida`, las acciones guardadas (a lo más K).
Nunca lee ni escribe la partida viva, su historial, su agenda ni su azar, y no toca la red.
"""
from model.efectos_omitidos import aplicar
from model.partida_logica import Partida


class ErrorReproduccion(Exception):
    """La reproducción no pudo seguir (falta una ficha, un contenido, o una acción no se pudo repetir)."""


class Reproductor:
    """Una consulta: `armar_mundo()` devuelve un `Mundo` nuevo (grafo y fábrica sin red) cada vez."""

    def __init__(self, linea_tiempo, armar_mundo):
        self.linea_tiempo = linea_tiempo          #LineaTiempoPartida (solo se lee)
        self.armar_mundo = armar_mundo
        self.acciones_aplicadas = 0               #cuántas acciones reproduce esta consulta (FR-020)

    #reglas de parada
    def antes_de_la_accion(self, k):
        """Estado justo antes de la acción k (1 <= k <= n) y el reloj de esa decisión."""
        partida, _ = self._hasta_frontera(k - 1)
        return partida, self.linea_tiempo.relojes[k - 1]

    def en_instante(self, t):
        """Estado tras ejecutar todos los eventos con tiempo <= t; si el jugador tiene una decisión en t
        gana la decisión: el estado es el de justo antes de ella (investigación R7)."""
        linea = self.linea_tiempo
        i = linea.ultimo_menor_o_igual(t)             #última decisión con reloj <= t (desde 0), o -1
        pendiente = linea.reloj_decision_pendiente    #reloj de la decisión n+1, o None si el juego terminó
        if pendiente is not None and t == pendiente:
            return self._hasta_frontera(len(linea))[0]
        if i == -1 or linea.relojes[i] == t:          #la decisión i+1 gana: antes de la acción i+1
            return self._hasta_frontera(max(i, 0))[0]
        partida, mundo = self._hasta_frontera(i)      #c_k < t: se juega la acción k y corren los eventos hasta t
        self._aplicar(partida, mundo, i, t)
        return partida

    #reproducción
    def _hasta_frontera(self, frontera):
        #frontera = acciones ya hechas: carga el punto de esa casilla y reproduce las que faltan (< K)
        linea = self.linea_tiempo
        self.acciones_aplicadas = 0
        mundo = self.armar_mundo()
        partida = Partida.desde_registro(linea.punto_para(frontera), mundo)
        base = (frontera // linea.k) * linea.k
        self._aplicar_omitidos(partida, mundo, base)        #el punto se tomó antes del pergamino, no se refresca
        for indice in range(base, frontera):
            self._aplicar(partida, mundo, indice, None)
            self._aplicar_omitidos(partida, mundo, indice + 1)
        return partida, mundo

    def _aplicar_omitidos(self, partida, mundo, frontera):
        #en el punto de decisión con `frontera` acciones hechas: los efectos que el deshacer omitió ahí.
        #Una frontera por debajo de la del punto del que se parte nunca llega aquí: ese punto ya los trae.
        for entrada in self.linea_tiempo.omitidos_en(frontera):
            aplicar(entrada, mundo, partida)

    def _aplicar(self, partida, mundo, indice, limite):
        self.acciones_aplicadas += 1
        if self.acciones_aplicadas > self.linea_tiempo.k:
            raise ErrorReproduccion("La consulta reprodujo más de K acciones")
        tipo = self.linea_tiempo.tipos[indice]
        argumento = self.linea_tiempo.argumentos[indice]
        partida.limite_reproduccion = limite
        if not self._ejecutar(partida, mundo, tipo, argumento):
            raise ErrorReproduccion(f"No se pudo repetir la acción {indice + 1} ({tipo} {argumento})")
        partida.limite_reproduccion = None

    def _ejecutar(self, partida, mundo, tipo, argumento):
        jugador = partida.jugador
        if tipo == "mover":
            salida = jugador.sala.salida(argumento)
            if salida is None or salida.cerrada:
                return False
            if mundo.fabrica is not None:            #los mundos armados a mano no tienen contenido que poblar
                mundo.fabrica.poblar_sala(salida.destino)
            return partida.mover(argumento)
        if tipo == "esperar":
            return partida.esperar_jugador()
        if tipo == "abrir":
            return partida.abrir_puerta(argumento)
        if tipo == "atacar":
            for enemigo in partida.enemigos:
                if enemigo.id_enemigo == argumento and enemigo.sala is jugador.sala and enemigo.esta_vivo():
                    return partida.atacar(enemigo)
            return False
        if tipo == "recoger":
            for objeto in jugador.sala.objetos:
                if objeto.id_instancia == argumento:
                    return partida.recoger(objeto)
            return False
        if tipo in ("soltar", "equipar", "usar"):
            if not self._cursor_en(jugador.inventario, argumento):
                return False
            if tipo == "soltar":
                return partida.soltar()
            if tipo == "equipar":
                return partida.equipar()
            return partida.usar()
        raise ErrorReproduccion(f"Tipo de acción desconocido: {tipo}")

    @staticmethod
    def _cursor_en(inventario, id_instancia):
        #pone el cursor sobre el objeto guardado: las acciones registran el objeto, no la posición
        nodo = inventario.cabeza
        while nodo is not None:
            if nodo.objeto.id_instancia == id_instancia:
                inventario.actual = nodo
                return True
            nodo = nodo.siguiente
        return False
