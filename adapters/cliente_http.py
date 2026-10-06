import time
import uuid
import requests

MAX_REINTENTOS = 5


class ErrorCliente(Exception):
    """Error al comunicarse con el servicio de Cripta."""


class ClienteHttp:
    def __init__(self, url, timeout):
        self.base_url = url
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())
        self.headers = {"X-Cripta-Client-Id": self.client_id}
        self.solicitudes = 0
        self.presupuesto = None

    def asignar_presupuesto(self, n):
        self.presupuesto = n

    def solicitudes_realizadas(self):
        return self.solicitudes

    def _get(self, ruta, params=None, operacion="solicitud"):
        for _ in range(MAX_REINTENTOS):
            if self.presupuesto is not None and self.solicitudes >= self.presupuesto:
                raise ErrorCliente(f"Presupuesto agotado al intentar: {operacion}")

            self.solicitudes += 1

            try:
                respuesta = requests.get(
                    self.base_url + ruta,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout,
                )
            except requests.exceptions.RequestException as e:
                raise ErrorCliente(f"Falló la red en '{operacion}': {e}") from e

            if respuesta.status_code == 200:
                return respuesta.json()

            if respuesta.status_code == 429:
                espera = respuesta.json().get("reintentar_en", 1)
                time.sleep(espera)
                continue

            raise ErrorCliente(
                f"'{operacion}' falló con código {respuesta.status_code}"
            )

        raise ErrorCliente(f"Demasiados 429 seguidos en '{operacion}'")

    def listar_criptas(self):
        return self._get("/criptas", operacion="listar criptas")

    def contenido_salas(self, id_cripta, ids_salas):
        salas = ",".join(str(s) for s in ids_salas)
        return self._get(
            f"/criptas/{id_cripta}/contenido",
            params={"salas": salas},
            operacion=f"descargar contenido de salas {salas}",
        )

    def datos_cripta(self, id_cripta):
        return self._get(f"/criptas/{id_cripta}", 
                         operacion=f"obtener datos de cripta {id_cripta}")

    def version_cripta(self, id_cripta):
        return self._get(f"/criptas/{id_cripta}/version",
                          operacion=f"obtener versión de cripta {id_cripta}")

    def version_catalogo(self):
        return self._get("/catalogo/version", 
                         operacion="obtener versión de catálogos")

    def catalogo(self, ids):
        lista = ",".join(ids)
        return self._get(
            "/catalogo",
            params={"ids": lista},
            operacion=f"descargar catálogo de {lista}",
        )

    def pagina_esqueleto(self, id_cripta, pagina):
        return self._get(
            f"/criptas/{id_cripta}/salas",
            params={"pagina": pagina},
            operacion=f"descargar página {pagina} del esqueleto de {id_cripta}",
        )

    