from adapters.almacen_fichas import AlmacenFichas
from adapters.bitacora_partida import BitacoraPartida
from adapters.cliente_http import ClienteHttp
from adapters.guardado_binario import CabeceraGuardado, GuardadoBinario
from controller.controlador import Controlador
from data.fabrica_modelo import FabricaModelo
from data.repositorio_catalogo import RepositorioCatalogo
from data.repositorio_cripta import RepositorioCripta
from service.juego_service import JuegoService
from structures.cache_fichas import CacheFichas
from view.vista_consola import VistaConsola
from adapters.salida_replay import imprimir_final_replay, imprimir_reporte
from pathlib import Path
from adapters.guardado_binario import GuardadoBinario, ErrorGuardado
from view.vista_silenciosa import VistaSilenciosa
from data.tabla_puntajes import TablaPuntajes, Puntaje

## La clase aplicacion arma todas las piezas y permite jugar o reproducir una partida grabada.
class Aplicacion:
    def __init__(self, url, id_cripta, tamano_cache=25, cliente=None):
        self.cliente = cliente if cliente is not None else ClienteHttp(url, timeout=10)
        self.nombre_jugador = "Jugador"
        self.repo_cripta = RepositorioCripta(self.cliente)
        dtos = self.repo_cripta.cargar_esqueleto(id_cripta)
        self.repo_cripta.construir_salas(dtos)
        self.dtos = dtos

        self.cache = CacheFichas(tamano_cache)
        self.repo_catalogo = RepositorioCatalogo(
            self.cliente, self.cache, AlmacenFichas("cache/catalogo"))
        self.fabrica = FabricaModelo(self.repo_cripta, self.repo_catalogo)
        self.fabrica.iniciar()

    def jugar(self, ruta_carga=None):
        vista = VistaConsola()
        self.nombre_jugador = vista.pedir_nombre()
        try:
            while True:
                ruta_carga = self._sesion(vista, ruta_carga)
                if ruta_carga is None:
                    break
        finally:
            self._reportar(vista)

    def _sesion(self, vista, ruta_carga):
        semilla = None
        comandos = []
        if ruta_carga is not None:
            guardado = GuardadoBinario()
            with open(ruta_carga, "rb") as archivo:
                semilla = guardado.leer_cabecera(archivo).semilla
            comandos = guardado.leer_comandos(ruta_carga)
            self._reiniciar_salas()

        partida = self.fabrica.nueva_partida(semilla=semilla)
        partida.jugador.nombre = self.nombre_jugador
        servicio = JuegoService(partida, self.fabrica)
        servicio.actualizar_fichas()
        bitacora = BitacoraPartida("saves")
        controlador = Controlador(servicio, vista, bitacora, self)
        datos = self.repo_cripta.datos
        try:
            bitacora.abrir(datos.id_cripta, datos.version,
                           self.repo_catalogo.version(), partida.semilla)
            self._reejecutar(controlador, vista, comandos)
            controlador.jugar()
        finally:
            bitacora.cerrar()
        return controlador.ruta_carga

    def _reejecutar(self, controlador, vista, comandos):
        controlador.vista = VistaSilenciosa()
        for comando in comandos:
            if controlador.servicio.terminada():
                break
            controlador.ejecutar(comando)
        controlador.vista = vista

    def _reiniciar_salas(self):
        self.fabrica.marcar_en_uso([])
        contenidos = self.repo_cripta.contenidos
        self.repo_cripta.construir_salas(self.dtos)
        self.repo_cripta.contenidos = contenidos
        self.fabrica.iniciar()

    def validar_guardado(self, ruta):
        # devuelve un mensaje de error, o None si se puede cargar
        try:
            with open(ruta, "rb") as archivo:
                cab = GuardadoBinario().leer_cabecera(archivo)
        except (ErrorGuardado, OSError, UnicodeDecodeError) as error:
            return f"No se puede cargar: {error}"
        datos = self.repo_cripta.datos
        if (cab.id_cripta != datos.id_cripta
                or cab.version_cripta != datos.version
                or cab.version_catalogo != self.repo_catalogo.version()):
            return "No se puede cargar: la partida es de otra cripta o versión."
        return None

    def reproducir(self, lector):
        if not self._versiones_coinciden(lector):
            print("No se puede garantizar una reproducción fiel: la versión de la "
                  "cripta o del catálogo cambió desde que se grabó el log.")
            return

        partida = self.fabrica.nueva_partida(semilla=lector.semilla)
        servicio = JuegoService(partida, self.fabrica)
        servicio.actualizar_fichas()
        controlador = Controlador(servicio, None, None, None, avisar=print)
        for comando in lector.comandos:
            if servicio.terminada():
                break
            controlador.ejecutar(comando)
        imprimir_final_replay(servicio.resumen_final())
        imprimir_reporte(
            self.cliente.solicitudes, self.cliente.presupuesto,
            self.repo_catalogo.aciertos_memoria + self.repo_catalogo.aciertos_disco,
            self.repo_catalogo.fallos)

    def _versiones_coinciden(self, lector):
        return (lector.version_cripta == self.repo_cripta.datos.version
                and lector.version_catalogo == self.repo_catalogo.version())

    def _reportar(self, vista):
        vista.mostrar_reporte(
            self.cliente.solicitudes, self.cliente.presupuesto,
            self.repo_catalogo.aciertos_memoria + self.repo_catalogo.aciertos_disco,
            self.repo_catalogo.fallos)

    def guardar_partida(self, semilla, comandos, nombre):
        ruta = self.ruta_guardado(nombre)
        ruta.parent.mkdir(exist_ok=True)
        cabecera = CabeceraGuardado(self.repo_cripta.datos.id_cripta, self.repo_cripta.datos.version, self.repo_catalogo.version(), semilla)
        GuardadoBinario().guardar(ruta, cabecera, self.repo_cripta.contenidos, comandos)
        return ruta

    def ruta_guardado(self, nombre):
        return Path("saves") / f"{nombre}.sav"

    def registrar_puntaje(self, resumen):
        datos = self.repo_cripta.datos
        tabla = TablaPuntajes("saves/puntajes.txt")
        tabla.registrar(Puntaje(resumen.nombre_jugador, datos.id_cripta, datos.version, resumen.acciones,
                                resumen.enemigos_derrotados, resumen.reloj, resumen.victoria))
        return tabla.ordenados()
