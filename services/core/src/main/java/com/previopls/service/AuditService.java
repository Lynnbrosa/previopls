package com.previopls.service;

import com.previopls.entity.AuditLog;
import com.previopls.entity.enums.AuditAction;
import com.previopls.repository.AuditLogRepository;
import com.previopls.security.RequestContext;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

/**
 * Registra eventos relevantes para auditoria (LGPD / segurança).
 *
 * Cada chamada cria uma nova transação ({@link Propagation#REQUIRES_NEW}) — o
 * audit é persistido mesmo que a transação de negócio principal rollback.
 *
 * Quando o chamador não informa o ator, o serviço preenche {@code actorId} e
 * {@code actorRole} a partir do JWT autenticado na requisição (inclusive o JWT
 * interno emitido pelo Gateway), para que a trilha responda "quem fez".
 */
@Service
public class AuditService {

    private final AuditLogRepository repository;

    public AuditService(AuditLogRepository repository) {
        this.repository = repository;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void log(AuditAction action,
                    UUID actorId,
                    String actorEmail,
                    String actorRole,
                    String entityType,
                    String entityId,
                    String details) {
        if (actorId == null || actorRole == null) {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            if (auth != null && auth.isAuthenticated() && auth.getName() != null) {
                if (actorId == null) {
                    actorId = parseUuid(auth.getName());
                }
                if (actorRole == null) {
                    actorRole = auth.getAuthorities().stream()
                            .map(GrantedAuthority::getAuthority)
                            .filter(a -> a.startsWith("ROLE_"))
                            .map(a -> a.substring(5).toLowerCase())
                            .findFirst()
                            .orElse(null);
                }
            }
        }

        AuditLog log = new AuditLog();
        log.setAction(action);
        log.setActorId(actorId);
        log.setActorEmail(actorEmail);
        log.setActorRole(actorRole);
        log.setEntityType(entityType);
        log.setEntityId(entityId);
        log.setRequestId(RequestContext.currentRequestId());
        log.setRemoteIp(RequestContext.remoteIp());
        String ua = RequestContext.userAgent();
        if (ua != null && ua.length() > 255) ua = ua.substring(0, 255);
        log.setUserAgent(ua);
        log.setDetails(details);
        repository.save(log);
    }

    private static UUID parseUuid(String value) {
        try {
            return UUID.fromString(value);
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    public void logLoginSuccess(UUID userId, String email, String role) {
        log(AuditAction.LOGIN_SUCCESS, userId, email, role, "Usuario", userId.toString(), null);
    }

    public void logLoginFailed(String email, String reason) {
        log(AuditAction.LOGIN_FAILED, null, email, null, null, null, reason);
    }

    public void logLoginLocked(String email) {
        log(AuditAction.LOGIN_LOCKED, null, email, null, null, null, "lockout ativo");
    }
}
