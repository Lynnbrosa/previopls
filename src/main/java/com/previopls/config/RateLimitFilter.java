package com.previopls.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.previopls.dto.ErrorResponse;
import com.previopls.security.RequestContext;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.Refill;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Rate limiting in-memory por IP usando Bucket4j (token bucket).
 *
 * - Endpoint de login tem limite agressivo (anti-brute-force).
 * - Demais endpoints têm um teto generoso para uso interno.
 *
 * Em produção com múltiplas réplicas, trocar o storage em memória
 * por um backend distribuído (ex.: Redis via bucket4j-redis).
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class RateLimitFilter extends OncePerRequestFilter {

    private final int loginPerMinute;
    private final int defaultPerMinute;
    private final ObjectMapper json = new ObjectMapper();

    private final ConcurrentHashMap<String, Bucket> loginBuckets = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, Bucket> defaultBuckets = new ConcurrentHashMap<>();

    public RateLimitFilter(
            @Value("${app.security.rate-limit.login-per-minute:5}") int loginPerMinute,
            @Value("${app.security.rate-limit.default-per-minute:200}") int defaultPerMinute) {
        this.loginPerMinute = loginPerMinute;
        this.defaultPerMinute = defaultPerMinute;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String path = request.getRequestURI();

        if ("/health".equals(path) || "/version".equals(path)) {
            chain.doFilter(request, response);
            return;
        }

        String ip = RequestContext.remoteIp();
        if (ip == null) ip = "unknown";

        boolean isLogin = path.endsWith("/v1/auth/login");
        Bucket bucket = isLogin
                ? loginBuckets.computeIfAbsent(ip, k -> newBucket(loginPerMinute))
                : defaultBuckets.computeIfAbsent(ip, k -> newBucket(defaultPerMinute));

        if (!bucket.tryConsume(1)) {
            writeRateLimited(response, isLogin ? loginPerMinute : defaultPerMinute);
            return;
        }
        chain.doFilter(request, response);
    }

    private static Bucket newBucket(int perMinute) {
        Bandwidth limit = Bandwidth.classic(
                perMinute,
                Refill.intervally(perMinute, Duration.ofMinutes(1))
        );
        return Bucket.builder().addLimit(limit).build();
    }

    private void writeRateLimited(HttpServletResponse response, int perMinute) throws IOException {
        response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        response.setHeader("Retry-After", "60");
        response.setHeader("X-RateLimit-Limit", String.valueOf(perMinute));
        ErrorResponse body = ErrorResponse.of(
                "RATE_LIMIT_EXCEEDED",
                "Limite de requisições excedido. Tente novamente em 60 segundos."
        );
        response.getWriter().write(json.writeValueAsString(body));
    }
}
