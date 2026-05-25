package com.previopls.entity.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum StatusLead {
    ABERTO("aberto"),
    AGENDADO("agendado"),
    RECUSADO("recusado"),
    SEM_CONTATO("sem-contato");

    private final String value;

    StatusLead(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static StatusLead fromValue(String value) {
        for (StatusLead s : values()) {
            if (s.value.equalsIgnoreCase(value) || s.name().equalsIgnoreCase(value)) {
                return s;
            }
        }
        throw new IllegalArgumentException("Status inválido: " + value);
    }
}
