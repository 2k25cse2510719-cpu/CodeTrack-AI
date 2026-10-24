package com.codetrack.problem;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

public record ProblemRequest(
        @NotBlank(message = "Title is required")
        @Size(max = 200, message = "Title must be 200 characters or fewer")
        String title,

        @Size(max = 100)
        String platform,

        @Size(max = 30)
        String difficulty,

        @Size(max = 100)
        String topic,

        @Size(max = 100)
        String selectedPattern,

        @Size(max = 2048)
        String url,

        ProblemStatus status,
        LocalDate solvedDate,
        String notes
) {}
