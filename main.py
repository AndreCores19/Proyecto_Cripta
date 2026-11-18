import sys
import argparse
from aplicacion import Aplicacion, verificar_cripta
from adapters.lector_bitacora import LectorBitacora, ErrorBitacora

URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


def _es_entero_no_negativo(texto):
    #solo cifras 0-9: sin signo, sin punto, sin exponente
    return texto != "" and all(c in "0123456789" for c in texto)


def _k_positivo(texto):
    #--checkpoint-cada: entero >= 1; cualquier otro valor lo rechaza argparse (salida 2) antes de correr nada
    if not _es_entero_no_negativo(texto) or int(texto) < 1:
        raise argparse.ArgumentTypeError(f"debe ser un entero positivo (se recibió «{texto}»)")
    return int(texto)


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
    parser.add_argument("--verificar", metavar="CRIPTA",
                        help="verifica si la cripta se puede ganar, imprime el reporte y termina")
    parser.add_argument("--forzar", action="store_true",
                        help="juega aunque la cripta no se pueda ganar")
    parser.add_argument("--hasta", metavar="T",
                        help="con --replay: reproduce hasta el instante T (entero >= 0) e imprime "
                             "el estado de ese instante")
    parser.add_argument("--checkpoint-cada", metavar="K", type=_k_positivo, default=None,
                        dest="checkpoint_cada",
                        help="acciones entre puntos de control de la línea de tiempo (entero >= 1; "
                             "por defecto el K medido); al cargar una partida gana el K con que se guardó")
    args = parser.parse_args()

    hasta = None
    if args.hasta is not None:
        if not args.replay:
            parser.error("--hasta solo se puede usar con --replay")
        if not _es_entero_no_negativo(args.hasta):
            print(f"--hasta debe ser un entero mayor o igual a 0 (se recibió «{args.hasta}»)")
            sys.exit(1)
        hasta = int(args.hasta)

    if args.bench:
        from bench import (bench_agenda, bench_bitacora, bench_ciclo,
                           bench_historial, bench_inventario,
                           bench_ordenamientos, bench_rastro,
                           bench_guardado, bench_cache, bench_fichas, bench_replay,
                           bench_precarga, bench_catalogo, bench_cazador, bench_ir_a, bench_solvabilidad)
        for modulo in (bench_ciclo, bench_historial, bench_agenda,
                       bench_inventario, bench_bitacora, bench_ordenamientos,
                       bench_rastro, bench_cache, bench_guardado, bench_fichas,
                       bench_replay, bench_precarga, bench_catalogo, bench_cazador,
                       bench_ir_a, bench_solvabilidad):
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
    if args.verificar:
        sys.exit(verificar_cripta(URL, args.verificar, cliente))
    if args.replay:
        lector = LectorBitacora(args.replay)
        try:
            lector.leer()
        except (ErrorBitacora, FileNotFoundError) as error:
            print(f"No se pudo leer la bitácora: {error}")
            sys.exit(1)
        Aplicacion(URL, lector.cripta, args.tamano_cache, cliente, args.checkpoint_cada).reproducir(lector, hasta=hasta)
    elif args.cripta:
        Aplicacion(URL, args.cripta, args.tamano_cache, cliente, args.checkpoint_cada).jugar(forzar=args.forzar)
    else:
        from view.vista_consola import VistaConsola
        id_cripta = VistaConsola().elegir_cripta(cliente.listar_criptas()["criptas"])
        if id_cripta is not None:
            Aplicacion(URL, id_cripta, args.tamano_cache, cliente, args.checkpoint_cada).jugar(forzar=args.forzar)
if __name__ == "__main__":
    from adapters.cliente_http import ErrorCliente
    from adapters.cliente_offline import ErrorOffline
    try:
        main()
    except (ErrorCliente, ErrorOffline) as error:
        print(f"Error de comunicación con el servicio: {error}")
        sys.exit(1)