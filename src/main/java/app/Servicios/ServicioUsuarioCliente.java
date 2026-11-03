package app.Servicios;

import app.DTO.UsuarioDTO;
import com.google.gson.Gson;
import java.net.ConnectException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Map;

public class ServicioUsuarioCliente {
    private final HttpClient cliente = HttpClient.newHttpClient();
    private final Gson gson = new Gson();

    public UsuarioDTO iniciarSesion(String id, String clave) throws Exception {
        String cuerpo = "id=" + codificar(id) + "&clave=" + codificar(clave);

        HttpRequest solicitud = HttpRequest.newBuilder()
                .uri(URI.create(ConfigCliente.URL_SERVIDOR + "/usuario/login"))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(cuerpo))
                .build();

        HttpResponse<String> respuesta;
        try {
            respuesta = cliente.send(solicitud, HttpResponse.BodyHandlers.ofString());
        } catch (ConnectException e) {
            throw new Exception("No se pudo conectar con el servidor.");
        }

        if (respuesta.statusCode() != 200) {
            throw new Exception(leerError(respuesta.body()));
        }
        return gson.fromJson(respuesta.body(), UsuarioDTO.class);
    }

    private String codificar(String valor) {
        return URLEncoder.encode(valor == null ? "" : valor, StandardCharsets.UTF_8);
    }

    private String leerError(String cuerpo) {
        try {
            Map<?, ?> mapa = gson.fromJson(cuerpo, Map.class);
            Object error = mapa.get("error");
            return error != null ? error.toString() : "Error del servidor.";
        } catch (Exception e) {
            return "Error del servidor.";
        }
    }
}