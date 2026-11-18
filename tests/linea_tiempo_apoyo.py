"""Apoyo de las pruebas de la línea de tiempo (spec 005). No es un módulo de pruebas.

Todo se arma con datos falsos dentro de la prueba y sin red: salas hechas por el constructor puro
del esqueleto, la fábrica real sobre un repositorio y un catálogo falsos, y un cliente falso que
falla ante cualquier llamada. Solo importa de model/, dto/, structures/, data/, service/ y controller/.
"""
import random

from controller.controlador import Controlador
from data.fabrica_modelo import FabricaModelo
from data.repositorio_cripta import construir_grafo
from dto.contenido_sala_dto import ContenidoSalaDTO, InstanciaEnemigoDTO, InstanciaTrampaDTO
from dto.datos_cripta_dto import EstadisticasJugadorDTO
from dto.ficha_dto import (FichaAntidotoDTO, FichaAntorchaDTO, FichaArmaDTO, FichaArmaduraDTO,
                           FichaEnemigoDTO, FichaLlaveDTO, FichaPergaminoRetrocesoDTO,
                           FichaPocionDTO, FichaTrampaDTO)
from dto.sala_dto import SalaDTO
from dto.salida_dto import SalidaDTO
from model.partida_logica import Partida
from model.registro_estado import Mundo
from service.juego_service import JuegoService
from structures.cache_fichas import CacheFichas

TECLAS = (("N", "w"), ("S", "s"), ("E", "d"), ("O", "a"))
LLAVE = "llave1"


def _tecla(direccion):
    for d, t in TECLAS:
        if d == direccion:
            return t
    return direccion


#fichas falsas
def _fichas():
    return [
        FichaArmaDTO("espada", "Espada", "arma", 5, 30, 4),
        FichaArmaduraDTO("escudo", "Escudo", "armadura", 6, 25, 2),
        FichaPocionDTO("curar", "Poción de vida", "pocion", 1, 10, 15, 0, 0),
        FichaPocionDTO("rapida", "Poción de velocidad", "pocion", 1, 10, 0, 300, 50),
        FichaPocionDTO("lenta", "Poción lenta", "pocion", 1, 5, 0, 200, -30),
        FichaAntidotoDTO("antidoto", "Antídoto", "antidoto", 1, 8),
        FichaAntorchaDTO("antorcha", "Antorcha", "antorcha", 2, 6, 400),
        FichaLlaveDTO(LLAVE, "Llave", "llave", 1, 1, LLAVE),
        FichaPergaminoRetrocesoDTO("perg", "Pergamino", "pergamino_retroceso", 1, 20),
        FichaEnemigoDTO("rata", "Rata", "enemigo", 12, 3, 0, 100, "errante", ["curar"]),
        FichaEnemigoDTO("guardia", "Guardia", "enemigo", 20, 4, 1, 80, "rastreador", []),
        FichaEnemigoDTO("arana", "Araña", "enemigo", 15, 3, 0, 90, "errante", [], regeneracion=2),
        FichaEnemigoDTO("lobo", "Lobo", "enemigo", 25, 4, 0, 120, "cazador", ["antidoto"], rango=300),
        FichaTrampaDTO("pinchos", "Pinchos", "trampa", 3, 200, 0),
        FichaTrampaDTO("veneno", "Trampa de veneno", "trampa", 1, 250, 3),
    ]


def _ficha(id_ficha):
    for f in _fichas():
        if f.id_ficha == id_ficha:
            return f
    raise AssertionError(f"ficha falsa desconocida: {id_ficha}")


class FakeCliente:
    """Cuenta las llamadas y falla ante cualquier una: prueba que no se toca la red."""

    def __init__(self):
        self.llamadas = 0

    def solicitudes_realizadas(self):
        return self.llamadas

    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)

        def llamar(*args, **kwargs):
            self.llamadas += 1
            raise AssertionError(f"Se intentó usar la red: {nombre}")
        return llamar


class FakeCatalogo:
    """Catálogo con una caché LRU de pocas fichas (2 por defecto): en juegos cortos ya hay desalojos."""

    def __init__(self, capacidad=2):
        self.cache = CacheFichas(capacidad)
        self.resoluciones = 0      #cuántas fichas hubo que volver a poner en la caché

    def ids_del_contenido(self, contenidos):
        ids = []
        for contenido in contenidos:
            for enemigo in contenido.enemigos:
                ids.append(enemigo.tipo)
            for trampa in contenido.trampas:
                ids.append(trampa.tipo)
            ids.extend(contenido.objetos)
        return ids

    def resolver(self, ids, con_sueltos=True):
        for id_ficha in ids:
            if not self.cache.contiene(id_ficha):
                self.resoluciones += 1
                self.cache.insertar(id_ficha, _ficha(id_ficha))

    def marcar_en_uso(self, ids):
        pass


class _DatosFalsos:
    def __init__(self, salas, salida, jugador, inventario_max):
        self.sala_inicial = 1
        self.sala_salida = salida
        self.jugador = jugador
        self.inventario_max = inventario_max


class _RepoFalso:
    def __init__(self, dtos, contenidos, datos):
        self.salas = construir_grafo(dtos)
        self.contenidos = contenidos
        self.datos = datos


#plano del mundo
def _armar_plano(semilla, salas, enemigos, cazadores, con_objetos, con_pergaminos):
    azar = random.Random(semilla * 7919 + 13)
    n = max(2, salas)
    salidas = [[] for _ in range(n)]
    for i in range(n - 1):
        forzada = (i == 1)                              #la puerta entre la sala 2 y la 3 cierra sola
        cerrada = con_objetos and i >= 1 and (forzada or azar.random() < 0.3)
        llave = LLAVE if cerrada else None
        auto = (150 if forzada else azar.choice((None, 150, 300))) if cerrada else None
        costo = azar.choice((None, None, 50, 150))
        salidas[i].append(SalidaDTO("N", i + 2, cerrada, llave, auto, costo))
        salidas[i + 1].append(SalidaDTO("S", i + 1, cerrada, llave, auto, costo))
    for i in range(n - 2):
        if azar.random() < 0.3:
            salidas[i].append(SalidaDTO("E", i + 3))
            salidas[i + 2].append(SalidaDTO("O", i + 1))
    dtos = [SalaDTO(i + 1, f"Sala {i + 1}", salidas[i]) for i in range(n)]

    objetos = [[] for _ in range(n)]
    enemigos_sala = [[] for _ in range(n)]
    trampas = [[] for _ in range(n)]
    if con_objetos:
        objetos[0].extend([LLAVE, "espada", "escudo", "curar", "rapida", "antidoto", "antorcha"])
        for i in range(1, n):
            for _ in range(azar.randint(0, 2)):
                objetos[i].append(azar.choice(("espada", "escudo", "curar", "rapida", "lenta",
                                               "antidoto", "antorcha", LLAVE)))
    if con_pergaminos:
        objetos[0].extend(["perg", "perg"])
        for i in range(1, n):
            if azar.random() < 0.3:
                objetos[i].append("perg")
    for k in range(enemigos):
        i = azar.randint(1, n - 1)
        enemigos_sala[i].append(InstanciaEnemigoDTO(f"e{k + 1}", azar.choice(("rata", "guardia", "arana")), None))
    for k in range(cazadores):
        i = azar.randint(min(2, n - 1), n - 1)
        enemigos_sala[i].append(InstanciaEnemigoDTO(f"c{k + 1}", "lobo", None))
    for i in range(1, n):
        if i == 1:
            trampas[i].append(InstanciaTrampaDTO(f"t{i + 1}", "veneno"))
        elif azar.random() < 0.4:
            trampas[i].append(InstanciaTrampaDTO(f"t{i + 1}", azar.choice(("pinchos", "veneno"))))
    contenidos = [ContenidoSalaDTO(i + 1, enemigos_sala[i], objetos[i], trampas[i]) for i in range(n)]
    return dtos, contenidos


class MundoPrueba:
    """Un mundo armado: el juego vivo, su fábrica y todo lo que hace falta para armar otro igual."""

    def __init__(self, semilla, salas, enemigos, cazadores, con_objetos, con_pergaminos, clase_partida,
                 vida_jugador=400):
        self.semilla = semilla
        self.dtos, self.contenidos = _armar_plano(semilla, salas, enemigos, cazadores,
                                                  con_objetos, con_pergaminos)
        self.cliente = FakeCliente()
        self.catalogo = FakeCatalogo()
        self.estadisticas = EstadisticasJugadorDTO(vida_jugador, 8, 1, 100)
        self.datos = _DatosFalsos(len(self.dtos), len(self.dtos), self.estadisticas, 8)
        self.repo = _RepoFalso(self.dtos, list(self.contenidos), self.datos)
        self.fabrica = FabricaModelo(self.repo, self.catalogo)
        self.fabrica.iniciar()
        inicial = self.repo.salas.buscar(1)
        salida = self.repo.salas.buscar(len(self.dtos))
        self.fabrica.poblar_sala(inicial)
        jugador = self.fabrica.crear_jugador(inicial)
        self.partida = clase_partida(jugador, semilla, salida)
        self.partida.creador_objetos = self.fabrica.objeto_desde_id
        self.partida.salas = self.repo.salas
        self.partida.fabrica = self.fabrica
        self.servicio = JuegoService(self.partida, self.fabrica)

    def constructor(self):
        """El constructor del mundo: arma un grafo nuevo del esqueleto cada vez."""
        return construir_grafo(self.dtos)

    def _instancia_enemigo(self, id_enemigo):
        for c in self.contenidos:
            for e in c.enemigos:
                if e.instancia == id_enemigo:
                    return e
        raise AssertionError(f"enemigo desconocido: {id_enemigo}")

    def _instancia_trampa(self, id_instancia):
        for c in self.contenidos:
            for t in c.trampas:
                if t.instancia == id_instancia:
                    return t
        raise AssertionError(f"trampa desconocida: {id_instancia}")

    def nuevo_mundo(self):
        """Un `Mundo` para restaurar: grafo nuevo, fábrica nueva (sin red) y las mismas fichas."""
        repo = _RepoFalso(self.dtos, list(self.contenidos), self.datos)
        fabrica = FabricaModelo(repo, FakeCatalogo())
        fabrica.iniciar()
        return Mundo(
            repo.salas,
            fabrica.crear_jugador,
            lambda id_instancia, id_catalogo: fabrica.crear_objeto(id_instancia, _ficha(id_catalogo)),
            lambda id_enemigo: self._crear_enemigo(fabrica, id_enemigo),
            lambda id_instancia: self._crear_trampa(fabrica, id_instancia),
            fabrica=fabrica, creador_objetos=fabrica.objeto_desde_id)

    def _crear_enemigo(self, fabrica, id_enemigo):
        instancia = self._instancia_enemigo(id_enemigo)
        return fabrica.crear_enemigo(instancia, _ficha(instancia.tipo), None)

    def _crear_trampa(self, fabrica, id_instancia):
        instancia = self._instancia_trampa(id_instancia)
        return fabrica.crear_trampa(instancia, _ficha(instancia.tipo))

    def servicio_de(self, partida, mundo):
        """Un servicio para jugar una partida restaurada con la fábrica de su mundo."""
        return JuegoService(partida, mundo.fabrica)


def armar_mundo(semilla, salas=6, enemigos=4, cazadores=1, con_objetos=True, con_pergaminos=False,
                clase_partida=Partida, vida_jugador=400):
    return MundoPrueba(semilla, salas, enemigos, cazadores, con_objetos, con_pergaminos, clase_partida,
                       vida_jugador)


#resúmenes comparables (los campos del FR-004)
def _plano_mapa(mapa):
    return (mapa.id_sala_actual,
            tuple((s.id_sala, s.nombre,
                   tuple((x.direccion, x.id_destino, x.nombre_destino, x.costo, x.puerta)
                         for x in s.salidas))
                  for s in mapa.salas))


def _plano(reloj, id_sala, jugador, inventario, enemigos, mapa):
    return (
        reloj, id_sala,
        (jugador.vida, jugador.vida_max, jugador.ataque, jugador.defensa, jugador.velocidad,
         jugador.arma, jugador.armadura, tuple(jugador.efectos)),
        tuple((o.id_instancia, o.nombre, bool(o.equipado)) for o in inventario),   #en orden, sin el cursor
        tuple(sorted(((str(e.id_enemigo), e.vida) for e in enemigos))),
        _plano_mapa(mapa))


def resumen_plano(origen):
    """Tupla comparable con exactamente los campos del FR-004, de una Partida viva o de un ResumenHistoriaDTO."""
    if isinstance(origen, Partida):
        servicio = JuegoService(origen, None)
        estado = servicio.estado_vista()
        return _plano(origen.reloj, estado.id_sala, estado.jugador,
                      servicio.inventario_vista().objetos, estado.enemigos, servicio.mapa_vista())
    return _plano(origen.reloj, origen.id_sala, origen.jugador, origen.inventario,
                  origen.enemigos, origen.mapa)


def _a_plano(resultado):
    return resultado if isinstance(resultado, tuple) else resumen_plano(resultado)


def con_reloj(plano, reloj):
    return (reloj,) + tuple(plano[1:])


def capturar_vivo(servicio):
    """(número de la acción próxima, reloj, resumen): se llama antes de cada acción y una vez al final."""
    p = servicio.partida
    return (p.acciones_jugador + 1, p.reloj, resumen_plano(p))


def registrar_vivo(vivos, servicio):
    """Anota la decisión actual en `vivos`. Tras un pergamino el número baja: se descartan las
    entradas de los números que ya no existen y la de la decisión actual se reemplaza por lo vivo."""
    entrada = capturar_vivo(servicio)
    while vivos and vivos[-1][0] > entrada[0]:
        vivos.pop()
    if vivos and vivos[-1][0] == entrada[0]:
        vivos[-1] = entrada
    else:
        vivos.append(entrada)


#un juego con semilla
class VistaMuda:
    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)
        return lambda *args, **kwargs: None


def _elegir_comando(azar, servicio, con_pergaminos):
    estado = servicio.estado_vista()
    inv = servicio.inventario_vista()
    opciones = []
    for s in estado.salidas:
        if s.cerrada:
            opciones.append((5, f"abrir {_tecla(s.direccion)}"))
        else:
            opciones.append((7, _tecla(s.direccion)))
    opciones.append((2, "esperar"))
    vivos = [e for e in estado.enemigos if e.vida > 0]
    if vivos:
        comando = "atacar" if len(vivos) == 1 else f"atacar {str(vivos[0].id_enemigo).lower()}"
        opciones.append((10, comando))
    for o in servicio.objetos_en_sala():
        opciones.append((5, f"recoger {o.id_instancia}"))
    if inv.tamano > 0:
        opciones.extend([(2, "soltar"), (4, "equipar"), (4, "usar"), (1, "sig"), (1, "ant")])
        if con_pergaminos:
            opciones.append((2, "retroceder"))
    total = 0
    for peso, _ in opciones:
        total += peso
    punto = azar.randrange(total)
    for peso, comando in opciones:
        if punto < peso:
            return comando
        punto -= peso
    return "esperar"


def jugar_semilla(servicio, semilla, n, vivos=None, con_pergaminos=False, despues=None):
    """Juega hasta n comandos deterministas (según la semilla) por Controlador.ejecutar con una vista muda.

    Devuelve la lista de comandos. Si se pasa `vivos`, anota la decisión antes de cada comando
    y una vez al final (ver registrar_vivo). `despues(comando)`, si se pasa, se llama tras cada comando."""
    azar = random.Random(semilla)
    controlador = Controlador(servicio, VistaMuda(), None, None)
    comandos = []
    for _ in range(n):
        if servicio.terminada():
            break
        comando = _elegir_comando(azar, servicio, con_pergaminos)
        if vivos is not None:
            registrar_vivo(vivos, servicio)
        controlador.ejecutar(comando)
        comandos.append(comando)
        if despues is not None:
            despues(comando)
    if vivos is not None:
        registrar_vivo(vivos, servicio)
    return comandos


def ejecutar_comandos(servicio, comandos):
    """Repite una lista de comandos en otro servicio (por ejemplo, el segundo juego del oráculo)."""
    controlador = Controlador(servicio, VistaMuda(), None, None)
    for comando in comandos:
        if servicio.terminada():
            break
        controlador.ejecutar(comando)


class PartidaInstrumentada(Partida):
    """Un segundo juego vivo que anota una foto con su reloj. No usa Reproductor ni LineaTiempo.

    Fotos: (a) al construirse (la primera avanzar_hasta_jugador); (b) tras cada evento que no es
    del jugador (_actuar_enemigo, _cerrar_puerta, efectos.ejecutar); (c) tras el efecto propio de cada
    acción del jugador, justo antes de correr los eventos (así un instante entre la decisión y el
    primer evento ve la acción ya hecha). Cada foto es (reloj, resumen, acciones hechas)."""

    def __init__(self, jugador, semilla=None, sala_salida=None):
        self.instantaneas = []
        super().__init__(jugador, semilla, sala_salida)
        original = self.efectos.ejecutar

        def ejecutar(ev):
            original(ev)
            self._anotar()
        self.efectos.ejecutar = ejecutar

    def _anotar(self):
        self.instantaneas.append((self.reloj, resumen_plano(self), self.acciones_jugador))

    def avanzar_hasta_jugador(self, limite=None):
        self._anotar()
        super().avanzar_hasta_jugador(limite)

    def _actuar_enemigo(self, enemigo):
        super()._actuar_enemigo(enemigo)
        self._anotar()

    def _cerrar_puerta(self, salida):
        super()._cerrar_puerta(salida)
        self._anotar()

    def retroceder(self):
        resultado = super().retroceder()
        if resultado:
            #las fotos de las acciones que se deshicieron ya no son parte de la historia
            while self.instantaneas and self.instantaneas[-1][2] > self.acciones_jugador:
                self.instantaneas.pop()
        return resultado


def oraculo(servicio, vivos, instantaneas, consultar):
    """Compara `consultar(modo, valor)` con lo que el juego vivo mostró.

    `#k` (1 <= k <= acciones hechas) debe dar lo capturado antes de la acción k. Para cada instante t
    de 0 al reloj: si t es el reloj de una decisión, gana la captura de esa decisión; si no, la última
    foto con reloj <= t (con el reloj puesto en t). Avisa de la primera diferencia con k, t y ambos resúmenes."""
    partida = servicio.partida
    for numero, reloj, esperado in vivos:
        if numero > partida.acciones_jugador:
            continue                      #la decisión pendiente no se consulta por número
        obtenido = _a_plano(consultar("#", numero))
        if obtenido != esperado:
            raise AssertionError(f"Diferencia en #{numero}\nesperado: {esperado}\nobtenido: {obtenido}")
    i = 0                                  #primera entrada de `vivos` con reloj >= t
    j = -1                                 #última foto con reloj <= t
    for t in range(partida.reloj + 1):
        while i < len(vivos) and vivos[i][1] < t:
            i += 1
        while j + 1 < len(instantaneas) and instantaneas[j + 1][0] <= t:
            j += 1
        if i < len(vivos) and vivos[i][1] == t:
            esperado = vivos[i][2]
        elif j >= 0:
            esperado = con_reloj(instantaneas[j][1], t)
        else:
            continue
        obtenido = _a_plano(consultar("t", t))
        if obtenido != esperado:
            raise AssertionError(f"Diferencia en t={t}\nesperado: {esperado}\nobtenido: {obtenido}")
