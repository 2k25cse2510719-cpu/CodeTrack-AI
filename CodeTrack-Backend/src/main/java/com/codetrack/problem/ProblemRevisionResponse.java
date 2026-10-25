
package com.codetrack.problem;

import java.time.LocalDate;
import java.time.LocalDateTime;

public record ProblemRevisionResponse(
        Long id,
        Long problemId,
        String problemTitle,
        LocalDate scheduledDate,
        LocalDateTime completedAt,
        RevisionStatus status,
        String notes,
        LocalDateTime createdAt
) {
    public static ProblemRevisionResponse from(ProblemRevision revision) {
        return new ProblemRevisionResponse(
                revision.getId(),
                revision.getProblem().getId(),
                revision.getProblem().getTitle(),
                revision.getScheduledDate(),
                revision.getCompletedAt(),
                revision.getStatus(),
                revision.getNotes(),
                revision.getCreatedAt()
        );
    }
}
