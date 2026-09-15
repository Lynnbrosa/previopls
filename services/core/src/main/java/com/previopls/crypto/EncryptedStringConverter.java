package com.previopls.crypto;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;

/**
 * AttributeConverter JPA que aplica AES-GCM transparentemente em campos String.
 *
 * Uso: anote a coluna com {@code @Convert(converter = EncryptedStringConverter.class)}.
 * Hibernate chama esta classe na escrita/leitura — o restante do código vê apenas plain text.
 *
 * Leitura tolerante: se o ciphertext não decifra (APP_CRYPTO_KEY diferente da usada para gravar,
 * por exemplo o seed V3 cifrado com a chave de dev e o backend subindo com outra), o campo vira
 * {@code null} e um WARN é emitido, em vez de derrubar toda a listagem de leads com 500.
 * A escrita continua estrita: falha de cifragem é erro.
 */
@Converter
public class EncryptedStringConverter implements AttributeConverter<String, String> {

    private static final Logger log = LoggerFactory.getLogger(EncryptedStringConverter.class);

    private static CryptoService cryptoService;

    @Autowired
    public void setCryptoService(@Lazy CryptoService cryptoService) {
        EncryptedStringConverter.cryptoService = cryptoService;
    }

    @Override
    public String convertToDatabaseColumn(String attribute) {
        if (attribute == null) return null;
        return cryptoService.encrypt(attribute);
    }

    @Override
    public String convertToEntityAttribute(String dbData) {
        if (dbData == null || dbData.isEmpty()) return null;
        try {
            return cryptoService.decrypt(dbData);
        } catch (IllegalStateException e) {
            log.warn("PII ilegível em repouso (APP_CRYPTO_KEY diferente da usada na gravação ou dado corrompido); "
                    + "campo devolvido como null. Regere o seed com a chave atual ou restaure a chave original.");
            return null;
        }
    }
}
