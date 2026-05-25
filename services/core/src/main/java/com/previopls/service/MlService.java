package com.previopls.service;

import com.previopls.entity.enums.PerfilCliente;
import com.previopls.entity.enums.PrioridadeLead;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.EnumMap;
import java.util.Map;
import java.util.Set;

/**
 * Motor preditivo — stub determinístico para integração end-to-end.
 *
 * Na versão final, este serviço chamará o modelo serializado treinado
 * pela equipe de IA/ML (Base 2). Regra crítica de produto (US02):
 * apenas variáveis disponíveis no momento da compra (D0) entram no input.
 */
@Service
public class MlService {

    public static final Set<PerfilCliente> PERFIS_GERAM_LEAD =
            Set.of(PerfilCliente.ABANDONO, PerfilCliente.ESQUECIDO);

    private static final Map<PerfilCliente, String> SCRIPTS = new EnumMap<>(PerfilCliente.class);

    static {
        SCRIPTS.put(PerfilCliente.FIEL,
                "Cliente fiel — oferecer pacote de manutenção preventiva premium e enfatizar histórico de relacionamento com a marca.");
        SCRIPTS.put(PerfilCliente.ABANDONO,
                "Cliente de alto risco de evasão — oferta agressiva de primeira revisão com desconto + brinde institucional. Abordar antes da 1ª revisão.");
        SCRIPTS.put(PerfilCliente.ESQUECIDO,
                "Cliente esquecido — lembrete proativo de manutenção + agendamento facilitado. Oferecer combo revisão + lavagem.");
        SCRIPTS.put(PerfilCliente.ECONOMICO,
                "Cliente sensível a preço — apresentar oferta promocional com parcelamento e comparativo de custo total de propriedade.");
    }

    public ResultadoClassificacao classificar(FeaturesCompra features) {
        String seed = features.concessionariaId() + "|" + features.modelo() + "|"
                + features.versao() + "|" + features.regiao();
        byte[] digest = sha256(seed);

        int bucket = Byte.toUnsignedInt(digest[0]) % 100;
        double scoreBase = Byte.toUnsignedInt(digest[1]) / 255.0;

        PerfilCliente perfil;
        double score;
        if (bucket < 35) {
            perfil = PerfilCliente.FIEL;
            score = round(0.10 + scoreBase * 0.20);
        } else if (bucket < 60) {
            perfil = PerfilCliente.ECONOMICO;
            score = round(0.30 + scoreBase * 0.25);
        } else if (bucket < 85) {
            perfil = PerfilCliente.ESQUECIDO;
            score = round(0.55 + scoreBase * 0.20);
        } else {
            perfil = PerfilCliente.ABANDONO;
            score = round(0.78 + scoreBase * 0.22);
        }

        return new ResultadoClassificacao(perfil, score, Instant.now());
    }

    public PrioridadeLead derivarPrioridade(double score) {
        if (score >= 0.85) return PrioridadeLead.CRITICA;
        if (score >= 0.65) return PrioridadeLead.ALTA;
        if (score >= 0.40) return PrioridadeLead.MEDIA;
        return PrioridadeLead.BAIXA;
    }

    public String scriptParaPerfil(PerfilCliente perfil) {
        return SCRIPTS.get(perfil);
    }

    private static byte[] sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            return md.digest(input.getBytes(StandardCharsets.UTF_8));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 indisponível", e);
        }
    }

    private static double round(double value) {
        return Math.round(value * 1000.0) / 1000.0;
    }

    public record FeaturesCompra(
            String regiao,
            String modelo,
            String versao,
            Integer ano,
            BigDecimal valorCompra,
            String concessionariaId
    ) {
    }

    public record ResultadoClassificacao(
            PerfilCliente perfil,
            Double scoreRisco,
            Instant classificadoEm
    ) {
    }
}
