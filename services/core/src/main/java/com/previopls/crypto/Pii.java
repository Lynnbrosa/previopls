package com.previopls.crypto;

/**
 * Helpers de mascaramento de PII para respostas de API e logs.
 *
 * Os métodos retornam strings mascaradas sem nunca acessar a chave criptográfica —
 * são funções puras pra uso em DTOs ou serializadores.
 */
public final class Pii {

    private Pii() {}

    public static String maskCpf(String cpf) {
        if (cpf == null || cpf.length() != 11) return cpf;
        return cpf.substring(0, 3) + ".***.***-" + cpf.substring(9);
    }

    public static String maskEmail(String email) {
        if (email == null) return null;
        int at = email.indexOf('@');
        if (at < 2) return "***" + email.substring(Math.max(0, at));
        return email.charAt(0) + "***" + email.substring(at);
    }

    public static String maskTelefone(String telefone) {
        if (telefone == null || telefone.length() < 4) return telefone;
        return "****" + telefone.substring(telefone.length() - 4);
    }
}
