package com.previopls.entity;

import com.previopls.entity.enums.AuditAction;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "audit_logs", indexes = {
        @Index(name = "ix_audit_logs_occurred_at", columnList = "occurred_at"),
        @Index(name = "ix_audit_logs_actor_id", columnList = "actor_id"),
        @Index(name = "ix_audit_logs_action", columnList = "action"),
        @Index(name = "ix_audit_logs_entity", columnList = "entity_type, entity_id")
})
@Getter
@Setter
@NoArgsConstructor
public class AuditLog {

    @Id
    @GeneratedValue
    @Column(columnDefinition = "uuid")
    private UUID id;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 40)
    private AuditAction action;

    @Column(name = "actor_id", columnDefinition = "uuid")
    private UUID actorId;

    @Column(name = "actor_email", length = 180)
    private String actorEmail;

    @Column(name = "actor_role", length = 20)
    private String actorRole;

    @Column(name = "entity_type", length = 40)
    private String entityType;

    @Column(name = "entity_id", length = 64)
    private String entityId;

    @Column(name = "request_id", length = 36)
    private String requestId;

    @Column(name = "remote_ip", length = 64)
    private String remoteIp;

    @Column(name = "user_agent", length = 255)
    private String userAgent;

    @Column(columnDefinition = "text")
    private String details;

    @Column(name = "occurred_at", nullable = false, updatable = false)
    private Instant occurredAt = Instant.now();
}
