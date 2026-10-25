
package com.codetrack.problem;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

public record ProblemRevisionRequest(
        @NotNull(message = "Scheduled date is required")
        LocalDate scheduledDate
) {}
