package com.previopls.crypto;

import org.junit.jupiter.api.Test;

import java.util.Base64;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class EncryptedStringConverterTest {

    private static CryptoService service(String seed) {
        byte[] key = new byte[32];
        byte[] s = seed.getBytes();
        System.arraycopy(s, 0, key, 0, Math.min(s.length, 32));
        CryptoService c = new CryptoService(Base64.getEncoder().encodeToString(key));
        c.init();
        return c;
    }

    private static EncryptedStringConverter converterWith(CryptoService c) {
        EncryptedStringConverter conv = new EncryptedStringConverter();
        conv.setCryptoService(c);
        return conv;
    }

    @Test
    void roundTripComMesmaChave() {
        EncryptedStringConverter conv = converterWith(service("chave-a"));
        String ct = conv.convertToDatabaseColumn("maria@example.com");
        assertThat(ct).isNotEqualTo("maria@example.com");
        assertThat(conv.convertToEntityAttribute(ct)).isEqualTo("maria@example.com");
        assertThat(conv.convertToEntityAttribute(null)).isNull();
        assertThat(conv.convertToDatabaseColumn(null)).isNull();
    }

    @Test
    void leituraComChaveErradaDevolveNullEmVezDeQuebrarAConsulta() {
        String ct = converterWith(service("chave-a")).convertToDatabaseColumn("+5511999998888");
        EncryptedStringConverter outraChave = converterWith(service("chave-b"));
        assertThat(outraChave.convertToEntityAttribute(ct)).isNull();
    }

    @Test
    void decifrarLixoContinuaSendoErroNoServico() {
        assertThatThrownBy(() -> service("chave-a").decrypt("nao-e-base64-valido!!"))
                .isInstanceOf(IllegalStateException.class);
        assertThat(converterWith(service("chave-a")).convertToDatabaseColumn("ok")).isNotBlank();
    }
}
