"""La línea de tiempo de una partida: qué se anota mientras se juega (spec 005).

Por cada acción del jugador que sobrevive se guarda un registro pequeño (reloj de la decisión, tipo y
objetivo ya resuelto) y, cada K acciones, un punto de control con el estado completo. No sabe nada de
la vista ni del controlador: la llama el servicio.
"""
from model.registro_estado import capturar
from structures.linea_tiempo import LineaTiempo

K_POR_DEFECTO = 50  # PROVISIONAL: replaced by T068 with the value measured by the benchmark (plan.md, "Default K")


class LineaTiempoPartida:

    def __init__(self):
        self.linea = None                 #LineaTiempo (estructura); existe tras `iniciar`
        self.constructor_mundo = None     #función que arma un esqueleto nuevo de salas
        self.reloj_final = 0

    def iniciar(self, partida, constructor_mundo, k=None):
        """Empieza a anotar la partida: toma el punto de control 0 (antes de toda acción)."""
        self.constructor_mundo = constructor_mundo
        self.linea = LineaTiempo(K_POR_DEFECTO if k is None else k)
        self.linea.agregar_punto(capturar(partida))
        self._marcar_reloj(partida)

    def registrar_accion(self, partida, tipo, argumento, reloj_antes):
        """Anota una acción que se ejecutó con éxito. `reloj_antes` es el reloj de la decisión."""
        linea = self.linea
        linea.agregar_accion(reloj_antes, tipo, argumento)
        if len(linea) % linea.k == 0:
            linea.agregar_punto(capturar(partida))
        self._marcar_reloj(partida)

    def _marcar_reloj(self, partida):
        #el reloj de ahora; si el juego sigue, también es el de la decisión pendiente (la n+1)
        self.reloj_final = partida.reloj
        self.linea.reloj_final = partida.reloj
        self.linea.reloj_decision_pendiente = None if partida.terminada else partida.reloj

    #lectura para las consultas
    @property
    def reloj_decision_pendiente(self):
        return self.linea.reloj_decision_pendiente

    def ultimo_menor_o_igual(self, t):
        return self.linea.ultimo_menor_o_igual(t)

    def punto_para(self, frontera):
        return self.linea.punto_para(frontera)

    @property
    def k(self):
        return self.linea.k

    @property
    def relojes(self):
        return self.linea.relojes

    @property
    def tipos(self):
        return self.linea.tipos

    @property
    def argumentos(self):
        return self.linea.argumentos

    @property
    def puntos(self):
        return self.linea.puntos

    def __len__(self):
        return len(self.linea)
