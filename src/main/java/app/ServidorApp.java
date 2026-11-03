package app;

import app.Servidor.ServidorHTTP;

public class ServidorApp {
    public static void main(String[] args) throws Exception {
        new ServidorHTTP().iniciar();
    }
}