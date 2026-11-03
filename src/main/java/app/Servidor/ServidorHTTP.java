package app.Servidor;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.concurrent.Executors;

public class ServidorHTTP {

    public static final int PUERTO = 8080;
    private HttpServer servidor;

    public void iniciar() throws IOException {
        // 1. crear
        servidor = HttpServer.create(new InetSocketAddress("0.0.0.0", PUERTO), 0);

        // 2. registrar rutas
        servidor.createContext("/usuario/login", new LoginHandler());

        // 3. executor
        servidor.setExecutor(Executors.newFixedThreadPool(10));

        // 4. arrancar
        servidor.start();

        // mensajes de consola
        System.out.println("Servidor iniciado en el puerto " + PUERTO);
        System.out.println("POST /usuario/login");
    }
}
