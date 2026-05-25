package com.previopls.service;

import com.previopls.entity.LoginAttempt;
import com.previopls.repository.LoginAttemptRepository;
import com.previopls.security.RequestContext;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;

/**
 * Anti-brute-force no login.
 *
 * Conta falhas dentro de uma janela ({@code app.security.lockout.window-minutes}).
 * Se atingir o limite, bloqueia o email pelo período de lockout.
 */
@Service
public class LockoutService {

    private final LoginAttemptRepository repository;
    private final int maxAttempts;
    private final Duration window;

    public LockoutService(
            LoginAttemptRepository repository,
            @Value("${app.security.lockout.max-attempts:5}") int maxAttempts,
            @Value("${app.security.lockout.window-minutes:15}") int windowMinutes) {
        this.repository = repository;
        this.maxAttempts = maxAttempts;
        this.window = Duration.ofMinutes(windowMinutes);
    }

    @Transactional(readOnly = true)
    public boolean isLocked(String email) {
        Instant since = Instant.now().minus(window);
        return repository.countFailuresSince(email, since) >= maxAttempts;
    }

    @Transactional
    public void recordAttempt(String email, boolean success) {
        LoginAttempt attempt = new LoginAttempt();
        attempt.setEmail(email);
        attempt.setSuccess(success);
        attempt.setRemoteIp(RequestContext.remoteIp());
        repository.save(attempt);
    }
}
