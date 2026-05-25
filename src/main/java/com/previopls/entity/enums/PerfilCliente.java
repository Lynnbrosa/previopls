package com.previopls.entity.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum PerfilCliente {
    FIEL("fiel"),
    ABANDONO("abandono"),
    ESQUECIDO("esquecido"),
    ECONOMICO("economico");

    private final String value;

    PerfilCliente(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static PerfilCliente fromValue(String value) {
        for (PerfilCliente p : values()) {
            if (p.value.equalsIgnoreCase(value) || p.name().equalsIgnoreCase(value)) {
                return p;
            }
        }
        throw new IllegalArgumentException("Perfil inválido: " + value);
    }
}
