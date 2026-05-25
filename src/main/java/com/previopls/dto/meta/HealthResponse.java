package com.previopls.dto.meta;

import java.util.Map;

public record HealthResponse(String status, Map<String, String> components) {
}
