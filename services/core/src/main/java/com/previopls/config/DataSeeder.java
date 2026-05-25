package com.previopls.config;

import com.previopls.entity.Usuario;
import com.previopls.entity.enums.RolePapel;
import com.previopls.repository.UsuarioRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@Profile("!test")
public class DataSeeder implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataSeeder.class);

    private final UsuarioRepository usuarioRepository;
    private final PasswordEncoder passwordEncoder;

    public DataSeeder(UsuarioRepository usuarioRepository, PasswordEncoder passwordEncoder) {
        this.usuarioRepository = usuarioRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) {
        if (usuarioRepository.findByEmail("admin@ford.com").isEmpty()) {
            Usuario admin = new Usuario();
            admin.setNome("Admin Ford");
            admin.setEmail("admin@ford.com");
            admin.setSenhaHash(passwordEncoder.encode("admin123"));
            admin.setPapel(RolePapel.ADMIN);
            usuarioRepository.save(admin);
            log.info("Seed: admin@ford.com criado (senha: admin123)");
        }
        if (usuarioRepository.findByEmail("consultor@ford.com").isEmpty()) {
            Usuario consultor = new Usuario();
            consultor.setNome("Carlos Consultor");
            consultor.setEmail("consultor@ford.com");
            consultor.setSenhaHash(passwordEncoder.encode("cons123"));
            consultor.setPapel(RolePapel.CONSULTOR);
            usuarioRepository.save(consultor);
            log.info("Seed: consultor@ford.com criado (senha: cons123)");
        }
    }
}
