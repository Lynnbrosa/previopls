package com.previopls.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "login_attempts", indexes = {
        @Index(name = "ix_login_attempts_email", columnList = "email"),
        @Index(name = "ix_login_attempts_attempted_at", columnList = "attempted_at"),
        @Index(name = "ix_login_attempts_email_attempted_at", columnList = "email, attempted_at")
})
@Getter
@Setter
@NoArgsConstructor
public class LoginAttempt {

    @Id
    @GeneratedValue
    @Column(columnDefinition = "uuid")
    private UUID id;

    @Column(nullable = false, length = 180)
    private String email;

    @Column(nullable = false)
    private boolean success;

    @Column(name = "remote_ip", length = 64)
    private String remoteIp;

    @Column(name = "attempted_at", nullable = false, updatable = false)
    private Instant attemptedAt = Instant.now();
}
