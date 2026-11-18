from adapters.almacen_fichas import AlmacenFichas
from adapters.bitacora_partida import BitacoraPartida
from adapters.almacen_llaves import AlmacenLlaves
from adapters.cliente_http import ClienteHttp, ErrorCliente
from adapters.cliente_offline import ErrorOffline
from adapters.guardado_binario import CabeceraGuardado, GuardadoBinario
from controller.controlador import Controlador
from data.fabrica_modelo import FabricaModelo
from data.repositorio_catalogo import RepositorioCatalogo
from data.repositorio_cripta import RepositorioCripta, construir_grafo
from data.repositorio_llaves import RepositorioLlaves
from model.linea_tiempo_logica import K_POR_DEFECTO, LineaTiempoPartida
from service.juego_service import JuegoService
from service.verificacion_service import VerificacionService
from structures.cache_fichas import CacheFichas
from view.vista_consola import VistaConsola
from adapters.salida_replay import (imprimir_final_replay, imprimir_historia, imprimir_reporte,
                                    imprimir_termino_antes)
from adapters.salida_verificacion import imprimir_reporte_verificacion
from pathlib import Path
from adapters.guardado_binario import GuardadoBinario, ErrorGuardado
from view.vista_silenciosa import VistaSilenciosa
from data.tabla_puntajes import TablaPuntajes, Puntaje

def verificar_cripta(url, id_cripta, cliente):
    """--verificar: solo la verificación, sin vista, sin catálogo y sin juego (FR-017). Devuelve el estado de salida.

    Baja los datos y el esqueleto de la cripta una vez y pregunta (o lee lo guardado) las llaves; 0 si se puede
    ganar, 1 si no se puede o si un error de comunicación termina la ejecución.
    """
    try:
        repo = RepositorioCripta(cliente)
        repo.construir_salas(repo.cargar_esqueleto(id_cripta))
        servicio = VerificacionService(repo, RepositorioLlaves(cliente, AlmacenLlaves("cache/llaves")))
        reporte = servicio.verificar()
    except (ErrorCliente, ErrorOffline) as error:
        print(f"Error de comunicación con el servicio: {error}")
        return 1
    imprimir_reporte_verificacion(reporte)
    print(f"Solicitudes realizadas: {cliente.solicitudes_realizadas()} de {repo.datos.presupuesto_solicitudes}")
    return 0 if reporte.resoluble else 1


def _crear_servicio(app, partida, k=None):
    """El servicio con su línea de tiempo: se arma igual al jugar, al cargar y en --replay (FR-017, FR-019).

    `k`: el K de una partida cargada; si es None, el de `--checkpoint-cada` y, sin la opción, el por defecto.
    Función de módulo y no método: las pruebas viejas llaman `_sesion` y `reproducir` con una app falsa."""
    if k is None:
        k = getattr(app, "checkpoint_cada", None)
    linea = LineaTiempoPartida()
    linea.iniciar(partida, lambda: construir_grafo(app.dtos), k)
    return JuegoService(partida, app.fabrica, linea_tiempo=linea)


def k_para_carga(k_guardado, k_opcion):
    """(K que se usa, aviso o None) al cargar una partida (FR-017, FR-019).

    Gana el K guardado; si `--checkpoint-cada` se escribió (k_opcion no es None) con otro valor, se avisa.
    Un archivo sin K (k_guardado None) usa el de la opción, o el por defecto si tampoco hay opción."""
    if k_guardado is None:
        return k_opcion, None
    if k_opcion is not None and k_opcion != k_guardado:
        return k_guardado, f"Se ignora --checkpoint-cada: esta partida se guardó con K={k_guardado}."
    return k_guardado, None


## La clase aplicacion arma todas las piezas y permite jugar o reproducir una partida grabada.
class Aplicacion:
    def __init__(self, url, id_cripta, tamano_cache=25, cliente=None, checkpoint_cada=None):
        self.checkpoint_cada = checkpoint_cada     #K de --checkpoint-cada; None = no se escribió (K por defecto)
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

    def jugar(self, ruta_carga=None, forzar=False):
        vista = VistaConsola()
        try:
            #antes de empezar: ¿se puede ganar la cripta? (FR-014, FR-015, FR-016); no se repite al cargar ni en --replay
            if not self._verificar_antes_de_jugar(vista, forzar):
                return
            self.nombre_jugador = vista.pedir_nombre()
            while True:
                ruta_carga = self._sesion(vista, ruta_carga)
                if ruta_carga is None:
                    break
        finally:
            self._reportar(vista)

    def _servicio_verificacion(self):
        #con el repositorio y el cliente del juego: el esqueleto ya está bajado y la consulta de llaves comparte el presupuesto
        return VerificacionService(self.repo_cripta,
                                   RepositorioLlaves(self.cliente, AlmacenLlaves("cache/llaves")))

    def _verificar_antes_de_jugar(self, vista, forzar):
        """Devuelve True si el juego puede empezar.

        Muestra el veredicto y el orden de llaves, o el reporte. Si no se puede ganar y no hay `forzar`, False.
        Si la consulta falla, muestra el error, no da veredicto y deja empezar solo con `forzar` (FR-022).
        """
        try:
            reporte = self._servicio_verificacion().verificar()
        except (ErrorCliente, ErrorOffline) as error:
            vista.mostrar_mensaje(f"Error de comunicación con el servicio: {error}")
            return forzar
        vista.mostrar_verificacion(reporte)
        return reporte.resoluble or forzar

    def _sesion(self, vista, ruta_carga):
        semilla = None
        comandos = []
        k, aviso_k = None, None
        if ruta_carga is not None:
            guardado = GuardadoBinario()
            with open(ruta_carga, "rb") as archivo:
                cabecera = guardado.leer_cabecera(archivo)
            semilla = cabecera.semilla
            #el K guardado gana (la cabecera v2 lo trae; Fase 8)
            k, aviso_k = k_para_carga(getattr(cabecera, "k", None), getattr(self, "checkpoint_cada", None))
            comandos = guardado.leer_comandos(ruta_carga)
            self._reiniciar_salas()

        partida = self.fabrica.nueva_partida(semilla=semilla)
        partida.jugador.nombre = self.nombre_jugador
        servicio = _crear_servicio(self, partida, k)
        self.k_sesion = servicio.linea_tiempo.k          #el K en uso: es el que se guarda
        servicio.actualizar_fichas()
        bitacora = BitacoraPartida("saves")
        controlador = Controlador(servicio, vista, bitacora, self)
        datos = self.repo_cripta.datos
        try:
            bitacora.abrir(datos.id_cripta, datos.version,
                           self.repo_catalogo.version(), partida.semilla)
            self._reejecutar(controlador, vista, comandos)
            if aviso_k is not None:
                vista.mostrar_mensaje(aviso_k)       #al empezar la sesión cargada
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
        #se lee el archivo entero (cabecera, índice y comandos) antes de tocar nada: un archivo cortado en
        #cualquier parte se rechaza aquí y nunca a medio cargar (FR-018). Solo lectura.
        try:
            cab = GuardadoBinario().validar(ruta)
        except (ErrorGuardado, OSError, UnicodeDecodeError) as error:
            return f"No se puede cargar: {error}"
        datos = self.repo_cripta.datos
        if (cab.id_cripta != datos.id_cripta
                or cab.version_cripta != datos.version
                or cab.version_catalogo != self.repo_catalogo.version()):
            return "No se puede cargar: la partida es de otra cripta o versión."
        return None

    def reproducir(self, lector, hasta=None):
        """--replay; con `hasta` (entero >= 0) se detiene en cuanto el reloj llega a `hasta` y imprime el
        resumen de ese instante desde la línea de tiempo, sin vista (FR-013..FR-016)."""
        if not self._versiones_coinciden(lector):
            print("No se puede garantizar una reproducción fiel: la versión de la "
                  "cripta o del catálogo cambió desde que se grabó el log.")
            return

        partida = self.fabrica.nueva_partida(semilla=lector.semilla)
        servicio = _crear_servicio(self, partida)
        servicio.actualizar_fichas()
        controlador = Controlador(servicio, None, None, None, avisar=print)
        for comando in lector.comandos:
            if servicio.terminada() or (hasta is not None and partida.reloj >= hasta):
                break
            controlador.ejecutar(comando)
        if hasta is None:
            imprimir_final_replay(servicio.resumen_final())
        elif hasta <= partida.reloj:
            imprimir_historia(servicio.historia_por_instante(hasta))
        else:
            #el log terminó antes del instante pedido: el estado final y el aviso (FR-015)
            imprimir_historia(servicio.historia_por_instante(partida.reloj))
            imprimir_termino_antes(partida.reloj)
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
        cabecera = CabeceraGuardado(self.repo_cripta.datos.id_cripta, self.repo_cripta.datos.version, self.repo_catalogo.version(), semilla,
                                     k=getattr(self, "k_sesion", None) or K_POR_DEFECTO)
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
