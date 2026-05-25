package com.previopls.entity;

import com.previopls.entity.enums.PrioridadeLead;
import com.previopls.entity.enums.StatusLead;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "leads", indexes = {
        @Index(name = "ix_leads_cliente_id", columnList = "cliente_id"),
        @Index(name = "ix_leads_veiculo_id", columnList = "veiculo_id"),
        @Index(name = "ix_leads_prioridade", columnList = "prioridade"),
        @Index(name = "ix_leads_status", columnList = "status"),
        @Index(name = "ix_leads_prioridade_status", columnList = "prioridade, status")
})
@Getter
@Setter
@NoArgsConstructor
public class Lead {

    @Id
    @GeneratedValue
    @Column(columnDefinition = "uuid")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "cliente_id", nullable = false)
    private Cliente cliente;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "veiculo_id", nullable = false)
    private Veiculo veiculo;

    @Column(name = "score_risco", nullable = false)
    private Double scoreRisco;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private PrioridadeLead prioridade;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private StatusLead status = StatusLead.ABERTO;

    @Column(name = "script_oferta", columnDefinition = "text")
    private String scriptOferta;

    @Column(columnDefinition = "text")
    private String observacao;

    @Column(name = "criado_em", nullable = false, updatable = false)
    private Instant criadoEm = Instant.now();

    @Column(name = "atualizado_em", nullable = false)
    private Instant atualizadoEm = Instant.now();

    @PreUpdate
    void preUpdate() {
        this.atualizadoEm = Instant.now();
    }
}
