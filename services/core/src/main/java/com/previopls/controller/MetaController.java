package com.previopls.controller;

import com.previopls.dto.meta.HealthResponse;
import com.previopls.dto.meta.VersionResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirements;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@Tag(name = "meta", description = "Saúde e descoberta do serviço")
public class MetaController {

    private final JdbcTemplate jdbc;
    private final String version;
    private final String build;

    public MetaController(JdbcTemplate jdbc,
                          @Value("${app.info.version:v1}") String version,
                          @Value("${app.info.build:1.0.0}") String build) {
        this.jdbc = jdbc;
        this.version = version;
        this.build = build;
    }

    @GetMapping("/health")
    @SecurityRequirements
    @Operation(summary = "Liveness/readiness — checa conectividade com o banco")
    public ResponseEntity<HealthResponse> health() {
        try {
            jdbc.queryForObject("SELECT 1", Integer.class);
            return ResponseEntity.ok(new HealthResponse("ok", Map.of("database", "up")));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(new HealthResponse("degraded", Map.of("database", "down")));
        }
    }

    @GetMapping("/version")
    @SecurityRequirements
    @Operation(summary = "Versão da API e build atual")
    public VersionResponse version() {
        return new VersionResponse("PrevioPLS API", version, build);
    }
}
