package app.ui;

import app.Controllers.SesionActual;
import app.DTO.UsuarioDTO;
import app.Servicios.ServicioUsuarioCliente;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Hyperlink;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;
import javafx.scene.control.Alert;

public class LoginViewController {
    @FXML private TextField txtIdLogin;
    @FXML private PasswordField txtPwdLogin;
    @FXML private Button btnLogin;
    @FXML private Button btnCancelar;
    @FXML private Hyperlink hyperPwd;

    private ServicioUsuarioCliente servicioUsuario = new ServicioUsuarioCliente();
    @FXML
    private void initialize() {
        btnLogin.setOnAction(event -> intentarLogin());
        btnCancelar.setOnAction(event -> cancelarLogin(event));
        hyperPwd.setOnAction(event -> irACambiarClave(event));
    }

    private void intentarLogin() {
        String id = txtIdLogin.getText().trim();
        String clave = txtPwdLogin.getText().trim();
        if (id.isEmpty() || clave.isEmpty()) {
            Alert alerta = new Alert(Alert.AlertType.WARNING, "Por favor, complete todos los campos.");
            alerta.showAndWait();
            return;
        }
        try {
            UsuarioDTO usuario = servicioUsuario.iniciarSesion(id, clave);
            SesionActual.setUsuarioActual(usuario);
            String vistaDestino;
            if ("ADMIN".equals(usuario.getRol())) {
                vistaDestino = "/app/ui/SistemaDeReservasFuncionarioAdmin.fxml";
            } else {
                vistaDestino = "/app/ui/SistemaDeReservasFuncionario.fxml";
            }

            javafx.scene.Parent raiz = javafx.fxml.FXMLLoader.load(getClass().getResource(vistaDestino));
            javafx.stage.Stage stage = (javafx.stage.Stage) btnLogin.getScene().getWindow();
            stage.setWidth(800);
            stage.setHeight(700);
            stage.getScene().setRoot(raiz);
            stage.setWidth(900);
            stage.setHeight(700);
            stage.centerOnScreen();

        } catch (Exception e) {
            e.printStackTrace();
            mostrarError(e.getMessage() != null ? e.getMessage() : "Error al iniciar sesión.");
        }
    }

    private void irACambiarClave(javafx.event.ActionEvent event) {
        String id = txtIdLogin.getText();
        String clave = txtPwdLogin.getText();
        try {
            UsuarioDTO usuario = servicioUsuario.iniciarSesion(id, clave);
            SesionActual.setUsuarioActual(usuario);

            javafx.scene.Parent raiz = javafx.fxml.FXMLLoader.load(
                    getClass().getResource("/app/ui/cambiarClave-view.fxml"));
            javafx.stage.Stage stage = (javafx.stage.Stage) ((javafx.scene.Node) event.getSource()).getScene().getWindow();
            stage.getScene().setRoot(raiz);

        } catch (Exception e) {
            mostrarError(e.getMessage());
        }
    }
    private void mostrarError(String mensaje) {
        Alert alerta = new Alert(Alert.AlertType.ERROR);
        alerta.setTitle("Error de inicio de sesión. ");
        alerta.setHeaderText(null);
        alerta.setContentText(mensaje);
        alerta.showAndWait();
    }
    private void cancelarLogin(javafx.event.ActionEvent event) {
        javafx.stage.Stage stage = (javafx.stage.Stage) ((javafx.scene.Node) event.getSource()).getScene().getWindow();
        stage.close();
    }
}