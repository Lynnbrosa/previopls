package com.previopls.controller;

import com.previopls.dto.lead.LeadDetailResponse;
import com.previopls.dto.lead.LeadListResponse;
import com.previopls.dto.lead.LeadPatchRequest;
import com.previopls.entity.enums.PrioridadeLead;
import com.previopls.entity.enums.StatusLead;
import com.previopls.service.LeadService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/v1/leads")
@Tag(name = "leads", description = "Leads priorizados consumidos pelo app mobile")
@Validated
public class LeadController {

    private final LeadService leadService;

    public LeadController(LeadService leadService) {
        this.leadService = leadService;
    }

    @GetMapping
    @PreAuthorize("hasAnyRole('CONSULTOR','ADMIN')")
    @Operation(summary = "Lista leads filtrados por prioridade/status (paginado)")
    public ResponseEntity<LeadListResponse> listar(
            @RequestParam(required = false) PrioridadeLead prioridade,
            @RequestParam(required = false) StatusLead status,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(name = "per_page", defaultValue = "20") @Min(1) @Max(100) int perPage
    ) {
        return ResponseEntity.ok(leadService.listar(prioridade, status, page, perPage));
    }

    @GetMapping("/{leadId}")
    @PreAuthorize("hasAnyRole('CONSULTOR','ADMIN')")
    @Operation(summary = "Visão 360 — cliente + veículo + script comercial")
    public ResponseEntity<LeadDetailResponse> obter(@PathVariable UUID leadId) {
        return ResponseEntity.ok(leadService.obter(leadId));
    }

    @PatchMapping("/{leadId}")
    @PreAuthorize("hasAnyRole('CONSULTOR','ADMIN')")
    @Operation(summary = "Atualiza status do lead (agendado/recusado/sem-contato)")
    public ResponseEntity<LeadDetailResponse> atualizar(
            @PathVariable UUID leadId,
            @Valid @RequestBody LeadPatchRequest request
    ) {
        return ResponseEntity.ok(leadService.atualizarStatus(leadId, request));
    }
}
