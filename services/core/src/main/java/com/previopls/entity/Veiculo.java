package com.previopls.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "veiculos", indexes = {
        @Index(name = "ix_veiculos_cliente_id", columnList = "cliente_id"),
        @Index(name = "ix_veiculos_vin", columnList = "vin", unique = true),
        @Index(name = "ix_veiculos_concessionaria_id", columnList = "concessionaria_id")
})
@Getter
@Setter
@NoArgsConstructor
public class Veiculo {

    @Id
    @GeneratedValue
    @Column(columnDefinition = "uuid")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "cliente_id", nullable = false)
    private Cliente cliente;

    @Column(nullable = false, length = 80)
    private String modelo;

    @Column(nullable = false, length = 80)
    private String versao;

    @Column(nullable = false)
    private Integer ano;

    @Column(nullable = false, unique = true, length = 17)
    private String vin;

    @Column(name = "data_compra", nullable = false)
    private LocalDate dataCompra;

    @Column(name = "valor_compra", nullable = false, precision = 12, scale = 2)
    private BigDecimal valorCompra;

    @Column(name = "concessionaria_id", nullable = false, length = 40)
    private String concessionariaId;

    @Column(name = "criado_em", nullable = false, updatable = false)
    private Instant criadoEm = Instant.now();
}
