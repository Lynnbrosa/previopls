package com.previopls.mapper;

import com.previopls.dto.lead.LeadDetailResponse;
import com.previopls.dto.lead.LeadListItemResponse;
import com.previopls.entity.Lead;

public final class LeadMapper {

    private LeadMapper() {
    }

    public static LeadListItemResponse toListItem(Lead l) {
        return new LeadListItemResponse(
                l.getId(),
                l.getCliente().getId(),
                l.getVeiculo().getId(),
                l.getCliente().getNome(),
                l.getVeiculo().getModelo() + " " + l.getVeiculo().getVersao(),
                l.getScoreRisco(),
                l.getPrioridade(),
                l.getStatus(),
                l.getCriadoEm()
        );
    }

    public static LeadDetailResponse toDetail(Lead l) {
        return new LeadDetailResponse(
                l.getId(),
                l.getScoreRisco(),
                l.getPrioridade(),
                l.getStatus(),
                l.getScriptOferta(),
                l.getObservacao(),
                l.getCriadoEm(),
                l.getAtualizadoEm(),
                ClienteMapper.toResponseSemVeiculos(l.getCliente()),
                ClienteMapper.toResponse(l.getVeiculo())
        );
    }
}
