package com.previopls.service;

import com.previopls.dto.cliente.ClienteCreateRequest;
import com.previopls.dto.cliente.ClienteCreatedResponse;
import com.previopls.dto.cliente.VeiculoRequest;
import com.previopls.entity.Cliente;
import com.previopls.entity.Lead;
import com.previopls.entity.Veiculo;
import com.previopls.entity.enums.AuditAction;
import com.previopls.entity.enums.StatusLead;
import com.previopls.exception.ConflictException;
import com.previopls.mapper.ClienteMapper;
import com.previopls.repository.ClienteRepository;
import com.previopls.repository.LeadRepository;
import com.previopls.repository.VeiculoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.UUID;

@Service
public class ClienteService {

    private final ClienteRepository clienteRepository;
    private final VeiculoRepository veiculoRepository;
    private final LeadRepository leadRepository;
    private final MlService mlService;
    private final AuditService auditService;

    public ClienteService(ClienteRepository clienteRepository,
                          VeiculoRepository veiculoRepository,
                          LeadRepository leadRepository,
                          MlService mlService,
                          AuditService auditService) {
        this.clienteRepository = clienteRepository;
        this.veiculoRepository = veiculoRepository;
        this.leadRepository = leadRepository;
        this.mlService = mlService;
        this.auditService = auditService;
    }

    @Transactional
    public ClienteCreatedResponse cadastrarCompra(ClienteCreateRequest req) {
        if (clienteRepository.existsByCpf(req.cpf())) {
            throw new ConflictException("Cliente já cadastrado", Map.of("cpf", req.cpf()));
        }

        VeiculoRequest veicReq = req.veiculo();
        if (veiculoRepository.existsByVin(veicReq.vin())) {
            throw new ConflictException("Veículo já cadastrado", Map.of("vin", veicReq.vin()));
        }

        Cliente cliente = new Cliente();
        cliente.setNome(req.nome());
        cliente.setCpf(req.cpf());
        cliente.setEmail(req.email());
        cliente.setTelefone(req.telefone());
        cliente.setRegiao(req.regiao());
        cliente = clienteRepository.save(cliente);

        Veiculo veiculo = new Veiculo();
        veiculo.setCliente(cliente);
        veiculo.setModelo(veicReq.modelo());
        veiculo.setVersao(veicReq.versao());
        veiculo.setAno(veicReq.ano());
        veiculo.setVin(veicReq.vin());
        veiculo.setDataCompra(veicReq.dataCompra());
        veiculo.setValorCompra(veicReq.valorCompra());
        veiculo.setConcessionariaId(veicReq.concessionariaId());
        veiculo = veiculoRepository.save(veiculo);

        MlService.FeaturesCompra features = new MlService.FeaturesCompra(
                cliente.getRegiao(),
                veiculo.getModelo(),
                veiculo.getVersao(),
                veiculo.getAno(),
                veiculo.getValorCompra(),
                veiculo.getConcessionariaId()
        );
        MlService.ResultadoClassificacao resultado = mlService.classificar(features);

        cliente.setPerfil(resultado.perfil());
        cliente.setScoreRisco(resultado.scoreRisco());
        cliente.setClassificadoEm(resultado.classificadoEm());

        auditService.log(AuditAction.CLIENTE_CREATED, null, null, null,
                "Cliente", cliente.getId().toString(),
                "perfil=" + resultado.perfil() + " score=" + resultado.scoreRisco());

        UUID leadId = null;
        if (MlService.PERFIS_GERAM_LEAD.contains(resultado.perfil())) {
            Lead lead = new Lead();
            lead.setCliente(cliente);
            lead.setVeiculo(veiculo);
            lead.setScoreRisco(resultado.scoreRisco());
            lead.setPrioridade(mlService.derivarPrioridade(resultado.scoreRisco()));
            lead.setStatus(StatusLead.ABERTO);
            lead.setScriptOferta(mlService.scriptParaPerfil(resultado.perfil()));
            lead = leadRepository.save(lead);
            leadId = lead.getId();

            auditService.log(AuditAction.LEAD_CREATED, null, null, null,
                    "Lead", leadId.toString(),
                    "prioridade=" + lead.getPrioridade());
        }

        return new ClienteCreatedResponse(
                ClienteMapper.toResponseComVeiculo(cliente, veiculo),
                leadId,
                resultado.perfil(),
                resultado.scoreRisco()
        );
    }
}
