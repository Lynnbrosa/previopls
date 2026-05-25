package com.previopls.dto.lead;

import com.previopls.entity.enums.StatusLead;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record LeadPatchRequest(
        @NotNull StatusLead status,
        @Size(max = 2000) String observacao
) {
}
