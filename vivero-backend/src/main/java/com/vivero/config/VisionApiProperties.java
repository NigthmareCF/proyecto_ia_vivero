package com.vivero.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "vision.api")
public class VisionApiProperties {

    private boolean enabled = false;
    private String provider = "gemini";
    private String model = "gemini-2.5-flash";
    private int timeoutSeconds = 30;
    private final Gemini gemini = new Gemini();
    private final LocalVlm localVlm = new LocalVlm();
    private final Patrol patrol = new Patrol();

    @Getter
    @Setter
    public static class Gemini {
        private String key;
        private String url = "https://generativelanguage.googleapis.com/v1beta/models";
    }

    @Getter
    @Setter
    public static class LocalVlm {
        private boolean enabled = false;
        private String url = "http://localhost:8000/v1";
        private String model = "qwen-vl-local";
        private int timeoutSeconds = 120;
    }

    @Getter
    @Setter
    public static class Patrol {
        private boolean classifierEnabled = true;
        private boolean geminiReportEnabled = true;
    }
}
