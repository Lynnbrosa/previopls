package com.previopls.dto.lead;

import java.util.List;

public record LeadListResponse(
        List<LeadListItemResponse> items,
        int page,
        int perPage,
        long total
) {
}
