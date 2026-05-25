package com.previopls.service;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.previopls.entity.enums.PerfilCliente;
import com.previopls.entity.enums.PrioridadeLead;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.Instant;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/**
 * Motor preditivo: chama o serviço ml-api via REST interno.
 *
 * Contrato: POST {ML_API_URL}/predict
 *   body  -> {regiao, modelo, ano, valor_compra, concessionaria_id}
 *   resp  -> {perfil, score, latency_ms}
 *
 * Regra crítica de produto (US02): só features D0 entram no input.
 *
 * Fallback: indisponibilidade do ml-api não derruba o cadastro do cliente.
 * O serviço devolve perfil ESQUECIDO com score 0.5 e loga warning, deixando
 * a trilha de auditoria evidenciar a degradação para o time de operações.
 */
@Service
public class MlService {

    private static final Logger log = LoggerFactory.getLogger(MlService.class);

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

    private static final Duration CLIENT_TIMEOUT = Duration.ofSeconds(2);

    private final RestClient restClient;

    public MlService(@Value("${ML_API_URL:http://ml-api:8000}") String mlApiUrl) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout((int) CLIENT_TIMEOUT.toMillis());
        factory.setReadTimeout((int) CLIENT_TIMEOUT.toMillis());

        this.restClient = RestClient.builder()
                .baseUrl(mlApiUrl)
                .requestFactory(factory)
                .build();
    }

    public ResultadoClassificacao classificar(FeaturesCompra features) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("regiao", features.regiao());
        body.put("modelo", features.modelo());
        body.put("ano", features.ano());
        body.put("valor_compra", features.valorCompra() != null
                ? features.valorCompra().toPlainString() : "0");
        body.put("concessionaria_id", features.concessionariaId());

        try {
            PredictResponse response = restClient.post()
                    .uri("/predict")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(body)
                    .retrieve()
                    .body(PredictResponse.class);

            if (response == null || response.perfil() == null || response.score() == null) {
                log.warn("ml-api retornou resposta incompleta, aplicando fallback");
                return fallback();
            }

            PerfilCliente perfil = PerfilCliente.valueOf(response.perfil());
            return new ResultadoClassificacao(perfil, response.score(), Instant.now());

        } catch (IllegalArgumentException unknownPerfil) {
            log.warn("ml-api retornou perfil desconhecido, aplicando fallback", unknownPerfil);
            return fallback();
        } catch (Exception remoteError) {
            log.warn("falha ao chamar ml-api ({}), aplicando fallback", remoteError.getMessage());
            return fallback();
        }
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

    private ResultadoClassificacao fallback() {
        return new ResultadoClassificacao(PerfilCliente.ESQUECIDO, 0.5, Instant.now());
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

    @JsonIgnoreProperties(ignoreUnknown = true)
    private record PredictResponse(
            String perfil,
            Double score,
            @JsonProperty("latency_ms") Integer latencyMs
    ) {
    }
}
