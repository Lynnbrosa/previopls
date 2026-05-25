package com.previopls.mapper;

import com.previopls.crypto.Pii;
import com.previopls.dto.cliente.ClienteResponse;
import com.previopls.dto.cliente.VeiculoResponse;
import com.previopls.entity.Cliente;
import com.previopls.entity.Veiculo;

import java.util.List;

public final class ClienteMapper {

    private ClienteMapper() {
    }

    public static VeiculoResponse toResponse(Veiculo v) {
        return new VeiculoResponse(
                v.getId(),
                v.getModelo(),
                v.getVersao(),
                v.getAno(),
                v.getVin(),
                v.getDataCompra(),
                v.getValorCompra(),
                v.getConcessionariaId()
        );
    }

    public static ClienteResponse toResponse(Cliente c) {
        List<VeiculoResponse> veiculos = c.getVeiculos() == null
                ? List.of()
                : c.getVeiculos().stream().map(ClienteMapper::toResponse).toList();
        return new ClienteResponse(
                c.getId(),
                c.getNome(),
                Pii.maskCpf(c.getCpf()),
                Pii.maskEmail(c.getEmail()),
                Pii.maskTelefone(c.getTelefone()),
                c.getRegiao(),
                c.getPerfil(),
                c.getScoreRisco(),
                c.getCriadoEm(),
                c.getClassificadoEm(),
                veiculos
        );
    }

    public static ClienteResponse toResponseSemVeiculos(Cliente c) {
        return new ClienteResponse(
                c.getId(),
                c.getNome(),
                Pii.maskCpf(c.getCpf()),
                Pii.maskEmail(c.getEmail()),
                Pii.maskTelefone(c.getTelefone()),
                c.getRegiao(),
                c.getPerfil(),
                c.getScoreRisco(),
                c.getCriadoEm(),
                c.getClassificadoEm(),
                List.of()
        );
    }

    public static ClienteResponse toResponseComVeiculo(Cliente c, Veiculo v) {
        return new ClienteResponse(
                c.getId(),
                c.getNome(),
                Pii.maskCpf(c.getCpf()),
                Pii.maskEmail(c.getEmail()),
                Pii.maskTelefone(c.getTelefone()),
                c.getRegiao(),
                c.getPerfil(),
                c.getScoreRisco(),
                c.getCriadoEm(),
                c.getClassificadoEm(),
                List.of(toResponse(v))
        );
    }
}
