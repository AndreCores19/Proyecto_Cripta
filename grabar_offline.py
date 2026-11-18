import json
import os
import shutil

from adapters.cliente_http import ClienteHttp
from main import URL

CARPETA = "offline"


def guardar(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False)

def ids_del_contenido(contenido):
    ids = []
    for sala in contenido:
        for enemigo in sala["enemigos"]:
            ids.append(enemigo["tipo"])
        for objeto in sala["objetos"]:
            ids.append(objeto)
        for trampa in sala["trampas"]:
            ids.append(trampa["tipo"])
    return ids

def completar_catalogo(cliente, pendientes, entidades, conocidas):
    while True:
        nuevos = []
        for id_ficha in pendientes:
            if id_ficha not in conocidas and id_ficha not in nuevos:
                nuevos.append(id_ficha)
        if not nuevos:
            return
        pendientes = []
        for i in range(0, len(nuevos), 10):
            lote = nuevos[i:i + 10]
            respuesta = cliente.catalogo(lote)
            for ficha in respuesta["entidades"]:
                entidades.append(ficha)
                for suelto in ficha.get("suelta", []):
                    pendientes.append(suelto)
            conocidas.extend(lote)

def quitar_criptas_no_servidas(carpeta, servidas):
    """Quita del paquete las carpetas de criptas que el servicio no lista (FR-006).

    Toca solo subcarpetas directas de `carpeta` que son criptas del paquete (tienen `datos.json`) y cuyo
    nombre no está en `servidas`. Se llama solo cuando el listado salió bien, no estaba vacío y todas las
    criptas se grabaron sin error.
    """
    for nombre in os.listdir(carpeta):
        ruta = os.path.join(carpeta, nombre)
        if (os.path.isdir(ruta) and nombre not in servidas
                and os.path.exists(os.path.join(ruta, "datos.json"))):
            shutil.rmtree(ruta)


def grabar():
    base = ClienteHttp(URL, timeout=10)
    criptas = base.listar_criptas()
    guardar(f"{CARPETA}/criptas.json", criptas)
    guardar(f"{CARPETA}/catalogo_version.json", base.version_catalogo())

    entidades = []
    conocidas = []
    for resumen in criptas["criptas"]:
        id_cripta = resumen["id"]
        cliente = ClienteHttp(URL, timeout=10)    # un cliente por cripta: presupuesto aparte
        datos = cliente.datos_cripta(id_cripta)
        guardar(f"{CARPETA}/{id_cripta}/datos.json", datos)

        salas = []
        pagina = 1
        while True:
            esqueleto = cliente.pagina_esqueleto(id_cripta, pagina)
            guardar(f"{CARPETA}/{id_cripta}/esqueleto_{pagina}.json", esqueleto)
            salas.extend(esqueleto["salas"])
            if pagina >= esqueleto["total_paginas"]:
                break
            pagina += 1

        ids_salas = []
        for sala in salas:
            ids_salas.append(sala["id"])
        contenido = []
        for i in range(0, len(ids_salas), 10):
            respuesta = cliente.contenido_salas(id_cripta, ids_salas[i:i + 10])
            contenido.extend(respuesta["contenido"])
        guardar(f"{CARPETA}/{id_cripta}/contenido.json", {"contenido": contenido})

        guardar(f"{CARPETA}/{id_cripta}/llaves.json", cliente.llaves(id_cripta))   # dónde está cada llave (FR-006)

        pendientes = ids_del_contenido(contenido)
        pendientes.append(datos["llave_salida"])
        completar_catalogo(cliente, pendientes, entidades, conocidas)
        print(f"{id_cripta}: {len(salas)} salas, {cliente.solicitudes} solicitudes")

    guardar(f"{CARPETA}/catalogo.json", {"entidades": entidades})
    # solo se llega aquí si el listado salió bien y todas las criptas se grabaron: una excepción corta antes
    servidas = [resumen["id"] for resumen in criptas["criptas"]]
    if servidas:
        quitar_criptas_no_servidas(CARPETA, servidas)
    print(f"Catálogo: {len(entidades)} fichas. Paquete en '{CARPETA}/'.")

if __name__ == "__main__":
    grabar()