package com.vivero.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * Mapea todas las propiedades del bloque 'app.*' en application.yml.
 * Centraliza la configuración de JWT, almacenamiento y notificaciones.
 *
 * Se inyecta con @Autowired o constructor en cualquier clase que lo necesite.
 */
@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "app")
public class AppProperties {

    private final Auth auth = new Auth();
    private final Jwt jwt = new Jwt();
    private final Storage storage = new Storage();
    private final Notification notification = new Notification();
    private final Cors cors = new Cors();
    private String publicBaseUrl;

    @Getter
    @Setter
    public static class Auth {
        private final Google google = new Google();

        @Getter
        @Setter
        public static class Google {
            private String clientId;
        }
    }

    @Getter
    @Setter
    public static class Jwt {
        // Clave secreta para firmar tokens — viene de variable de entorno JWT_SECRET
        private String secret;
        // Tiempo de expiración del access token en milisegundos (default: 24h)
        private long expirationMs;
        // Tiempo de expiración del refresh token en milisegundos (default: 7 días)
        private long refreshExpirationMs;
    }

    @Getter
    @Setter
    public static class Storage {
        // Ruta base donde se guardan las imágenes del robot — volumen Docker
        private String imagesPath;
    }

    @Getter
    @Setter
    public static class Notification {
        private final Email email = new Email();

        @Getter
        @Setter
        public static class Email {
            private String from;
        }
    }

    @Getter
    @Setter
    public static class Cors {
        /**
         * Lista de orígenes permitidos para CORS.
         * Spring puede enlazar una lista separada por comas desde variables de entorno.
         */
        private java.util.List<String> allowedOriginPatterns = java.util.List.of("http://localhost:3000");
    }
}
