package app.Servidor;

import com.google.gson.Gson;
import com.sun.net.httpserver.HttpExchange;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

public class HttpUtil {

    private static final Gson gson = new Gson();

    public static String leerCuerpo(HttpExchange exchange) throws IOException {
        byte[] bytes = exchange.getRequestBody().readAllBytes();
        return new String(bytes, StandardCharsets.UTF_8);
    }

    public static Map<String, String> obtenerParametros(String cuerpo) {
        Map<String, String> parametros = new HashMap<>();
        if (cuerpo == null || cuerpo.isBlank()) {
            return parametros;
        }

        for (String par : cuerpo.split("&")) {
            String[] partes = par.split("=", 2);
            if (partes.length == 2) {
                String clave = URLDecoder.decode(partes[0], StandardCharsets.UTF_8);
                String valor = URLDecoder.decode(partes[1], StandardCharsets.UTF_8);
                parametros.put(clave, valor);
            }
        }
        return parametros;
    }

    public static void enviarRespuesta(HttpExchange exchange, int codigo, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);

        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
        exchange.sendResponseHeaders(codigo, bytes.length);

        try (OutputStream salida = exchange.getResponseBody()) {
            salida.write(bytes);
        }
    }

    public static void enviarError(HttpExchange exchange, int codigo, String mensaje) throws IOException {
        if (mensaje == null || mensaje.isBlank()) {
            mensaje = "Error desconocido";
        }
        Map<String, String> error = new HashMap<>();
        error.put("error", mensaje);
        enviarRespuesta(exchange, codigo, gson.toJson(error));
    }

    public static String aJson(Object objeto) {
        return gson.toJson(objeto);
    }
}