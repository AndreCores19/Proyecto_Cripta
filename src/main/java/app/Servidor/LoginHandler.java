package app.Servidor;

import app.DTO.UsuarioDTO;
import app.Servicios.ServicioUsuario;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.IOException;
import java.util.Map;

public class LoginHandler implements HttpHandler {

    private final ServicioUsuario servicioUsuario = new ServicioUsuario();

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        try {
            // validar POST
            if(!exchange.getRequestMethod().equalsIgnoreCase("POST")) {
                HttpUtil.enviarError(exchange, 405, "Método no permitido");
                return;
            }
            // leer parámetros, sacar id y clave
            String cuerpo = HttpUtil.leerCuerpo(exchange);
            Map<String, String> parametros = HttpUtil.obtenerParametros(cuerpo);
            String id = parametros.get("id");
            String clave = parametros.get("clave");

            UsuarioDTO usuario;
            try {
                usuario = servicioUsuario.iniciarSesion(id, clave);
            } catch (Exception e) {
                HttpUtil.enviarError(exchange, 401, e.getMessage());
                return;
            }
            // quitar la clave
            usuario.setClave(null);
            // responder 200
            HttpUtil.enviarRespuesta(exchange, 200, HttpUtil.aJson(usuario));
        } catch (Exception e) {
            e.printStackTrace();
            HttpUtil.enviarError(exchange, 500, "Error interno del servidor");
        }
    }
}

