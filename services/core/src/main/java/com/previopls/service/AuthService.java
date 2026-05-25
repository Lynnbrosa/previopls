package com.previopls.service;

import com.previopls.dto.auth.LoginRequest;
import com.previopls.dto.auth.LoginResponse;
import com.previopls.entity.Usuario;
import com.previopls.exception.UnauthorizedException;
import com.previopls.repository.UsuarioRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final UsuarioRepository usuarioRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final LockoutService lockoutService;
    private final AuditService auditService;

    public AuthService(UsuarioRepository usuarioRepository,
                       PasswordEncoder passwordEncoder,
                       JwtService jwtService,
                       LockoutService lockoutService,
                       AuditService auditService) {
        this.usuarioRepository = usuarioRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.lockoutService = lockoutService;
        this.auditService = auditService;
    }

    public LoginResponse login(LoginRequest request) {
        String email = request.email();

        if (lockoutService.isLocked(email)) {
            auditService.logLoginLocked(email);
            throw new UnauthorizedException("Conta temporariamente bloqueada por excesso de tentativas. Tente novamente em alguns minutos.");
        }

        Usuario usuario = usuarioRepository.findByEmail(email).orElse(null);
        if (usuario == null || !passwordEncoder.matches(request.senha(), usuario.getSenhaHash())) {
            lockoutService.recordAttempt(email, false);
            auditService.logLoginFailed(email, usuario == null ? "usuario_inexistente" : "senha_invalida");
            throw new UnauthorizedException("Credenciais inválidas");
        }

        lockoutService.recordAttempt(email, true);
        String token = jwtService.generate(usuario.getId(), usuario.getPapel().getValue(), usuario.getNome());
        auditService.logLoginSuccess(usuario.getId(), usuario.getEmail(), usuario.getPapel().getValue());

        return new LoginResponse(
                token,
                "Bearer",
                jwtService.expirationSeconds(),
                usuario.getPapel().getValue()
        );
    }
}
