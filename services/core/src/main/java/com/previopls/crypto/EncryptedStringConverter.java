package com.previopls.crypto;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;

/**
 * AttributeConverter JPA que aplica AES-GCM transparentemente em campos String.
 *
 * Uso: anote a coluna com {@code @Convert(converter = EncryptedStringConverter.class)}.
 * Hibernate chama esta classe na escrita/leitura — o restante do código vê apenas plain text.
 */
@Converter
public class EncryptedStringConverter implements AttributeConverter<String, String> {

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
        return cryptoService.decrypt(dbData);
    }
}
