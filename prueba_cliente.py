from adapters.cliente_http import ClienteHttp, ErrorCliente

URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"
cliente = ClienteHttp(URL, timeout=10)

try:
    # 1. Datos generales: de aquí sale el presupuesto
    datos = cliente.datos_cripta("cripta-01")
    print(datos)
    cliente.asignar_presupuesto(datos["presupuesto_solicitudes"])

    # 2. Versión de la cripta y del catálogo
    print(cliente.version_cripta("cripta-01"))
    print(cliente.version_catalogo())

    # 3. Esqueleto: página 1
    pagina = cliente.pagina_esqueleto("cripta-01", 1)
    print(pagina)
    ids_salas = [sala["id"] for sala in pagina["salas"]]

    # 4. Contenido de las salas que salieron en el esqueleto
    contenido = cliente.contenido_salas("cripta-01", ids_salas)
    print(contenido)

    # 5. Catálogo: con los tipos que aparecieron en el contenido
    tipos = []
    for sala in contenido["contenido"]:
        for enemigo in sala["enemigos"]:
            tipos.append(enemigo["tipo"])
        tipos.extend(sala["objetos"])
        for trampa in sala["trampas"]:
            tipos.append(trampa["tipo"])
    tipos = list(set(tipos))[:10]          # sin repetir, máximo 10
    print(cliente.catalogo(tipos))

except ErrorCliente as e:
    print("Error:", e)

print("Solicitudes:", cliente.solicitudes_realizadas())