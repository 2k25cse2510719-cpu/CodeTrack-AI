
package com.codetrack.problem;

import java.time.LocalDate;
import java.time.LocalDateTime;

public record ProblemResponse(
        Long id,
        String title,
        String platform,
        String difficulty,
        String topic,
        String selectedPattern,
        String verifiedPattern,
        String url,
        ProblemStatus status,
        LocalDate solvedDate,
        String notes,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
    public static ProblemResponse from(Problem problem) {
        return new ProblemResponse(
                problem.getId(),
                problem.getTitle(),
                problem.getPlatform(),
                problem.getDifficulty(),
                problem.getTopic(),
                problem.getSelectedPattern(),
                problem.getVerifiedPattern(),
                problem.getUrl(),
                problem.getStatus(),
                problem.getSolvedDate(),
                problem.getNotes(),
                problem.getCreatedAt(),
                problem.getUpdatedAt()
        );
    }
}
