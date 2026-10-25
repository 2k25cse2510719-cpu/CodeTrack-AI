
package com.codetrack.problem;

import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface ProblemRevisionRepository
        extends JpaRepository<ProblemRevision, Long> {

    List<ProblemRevision>
    findAllByProblemUserIdAndStatusAndScheduledDateLessThanEqualOrderByScheduledDateAsc(
            Long userId,
            RevisionStatus status,
            LocalDate date
    );

    Optional<ProblemRevision> findByIdAndProblemUserId(
            Long revisionId,
            Long userId
    );

    boolean existsByProblemIdAndProblemUserIdAndStatus(
            Long problemId,
            Long userId,
            RevisionStatus status
    );

    List<ProblemRevision>
    findAllByProblemUserIdAndStatusOrderByCompletedAtDesc(
            Long userId,
            RevisionStatus status
    );

    List<ProblemRevision>
    findAllByProblemIdAndProblemUserIdAndStatus(
            Long problemId,
            Long userId,
            RevisionStatus status
    );
}
