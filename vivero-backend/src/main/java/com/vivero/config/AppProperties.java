package com.vivero.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * Mapea todas las propiedades del bloque 'app.*' en application.yml.
 * Centraliza la configuracion de JWT, almacenamiento, notificaciones y OAuth.
 */
@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "app")
public class AppProperties {

    private final Jwt jwt = new Jwt();
    private final Storage storage = new Storage();
    private final Notification notification = new Notification();
    private final Cors cors = new Cors();
    private final Oauth oauth = new Oauth();
    private final VisionApi visionApi = new VisionApi();

    @Getter
    @Setter
    public static class Jwt {
        private String secret;
        private long expirationMs;
        private long refreshExpirationMs;
    }

    @Getter
    @Setter
    public static class Storage {
        private String imagesPath;
    }

    @Getter
    @Setter
    public static class Notification {
        private final Email email = new Email();
        private final Twilio twilio = new Twilio();
        private final Telegram telegram = new Telegram();

        @Getter
        @Setter
        public static class Email {
            private String from;
        }

        @Getter
        @Setter
        public static class Twilio {
            private String accountSid;
            private String authToken;
            private String fromWhatsapp;
            private String fromSms;
        }

        @Getter
        @Setter
        public static class Telegram {
            private String botToken;
            private String botUsername;
        }
    }

    @Getter
    @Setter
    public static class Cors {
        private java.util.List<String> allowedOriginPatterns = java.util.List.of("http://localhost:3000");
    }

    @Getter
    @Setter
    public static class Oauth {
        private final Provider google = new Provider();
        private final Provider apple = new Provider();

        @Getter
        @Setter
        public static class Provider {
            private String clientId;
            private String issuer;
            private String jwksUri;
        }
    }

    @Getter
    @Setter
    public static class VisionApi {
        private String provider = "gemini";
        private int timeoutSeconds = 30;
        private final Provider gemini = new Provider();
        private final Provider openai = new Provider();

        @Getter
        @Setter
        public static class Provider {
            private String key;
            private String url;
            private String model;
        }
    }
}
