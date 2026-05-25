package com.previopls.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.util.Map;

public record ErrorResponse(Body error) {

    public static ErrorResponse of(String code, String message) {
        return new ErrorResponse(new Body(code, message, null));
    }

    public static ErrorResponse of(String code, String message, Map<String, Object> details) {
        return new ErrorResponse(new Body(code, message, details));
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record Body(String code, String message, Map<String, Object> details) {
    }
}
