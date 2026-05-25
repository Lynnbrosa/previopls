package com.previopls.security;

import ch.qos.logback.classic.pattern.ClassicConverter;
import ch.qos.logback.classic.spi.ILoggingEvent;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Logback converter que mascara PII em qualquer mensagem antes da escrita no log.
 *
 * Patterns cobertos:
 *  - CPF (11 dígitos contíguos)
 *  - Email
 *  - Header Authorization: Bearer ...
 *  - Cartão de crédito (13-19 dígitos contíguos)
 *
 * É a última linha de defesa — devs devem evitar logar PII de propósito,
 * mas este filtro impede vazamentos acidentais via Logger.info("user={}", obj).
 */
public class PiiMaskingConverter extends ClassicConverter {

    private static final Pattern CPF = Pattern.compile("\\b\\d{11}\\b");
    private static final Pattern EMAIL = Pattern.compile(
            "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b");
    private static final Pattern BEARER = Pattern.compile(
            "(?i)(Bearer\\s+)[A-Za-z0-9._\\-+/=]+");
    private static final Pattern LONG_DIGITS = Pattern.compile("\\b\\d{13,19}\\b");

    @Override
    public String convert(ILoggingEvent event) {
        String msg = event.getFormattedMessage();
        if (msg == null || msg.isEmpty()) return msg;

        msg = mask(CPF, msg, m -> m.group().substring(0, 3) + ".***.***-" + m.group().substring(9));
        msg = mask(EMAIL, msg, m -> {
            String e = m.group();
            int at = e.indexOf('@');
            return e.charAt(0) + "***" + e.substring(at);
        });
        msg = BEARER.matcher(msg).replaceAll("$1***REDACTED***");
        msg = mask(LONG_DIGITS, msg, m -> "****" + m.group().substring(m.group().length() - 4));

        return msg;
    }

    private static String mask(Pattern pattern, String input, java.util.function.Function<Matcher, String> replacer) {
        Matcher m = pattern.matcher(input);
        StringBuilder out = new StringBuilder();
        while (m.find()) {
            m.appendReplacement(out, Matcher.quoteReplacement(replacer.apply(m)));
        }
        m.appendTail(out);
        return out.toString();
    }
}
