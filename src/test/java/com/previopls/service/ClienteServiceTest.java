package com.previopls.service;

import com.previopls.dto.cliente.ClienteCreateRequest;
import com.previopls.dto.cliente.ClienteCreatedResponse;
import com.previopls.dto.cliente.VeiculoRequest;
import com.previopls.entity.Cliente;
import com.previopls.entity.Lead;
import com.previopls.entity.Veiculo;
import com.previopls.entity.enums.PerfilCliente;
import com.previopls.entity.enums.PrioridadeLead;
import com.previopls.exception.ConflictException;
import com.previopls.repository.ClienteRepository;
import com.previopls.repository.LeadRepository;
import com.previopls.repository.VeiculoRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ClienteServiceTest {

    @Mock
    ClienteRepository clienteRepository;
    @Mock
    VeiculoRepository veiculoRepository;
    @Mock
    LeadRepository leadRepository;
    @Mock
    MlService mlService;

    @InjectMocks
    ClienteService service;

    ClienteCreateRequest payload;

    @BeforeEach
    void setUp() {
        payload = new ClienteCreateRequest(
                "Maria Silva",
                "12345678900",
                "maria@example.com",
                "+5511999998888",
                "SP",
                new VeiculoRequest(
                        "Ranger", "XLT", 2026,
                        "9BFZZZ8F7NB000001",
                        LocalDate.of(2026, 5, 13),
                        new BigDecimal("250000.00"),
                        "FORD-SP-001"
                )
        );
    }

    @Test
    void geraLeadCriticoQuandoPerfilEhAbandonoComScoreAlto() {
        when(clienteRepository.existsByCpf("12345678900")).thenReturn(false);
        when(veiculoRepository.existsByVin("9BFZZZ8F7NB000001")).thenReturn(false);
        when(clienteRepository.save(any(Cliente.class))).thenAnswer(inv -> {
            Cliente c = inv.getArgument(0);
            c.setId(UUID.randomUUID());
            return c;
        });
        when(veiculoRepository.save(any(Veiculo.class))).thenAnswer(inv -> {
            Veiculo v = inv.getArgument(0);
            v.setId(UUID.randomUUID());
            return v;
        });
        when(mlService.classificar(any())).thenReturn(
                new MlService.ResultadoClassificacao(PerfilCliente.ABANDONO, 0.92, Instant.now())
        );
        when(mlService.derivarPrioridade(0.92)).thenReturn(PrioridadeLead.CRITICA);
        when(mlService.scriptParaPerfil(PerfilCliente.ABANDONO)).thenReturn("oferta agressiva");
        when(leadRepository.save(any(Lead.class))).thenAnswer(inv -> {
            Lead l = inv.getArgument(0);
            l.setId(UUID.randomUUID());
            return l;
        });

        ClienteCreatedResponse result = service.cadastrarCompra(payload);

        assertThat(result.perfil()).isEqualTo(PerfilCliente.ABANDONO);
        assertThat(result.scoreRisco()).isEqualTo(0.92);
        assertThat(result.leadId()).isNotNull();

        ArgumentCaptor<Lead> leadCaptor = ArgumentCaptor.forClass(Lead.class);
        verify(leadRepository).save(leadCaptor.capture());
        assertThat(leadCaptor.getValue().getPrioridade()).isEqualTo(PrioridadeLead.CRITICA);
        assertThat(leadCaptor.getValue().getScriptOferta()).isEqualTo("oferta agressiva");
    }

    @Test
    void naoGeraLeadParaPerfilFiel() {
        when(clienteRepository.existsByCpf(anyString())).thenReturn(false);
        when(veiculoRepository.existsByVin(anyString())).thenReturn(false);
        when(clienteRepository.save(any(Cliente.class))).thenAnswer(inv -> {
            Cliente c = inv.getArgument(0);
            c.setId(UUID.randomUUID());
            return c;
        });
        when(veiculoRepository.save(any(Veiculo.class))).thenAnswer(inv -> {
            Veiculo v = inv.getArgument(0);
            v.setId(UUID.randomUUID());
            return v;
        });
        when(mlService.classificar(any())).thenReturn(
                new MlService.ResultadoClassificacao(PerfilCliente.FIEL, 0.15, Instant.now())
        );

        ClienteCreatedResponse result = service.cadastrarCompra(payload);

        assertThat(result.perfil()).isEqualTo(PerfilCliente.FIEL);
        assertThat(result.leadId()).isNull();
        verify(leadRepository, never()).save(any(Lead.class));
    }

    @Test
    void rejeitaCpfDuplicado() {
        when(clienteRepository.existsByCpf("12345678900")).thenReturn(true);

        assertThatThrownBy(() -> service.cadastrarCompra(payload))
                .isInstanceOf(ConflictException.class)
                .hasMessageContaining("Cliente já cadastrado");

        verify(clienteRepository, never()).save(any(Cliente.class));
        verify(leadRepository, never()).save(any(Lead.class));
    }

    @Test
    void rejeitaVinDuplicado() {
        when(clienteRepository.existsByCpf(anyString())).thenReturn(false);
        when(veiculoRepository.existsByVin("9BFZZZ8F7NB000001")).thenReturn(true);

        assertThatThrownBy(() -> service.cadastrarCompra(payload))
                .isInstanceOf(ConflictException.class)
                .hasMessageContaining("Veículo já cadastrado");

        verify(veiculoRepository, never()).save(any(Veiculo.class));
        verify(leadRepository, never()).save(any(Lead.class));
    }
}
