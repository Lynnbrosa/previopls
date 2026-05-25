package com.previopls.entity.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum RolePapel {
    ADMIN("admin"),
    CONSULTOR("consultor");

    private final String value;

    RolePapel(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static RolePapel fromValue(String value) {
        for (RolePapel r : values()) {
            if (r.value.equalsIgnoreCase(value) || r.name().equalsIgnoreCase(value)) {
                return r;
            }
        }
        throw new IllegalArgumentException("Papel inválido: " + value);
    }
}
