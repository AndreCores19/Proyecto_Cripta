import sys
import argparse
from aplicacion import Aplicacion
from adapters.lector_bitacora import LectorBitacora, ErrorBitacora

URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


def main():
    parser = argparse.ArgumentParser(description="Cripta")
    parser.add_argument("cripta", nargs="?", help="id de la cripta a jugar")
    parser.add_argument("--replay", metavar="LOG", help="reproduce una partida grabada")
    parser.add_argument("--cache-size", type=int, default=25, dest="tamano_cache",
                        help="fichas máximas en memoria (por defecto 25)")
    parser.add_argument("--bench", action="store_true",
                        help="ejecuta los benchmarks y termina")
    parser.add_argument("--offline", action="store_true",
                        help="usa el paquete de respuestas de offline/ en vez de la red")
    args = parser.parse_args()

    if args.bench:
        from bench import (bench_agenda, bench_bitacora, bench_ciclo,
                           bench_historial, bench_inventario,
                           bench_ordenamientos, bench_rastro,
                           bench_guardado, bench_cache, bench_fichas, bench_replay,
                           bench_precarga, bench_catalogo, bench_cazador)
        for modulo in (bench_ciclo, bench_historial, bench_agenda,
                       bench_inventario, bench_bitacora, bench_ordenamientos,
                       bench_rastro, bench_cache, bench_guardado, bench_fichas,
                       bench_replay, bench_precarga, bench_catalogo, bench_cazador):
            modulo.ejecutar()
            print()
            if modulo is bench_ciclo:
                bench_ciclo.ejecutar_modos()  #el ciclo con cada modo del decisor de cazadores
                print()
        return

    if args.tamano_cache < 1:
        parser.error("--cache-size debe ser al menos 1")
    from adapters.cliente_http import ClienteHttp
    if args.offline:
        from adapters.cliente_offline import ClienteOffline
        cliente = ClienteOffline("offline")
    else:
        cliente = ClienteHttp(URL, timeout=10)
    if args.replay:
        lector = LectorBitacora(args.replay)
        try:
            lector.leer()
        except (ErrorBitacora, FileNotFoundError) as error:
            print(f"No se pudo leer la bitácora: {error}")
            sys.exit(1)
        Aplicacion(URL, lector.cripta, args.tamano_cache, cliente).reproducir(lector)
    elif args.cripta:
        Aplicacion(URL, args.cripta, args.tamano_cache, cliente).jugar()
    else:
        from view.vista_consola import VistaConsola
        id_cripta = VistaConsola().elegir_cripta(cliente.listar_criptas()["criptas"])
        if id_cripta is not None:
            Aplicacion(URL, id_cripta, args.tamano_cache, cliente).jugar()
if __name__ == "__main__":
    from adapters.cliente_http import ErrorCliente
    from adapters.cliente_offline import ErrorOffline
    try:
        main()
    except (ErrorCliente, ErrorOffline) as error:
        print(f"Error de comunicación con el servicio: {error}")
        sys.exit(1)