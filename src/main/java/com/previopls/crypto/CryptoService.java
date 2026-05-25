package com.previopls.crypto;

import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Base64;

/**
 * Criptografia simétrica autenticada (AES-256-GCM) para PII em repouso.
 *
 * Formato armazenado: Base64( IV(12B) || ciphertext || tag(16B) ).
 * IV aleatório por chamada — mesma plaintext gera ciphertexts diferentes.
 *
 * Em produção, a chave NÃO deve vir do application.yml em texto puro:
 * use variável de ambiente apontando para KMS/Vault/Parameter Store.
 */
@Service
public class CryptoService {

    private static final int IV_BYTES = 12;
    private static final int TAG_BITS = 128;
    private static final String ALGO = "AES/GCM/NoPadding";

    private final String configuredKey;
    private SecretKey key;
    private final SecureRandom random = new SecureRandom();

    public CryptoService(@Value("${app.crypto.key}") String configuredKey) {
        this.configuredKey = configuredKey;
    }

    @PostConstruct
    void init() {
        byte[] decoded = Base64.getDecoder().decode(configuredKey);
        if (decoded.length != 32) {
            throw new IllegalStateException(
                    "app.crypto.key deve ser Base64 de exatamente 32 bytes (AES-256)");
        }
        this.key = new SecretKeySpec(decoded, "AES");
    }

    public String encrypt(String plaintext) {
        if (plaintext == null) return null;
        try {
            byte[] iv = new byte[IV_BYTES];
            random.nextBytes(iv);
            Cipher cipher = Cipher.getInstance(ALGO);
            cipher.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(TAG_BITS, iv));
            byte[] ct = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));
            ByteBuffer buf = ByteBuffer.allocate(iv.length + ct.length);
            buf.put(iv);
            buf.put(ct);
            return Base64.getEncoder().encodeToString(buf.array());
        } catch (Exception e) {
            throw new IllegalStateException("Falha ao criptografar PII", e);
        }
    }

    public String decrypt(String ciphertext) {
        if (ciphertext == null || ciphertext.isEmpty()) return null;
        try {
            byte[] raw = Base64.getDecoder().decode(ciphertext);
            ByteBuffer buf = ByteBuffer.wrap(raw);
            byte[] iv = new byte[IV_BYTES];
            buf.get(iv);
            byte[] ct = new byte[buf.remaining()];
            buf.get(ct);
            Cipher cipher = Cipher.getInstance(ALGO);
            cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(TAG_BITS, iv));
            return new String(cipher.doFinal(ct), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new IllegalStateException("Falha ao descriptografar PII (chave incorreta ou dado corrompido)", e);
        }
    }
}
