package com.previopls.service;

import com.previopls.dto.lead.LeadDetailResponse;
import com.previopls.dto.lead.LeadListItemResponse;
import com.previopls.dto.lead.LeadListResponse;
import com.previopls.dto.lead.LeadPatchRequest;
import com.previopls.entity.Lead;
import com.previopls.entity.enums.AuditAction;
import com.previopls.entity.enums.PrioridadeLead;
import com.previopls.entity.enums.StatusLead;
import com.previopls.exception.NotFoundException;
import com.previopls.mapper.LeadMapper;
import com.previopls.repository.LeadRepository;
import org.owasp.encoder.Encode;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
public class LeadService {

    private final LeadRepository leadRepository;
    private final AuditService auditService;

    public LeadService(LeadRepository leadRepository, AuditService auditService) {
        this.leadRepository = leadRepository;
        this.auditService = auditService;
    }

    @Transactional(readOnly = true)
    public LeadListResponse listar(PrioridadeLead prioridade, StatusLead status, int page, int perPage) {
        Page<Lead> result = leadRepository.findFiltered(
                prioridade, status, PageRequest.of(page - 1, perPage));

        List<LeadListItemResponse> items = result.getContent().stream()
                .map(LeadMapper::toListItem)
                .toList();

        return new LeadListResponse(items, page, perPage, result.getTotalElements());
    }

    @Transactional(readOnly = true)
    public LeadDetailResponse obter(UUID leadId) {
        Lead lead = leadRepository.findByIdWithDetails(leadId)
                .orElseThrow(() -> new NotFoundException("Lead não encontrado"));
        return LeadMapper.toDetail(lead);
    }

    @Transactional
    public LeadDetailResponse atualizarStatus(UUID leadId, LeadPatchRequest patch) {
        Lead lead = leadRepository.findByIdWithDetails(leadId)
                .orElseThrow(() -> new NotFoundException("Lead não encontrado"));

        StatusLead anterior = lead.getStatus();
        lead.setStatus(patch.status());
        if (patch.observacao() != null) {
            // Sanitização anti-XSS: campo livre exibido em UI mobile/web.
            lead.setObservacao(sanitize(patch.observacao()));
        }
        lead.setAtualizadoEm(Instant.now());

        auditService.log(AuditAction.LEAD_PATCHED, null, null, null,
                "Lead", leadId.toString(),
                "status: " + anterior + " -> " + patch.status());

        return LeadMapper.toDetail(lead);
    }

    private static String sanitize(String input) {
        // Remove caracteres de controle e escapa HTML.
        String cleaned = input.replaceAll("[\\p{Cntrl}&&[^\r\n\t]]", "");
        return Encode.forHtmlContent(cleaned).trim();
    }
}
