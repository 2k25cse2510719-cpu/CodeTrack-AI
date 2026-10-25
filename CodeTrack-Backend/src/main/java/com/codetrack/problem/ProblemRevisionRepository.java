package com.codetrack.problem;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface ProblemRevisionRepository
        extends JpaRepository<ProblemRevision, Long> {

    List<ProblemRevision>
    findAllByProblemUserIdAndStatusAndScheduledDateLessThanEqualOrderByScheduledDateAsc(
            Long userId, RevisionStatus status, LocalDate date);

    List<ProblemRevision>
    findAllByProblemUserIdAndStatusAndScheduledDateGreaterThanOrderByScheduledDateAsc(
            Long userId, RevisionStatus status, LocalDate date);

    @Query("""
            SELECT r FROM ProblemRevision r
            JOIN FETCH r.problem p
            WHERE p.user.id = :userId
              AND r.status = :status
              AND r.scheduledDate > :date
            ORDER BY r.scheduledDate ASC
            """)
    List<ProblemRevision> findUpcomingWithProblem(
            @Param("userId") Long userId,
            @Param("status") RevisionStatus status,
            @Param("date") LocalDate date);

    Optional<ProblemRevision> findByIdAndProblemUserId(
            Long revisionId, Long userId);

    boolean existsByProblemIdAndProblemUserIdAndStatus(
            Long problemId, Long userId, RevisionStatus status);

    List<ProblemRevision>
    findAllByProblemUserIdAndStatusOrderByCompletedAtDesc(
            Long userId, RevisionStatus status);

    List<ProblemRevision>
    findAllByProblemIdAndProblemUserIdAndStatus(
            Long problemId, Long userId, RevisionStatus status);
}
