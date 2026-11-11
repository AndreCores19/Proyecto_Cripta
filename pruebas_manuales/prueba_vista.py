from adapters.cliente_http import ClienteHttp
from adapters.almacen_fichas import AlmacenFichas
from data.repositorio_cripta import RepositorioCripta
from data.repositorio_catalogo import RepositorioCatalogo
from data.fabrica_modelo import FabricaModelo
from structures.cache_fichas import CacheFichas
from service.juego_service import JuegoService
from view.vista_consola import VistaConsola

URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
ID_CRIPTA = "cripta-01"

cliente = ClienteHttp(URL, timeout=10)
repo_cripta = RepositorioCripta(cliente)
dtos = repo_cripta.cargar_esqueleto(ID_CRIPTA)
repo_cripta.construir_salas(dtos)

repo_catalogo = RepositorioCatalogo(cliente, CacheFichas(25), AlmacenFichas("cache/catalogo"))
fabrica = FabricaModelo(repo_cripta, repo_catalogo)
fabrica.iniciar()

partida = fabrica.nueva_partida(semilla=1)
vista = VistaConsola()
servicio = JuegoService(partida, fabrica)

vista.mostrar_estado(servicio.estado_vista())

# Probar que moverse cambia lo que se ve
sala = partida.jugador.sala
for salida in sala.salidas:
    if not salida.cerrada:
        fabrica.poblar_sala(salida.destino)
        partida.mover(salida.direccion)
        break

vista.mostrar_estado(servicio.estado_vista())
print("Solicitudes:", cliente.solicitudes_realizadas())