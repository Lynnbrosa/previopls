package com.previopls.security;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.MDC;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

public final class RequestContext {

    public static final String MDC_REQUEST_ID = "requestId";
    public static final String HEADER_REQUEST_ID = "X-Request-Id";

    private RequestContext() {}

    public static String currentRequestId() {
        String fromMdc = MDC.get(MDC_REQUEST_ID);
        if (fromMdc != null) return fromMdc;
        HttpServletRequest req = currentRequest();
        return req == null ? null : req.getHeader(HEADER_REQUEST_ID);
    }

    public static String remoteIp() {
        return remoteIp(currentRequest());
    }

    /**
     * IP do cliente a partir da requisição informada. Use esta variante em filtros que rodam
     * antes do {@code RequestContextFilter} do Spring (o holder ainda está vazio lá).
     */
    public static String remoteIp(HttpServletRequest req) {
        if (req == null) return null;
        String forwarded = req.getHeader("X-Forwarded-For");
        if (forwarded != null && !forwarded.isBlank()) {
            String first = forwarded.split(",")[0].trim();
            if (!first.isEmpty()) return first.length() > 64 ? first.substring(0, 64) : first;
        }
        return req.getRemoteAddr();
    }

    public static String userAgent() {
        HttpServletRequest req = currentRequest();
        return req == null ? null : req.getHeader("User-Agent");
    }

    private static HttpServletRequest currentRequest() {
        ServletRequestAttributes attrs = (ServletRequestAttributes)
                RequestContextHolder.getRequestAttributes();
        return attrs == null ? null : attrs.getRequest();
    }
}
