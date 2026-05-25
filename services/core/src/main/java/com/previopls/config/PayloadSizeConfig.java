package com.previopls.config;

import org.apache.catalina.connector.Connector;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Limites no nível do servlet container para evitar abuse de payloads grandes.
 *
 * - max-post-size de 1MB (cobertura ampla para JSON da API).
 * - max-http-header-size 16KB (defesa contra header smuggling).
 */
@Configuration
public class PayloadSizeConfig {

    private static final int MAX_POST_BYTES = 1024 * 1024;
    private static final int MAX_HEADER_BYTES = 16 * 1024;

    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> tomcatHardening() {
        return factory -> factory.addConnectorCustomizers((Connector connector) -> {
            connector.setMaxPostSize(MAX_POST_BYTES);
            connector.setProperty("maxHttpHeaderSize", String.valueOf(MAX_HEADER_BYTES));
            connector.setProperty("maxParameterCount", "100");
        });
    }
}
