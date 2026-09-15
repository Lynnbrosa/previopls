package com.previopls.config;

import com.previopls.security.RequestContext;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

/**
 * Garante um identificador de correlação por requisição.
 *
 * - Se o cliente enviar {@code X-Request-Id}, reusa.
 * - Caso contrário, gera UUID.
 * - Coloca em {@link MDC} (visível em todo log da requisição) e ecoa no header de resposta.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestIdFilter extends OncePerRequestFilter {

    private static final int MAX_REQUEST_ID_LENGTH = 36;
    private static final java.util.regex.Pattern SAFE_REQUEST_ID =
            java.util.regex.Pattern.compile("^[A-Za-z0-9._-]+$");

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String requestId = request.getHeader(RequestContext.HEADER_REQUEST_ID);
        // audit_logs.request_id é VARCHAR(36): aceita UUID canônico (36) ou hex (32),
        // que é o formato propagado pelo Gateway. Qualquer coisa fora disso é regenerada.
        if (requestId == null || requestId.isBlank()
                || requestId.length() > MAX_REQUEST_ID_LENGTH
                || !SAFE_REQUEST_ID.matcher(requestId).matches()) {
            requestId = UUID.randomUUID().toString();
        }
        MDC.put(RequestContext.MDC_REQUEST_ID, requestId);
        response.setHeader(RequestContext.HEADER_REQUEST_ID, requestId);
        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove(RequestContext.MDC_REQUEST_ID);
        }
    }
}
