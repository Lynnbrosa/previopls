package com.previopls.entity.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum PrioridadeLead {
    CRITICA("critica", 0),
    ALTA("alta", 1),
    MEDIA("media", 2),
    BAIXA("baixa", 3);

    private final String value;
    private final int ordem;

    PrioridadeLead(String value, int ordem) {
        this.value = value;
        this.ordem = ordem;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public int getOrdem() {
        return ordem;
    }

    @JsonCreator
    public static PrioridadeLead fromValue(String value) {
        for (PrioridadeLead p : values()) {
            if (p.value.equalsIgnoreCase(value) || p.name().equalsIgnoreCase(value)) {
                return p;
            }
        }
        throw new IllegalArgumentException("Prioridade inválida: " + value);
    }
}
