package com.previopls.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI previoPlsOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("PrevioPLS API")
                        .version("v1")
                        .description("API REST da plataforma Ford Predict & Care (PrevioPLS). " +
                                "Backend SOA para retenção pós-venda. Atende às histórias US01–US07.")
                        .contact(new Contact().name("Equipe PrevioPLS — Challenge Ford FIAP 2026")))
                .servers(List.of(
                        new Server().url("http://localhost:5000").description("Local"),
                        new Server().url("https://api.previopls.example.com").description("Produção")
                ))
                .components(new Components()
                        .addSecuritySchemes("bearerAuth", new SecurityScheme()
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")))
                .addSecurityItem(new SecurityRequirement().addList("bearerAuth"));
    }
}
