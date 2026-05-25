package com.previopls.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.previopls.dto.ErrorResponse;
import com.previopls.entity.enums.AuditAction;
import com.previopls.service.AuditService;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;
    private final AuditService auditService;
    private final String[] allowedOrigins;

    public SecurityConfig(JwtAuthFilter jwtAuthFilter,
                          @Lazy AuditService auditService,
                          @Value("${app.cors.allowed-origins:*}") String allowedOrigins) {
        this.jwtAuthFilter = jwtAuthFilter;
        this.auditService = auditService;
        this.allowedOrigins = Arrays.stream(allowedOrigins.split(","))
                .map(String::trim)
                .toArray(String[]::new);
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        ObjectMapper json = new ObjectMapper();
        http
                .csrf(AbstractHttpConfigurer::disable)
                .cors(c -> c.configurationSource(corsConfigurationSource()))
                .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(
                                "/health", "/version",
                                "/v1/auth/login",
                                "/v3/api-docs/**", "/v3/api-docs.yaml",
                                "/docs", "/docs/**", "/swagger-ui.html", "/swagger-ui/**"
                        ).permitAll()
                        .anyRequest().authenticated()
                )
                .exceptionHandling(e -> e
                        .authenticationEntryPoint((req, resp, ex) -> {
                            auditService.log(AuditAction.UNAUTHORIZED_ACCESS,
                                    null, null, null, null, req.getRequestURI(), ex.getMessage());
                            writeJson(resp, json, HttpServletResponse.SC_UNAUTHORIZED,
                                    "UNAUTHORIZED", "Não autenticado");
                        })
                        .accessDeniedHandler((req, resp, ex) -> {
                            auditService.log(AuditAction.FORBIDDEN_ACCESS,
                                    null, null, null, null, req.getRequestURI(), ex.getMessage());
                            writeJson(resp, json, HttpServletResponse.SC_FORBIDDEN,
                                    "FORBIDDEN", "Acesso negado");
                        })
                )
                .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration cfg = new CorsConfiguration();
        cfg.setAllowedOriginPatterns(List.of(allowedOrigins));
        cfg.setAllowedMethods(List.of("GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"));
        cfg.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-Request-Id"));
        cfg.setExposedHeaders(List.of("X-Request-Id"));
        cfg.setAllowCredentials(true);
        cfg.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", cfg);
        return source;
    }

    private void writeJson(HttpServletResponse resp, ObjectMapper json, int status, String code, String message)
            throws java.io.IOException {
        resp.setStatus(status);
        resp.setContentType(MediaType.APPLICATION_JSON_VALUE);
        resp.setCharacterEncoding("UTF-8");
        resp.getWriter().write(json.writeValueAsString(ErrorResponse.of(code, message)));
    }
}
