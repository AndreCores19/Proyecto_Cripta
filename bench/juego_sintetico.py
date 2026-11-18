"""Partidas sintéticas para el benchmark de la línea de tiempo (spec 005, FR-024, FR-025).

Un mundo se describe con datos simples (SalaDTO/SalidaDTO, una lista de enemigos y los objetos del suelo),
así que el juego vivo y cada mundo aparte de una consulta se arman con las mismas funciones: el grafo con el
constructor puro `construir_grafo` y las entidades por id. Sin red (el esqueleto de `referencia` sale del
paquete sin conexión) y sin vista: los comandos pasan por `Controlador` con `vista=None`.

Mundos (investigación R11):
- `referencia`: esqueleto y costos de cripta-06 (paquete offline) y 30 cazadores, como
  `bench_ciclo.armar_partida_referencia`; es el del veredicto.
- `grande`: cadena de 100 salas y 100 enemigos errantes (prueba de esfuerzo).
- `extremo`: cadena de 100 salas y 300 enemigos (solo información).
Mismo mundo y misma semilla → los mismos comandos y el mismo estado final.
"""
import random

from adapters.cliente_offline import ClienteOffline
from bench.bench_ciclo import CARPETA_OFFLINE, COSTOS_SALIDA, RANGOS_CAZADOR
from controller.controlador import Controlador
from data.repositorio_cripta import RepositorioCripta, construir_grafo
from dto.sala_dto import SalaDTO
from dto.salida_dto import SalidaDTO
from model.enemigo_logica import Enemigo
from model.jugador_logica import Jugador
from model.linea_tiempo_logica import LineaTiempoPartida
from model.objeto_logica import PERGAMINO_RETROCESO, Objeto
from model.partida_logica import Partida
from model.registro_estado import Mundo
from service.juego_service import JuegoService

MUNDOS = ("referencia", "grande", "extremo")
TECLAS = (("N", "w"), ("S", "s"), ("E", "d"), ("O", "a"))
#objetos del suelo de la sala inicial: (id_instancia, id_catalogo)
OBJETOS_INICIALES = ((1, "perg"), (2, "perg"), (3, "perg"), (4, "perg"), (5, "perg"), (6, "perg"),
                     (7, "espada"), (8, "escudo"))
MAX_LECTURAS = 8


def _objeto(id_instancia, id_catalogo):
    if id_catalogo == "perg":
        return Objeto(id_instancia, "perg", "Pergamino", PERGAMINO_RETROCESO, 1, 20)
    if id_catalogo == "espada":
        return Objeto(id_instancia, "espada", "Espada", "arma", 5, 30, ataque_bonus=4)
    if id_catalogo == "escudo":
        return Objeto(id_instancia, "escudo", "Escudo", "armadura", 6, 25, defensa_bonus=2)
    raise ValueError(f"Objeto sintético desconocido: {id_catalogo}")


def _jugador(sala):
    #invulnerable, como en bench_ciclo: la partida dura todas las acciones pedidas
    return Jugador(vida_max=10 ** 9, ataque=10, defensa=10 ** 6, velocidad=100, inventario_max=10, sala=sala)


class _FabricaNula:
    """Los mundos sintéticos no tienen contenido que poblar ni catálogo: el servicio no pide nada."""

    def poblar_sala(self, sala):
        return None

    def marcar_en_uso(self, ids):
        pass


class MundoSintetico:
    """Un mundo: sus DTO de salas, sus enemigos (id, sala, cazador, rango) y la sala inicial."""

    def __init__(self, nombre, semilla=1):
        self.nombre = nombre
        self.semilla = semilla
        if nombre == "referencia":
            repo = RepositorioCripta(ClienteOffline(CARPETA_OFFLINE))
            self.dtos = repo.cargar_esqueleto("cripta-06")
            self.sala_inicial = repo.datos.sala_inicial
            azar = random.Random(semilla)
            candidatas = [d.id_sala for d in self.dtos if d.id_sala != self.sala_inicial]
            elegidas = azar.sample(candidatas, 30)
            self.enemigos = [(f"c{k}", id_sala, True, azar.choice(RANGOS_CAZADOR))
                             for k, id_sala in enumerate(elegidas)]
        elif nombre in ("grande", "extremo"):
            salas, cantidad = 100, (100 if nombre == "grande" else 300)
            azar = random.Random(semilla)
            salidas = [[] for _ in range(salas)]
            for i in range(salas - 1):
                costo = azar.choice(COSTOS_SALIDA)
                salidas[i].append(SalidaDTO("N", i + 2, costo=costo))
                salidas[i + 1].append(SalidaDTO("S", i + 1, costo=costo))
            self.dtos = [SalaDTO(i + 1, f"Sala {i + 1}", salidas[i]) for i in range(salas)]
            self.sala_inicial = 1
            self.enemigos = [(f"e{k}", k % salas + 1, False, 0) for k in range(cantidad)]
        else:
            raise ValueError(f"Mundo desconocido: {nombre}")

    def _crear_enemigo(self, id_enemigo, salas):
        for id_e, id_sala, cazador, rango in self.enemigos:
            if id_e == id_enemigo:
                sala = salas.buscar(id_sala)
                if cazador:
                    return Enemigo(id_e, "x", f"Cazador {id_e}", 50, 50, 5, 0, 100, "cazador", sala, rango=rango)
                return Enemigo(id_e, "x", f"Enemigo {id_e}", 50, 50, 5, 0, 100, "errante", sala)
        raise ValueError(f"Enemigo sintético desconocido: {id_enemigo}")

    def nueva_partida(self, semilla_partida):
        """La partida viva: un grafo nuevo, el jugador, los objetos del suelo y los enemigos activos."""
        salas = construir_grafo(self.dtos)
        inicial = salas.buscar(self.sala_inicial)
        for id_instancia, id_catalogo in OBJETOS_INICIALES:
            inicial.objetos.append(_objeto(id_instancia, id_catalogo))
        partida = Partida(_jugador(inicial), semilla=semilla_partida)
        partida.salas = salas
        for id_enemigo, _, _, _ in self.enemigos:
            partida.activar_enemigo(self._crear_enemigo(id_enemigo, salas))
        return partida

    def constructor(self):
        """El esqueleto de salas (lo que la línea de tiempo llama `constructor_mundo`)."""
        return construir_grafo(self.dtos)

    def armar_mundo(self):
        """Un `Mundo` nuevo para restaurar un punto de control: grafo nuevo y entidades por id."""
        return self.mundo_sobre(construir_grafo(self.dtos))

    def mundo_sobre(self, salas):
        """Un `Mundo` sobre un grafo ya armado (p. ej. el de `GrafoReutilizable`), con entidades por id."""
        return Mundo(salas, _jugador, _objeto, lambda id_e: self._crear_enemigo(id_e, salas),
                     lambda id_instancia: None)


def _tecla(direccion):
    for d, t in TECLAS:
        if d == direccion:
            return t
    return direccion


def _elegir(azar, servicio, lecturas, sala_nueva):
    """Un comando con semilla, según el estado: movimientos por salidas abiertas, esperar, atacar si hay
    enemigos, recoger y soltar si hay objetos, usar o equipar, y algunas lecturas de pergamino (una justo
    después de entrar en una sala nueva)."""
    estado = servicio.estado_vista()
    inv = servicio.inventario_vista()
    con_pergamino = any(o.nombre == "Pergamino" for o in inv.objetos)
    if con_pergamino and lecturas < MAX_LECTURAS and (sala_nueva and azar.random() < 0.5 or azar.random() < 0.004):
        return "retroceder"
    opciones = [(7, _tecla(s.direccion)) for s in estado.salidas if not s.cerrada]
    opciones.append((2, "esperar"))
    vivos = [e for e in estado.enemigos if e.vida > 0]
    if vivos:
        opciones.append((1, "atacar" if len(vivos) == 1 else f"atacar {str(vivos[0].id_enemigo).lower()}"))
    for o in servicio.objetos_en_sala():
        opciones.append((4, f"recoger {o.id_instancia}"))
    if inv.tamano > 0:
        opciones.extend([(1, "soltar"), (1, "equipar"), (1, "sig")])
    total = 0
    for peso, _ in opciones:
        total += peso
    punto = azar.randrange(total)
    for peso, comando in opciones:
        if punto < peso:
            return comando
        punto -= peso
    return "esperar"


class Juego:
    """Una partida sintética jugada: la partida viva, su servicio, su línea de tiempo y los comandos."""

    def __init__(self, mundo, semilla, acciones, k):
        self.mundo = mundo
        self.partida = mundo.nueva_partida(semilla)
        self.linea = None
        if k is not None:
            self.linea = LineaTiempoPartida()
            self.linea.iniciar(self.partida, mundo.constructor, k)
        self.servicio = JuegoService(self.partida, _FabricaNula(), linea_tiempo=self.linea)
        self.comandos = []
        self.lecturas = 0
        azar = random.Random(semilla)
        controlador = Controlador(self.servicio, None, None, None)
        p = self.partida
        #se cuentan acciones del jugador que sobreviven; un tope evita un bucle si nada avanza
        intentos = 0
        #primero recoge tres pergaminos de la sala inicial: así toda partida tiene lecturas que probar
        al_empezar = ["recoger 1", "recoger 2", "recoger 3"]
        self._entro = False
        while p.acciones_jugador < acciones and intentos < acciones * 6:
            intentos += 1
            conocidas = len(p.conocidas)
            if al_empezar:
                comando = al_empezar.pop(0)
            else:
                comando = _elegir(azar, self.servicio, self.lecturas, self._entro)
            retrocesos = p.retrocesos
            controlador.ejecutar(comando)
            self.comandos.append(comando)
            if p.retrocesos != retrocesos:
                self.lecturas += 1
            self._entro = len(p.conocidas) > conocidas


def jugar(nombre, semilla, acciones, k=50, mundo=None):
    """Juega `acciones` acciones del jugador en el mundo `nombre` con la semilla dada; devuelve el `Juego`."""
    return Juego(mundo if mundo is not None else MundoSintetico(nombre), semilla, acciones, k)
