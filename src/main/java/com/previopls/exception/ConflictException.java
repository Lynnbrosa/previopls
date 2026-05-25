package com.previopls.exception;

import org.springframework.http.HttpStatus;

import java.util.Map;

public class ConflictException extends AppException {
    public ConflictException(String message) {
        super(HttpStatus.CONFLICT, "CONFLICT", message);
    }

    public ConflictException(String message, Map<String, Object> details) {
        super(HttpStatus.CONFLICT, "CONFLICT", message, details);
    }
}
