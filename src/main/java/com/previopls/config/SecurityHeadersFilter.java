package com.previopls.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * Headers de segurança aplicados a todas as respostas da API.
 *
 * O CSP restritivo (default-src 'none') é aplicado nos endpoints de negócio
 * — eles só respondem JSON e não devem carregar nenhum recurso de origem.
 *
 * Para os paths de documentação ({@code /docs}, {@code /swagger-ui/*},
 * {@code /v3/api-docs/*}) usamos um CSP mais permissivo permitindo {@code 'self'}
 * + inline + a CDN do Swagger UI configurada no application.yml, senão o
 * próprio Swagger UI fica em branco no navegador (sem CSS/JS).
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 20)
public class SecurityHeadersFilter extends OncePerRequestFilter {

    private static final String CSP_DOCS =
            "default-src 'self'; " +
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " +
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " +
            "img-src 'self' data: https://cdn.jsdelivr.net; " +
            "font-src 'self' data: https://cdn.jsdelivr.net; " +
            "connect-src 'self'; " +
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'";

    private static final String CSP_API =
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        response.setHeader("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload");
        response.setHeader("X-Frame-Options", "DENY");
        response.setHeader("X-Content-Type-Options", "nosniff");
        response.setHeader("Referrer-Policy", "no-referrer");
        response.setHeader("Permissions-Policy",
                "geolocation=(), microphone=(), camera=(), payment=(), usb=()");

        String path = request.getRequestURI();
        boolean isDocs = path.startsWith("/docs")
                || path.startsWith("/swagger-ui")
                || path.startsWith("/v3/api-docs")
                || path.equals("/swagger-ui.html");

        response.setHeader("Content-Security-Policy", isDocs ? CSP_DOCS : CSP_API);

        chain.doFilter(request, response);
    }
}
