package com.previopls.entity;

import com.previopls.crypto.EncryptedStringConverter;
import com.previopls.entity.enums.PerfilCliente;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "clientes", indexes = {
        @Index(name = "ix_clientes_cpf", columnList = "cpf", unique = true),
        @Index(name = "ix_clientes_perfil", columnList = "perfil")
})
@Getter
@Setter
@NoArgsConstructor
public class Cliente {

    @Id
    @GeneratedValue
    @Column(columnDefinition = "uuid")
    private UUID id;

    @Column(nullable = false, length = 180)
    private String nome;

    @Column(nullable = false, unique = true, length = 14)
    private String cpf;

    @Convert(converter = EncryptedStringConverter.class)
    @Column(columnDefinition = "text")
    private String email;

    @Convert(converter = EncryptedStringConverter.class)
    @Column(columnDefinition = "text")
    private String telefone;

    @Column(nullable = false, length = 40)
    private String regiao;

    @Enumerated(EnumType.STRING)
    @Column(length = 20)
    private PerfilCliente perfil;

    @Column(name = "score_risco")
    private Double scoreRisco;

    @Column(name = "criado_em", nullable = false, updatable = false)
    private Instant criadoEm = Instant.now();

    @Column(name = "classificado_em")
    private Instant classificadoEm;

    @Column(name = "retencao_ate")
    private Instant retencaoAte;

    @OneToMany(mappedBy = "cliente", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<Veiculo> veiculos = new ArrayList<>();

    @OneToMany(mappedBy = "cliente", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<Lead> leads = new ArrayList<>();
}
