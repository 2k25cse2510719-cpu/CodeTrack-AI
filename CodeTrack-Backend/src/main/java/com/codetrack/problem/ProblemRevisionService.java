
package com.codetrack.problem;

import com.codetrack.auth.User;
import com.codetrack.auth.UserRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class ProblemRevisionService {

    private static final int[] INTERVALS = {1, 3, 7, 14, 30};

    private final ProblemRepository problemRepository;
    private final ProblemRevisionRepository revisionRepository;
    private final UserRepository userRepository;

    public ProblemRevisionService(
            ProblemRepository problemRepository,
            ProblemRevisionRepository revisionRepository,
            UserRepository userRepository) {
        this.problemRepository = problemRepository;
        this.revisionRepository = revisionRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public ProblemRevisionResponse schedule(
            Long problemId,
            LocalDate scheduledDate,
            String email) {

        User user = getUser(email);
        Problem problem = getOwnedProblem(problemId, user.getId());

        if (problem.getStatus() != ProblemStatus.SOLVED) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Only solved problems can be scheduled for revision");
        }

        if (scheduledDate == null ||
                scheduledDate.isBefore(LocalDate.now())) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Revision date must be today or in the future");
        }

        boolean activeRevisionExists =
                revisionRepository
                        .existsByProblemIdAndProblemUserIdAndStatus(
                                problemId,
                                user.getId(),
                                RevisionStatus.SCHEDULED);

        if (activeRevisionExists) {
            throw new ResponseStatusException(
                    HttpStatus.CONFLICT,
                    "This problem already has a scheduled revision");
        }

        ProblemRevision revision = new ProblemRevision();
        revision.setProblem(problem);
        revision.setScheduledDate(scheduledDate);
        revision.setStatus(RevisionStatus.SCHEDULED);

        return ProblemRevisionResponse.from(
                revisionRepository.save(revision));
    }

    @Transactional(readOnly = true)
    public List<ProblemRevisionResponse> getDue(String email) {
        User user = getUser(email);

        return revisionRepository
                .findAllByProblemUserIdAndStatusAndScheduledDateLessThanEqualOrderByScheduledDateAsc(
                        user.getId(),
                        RevisionStatus.SCHEDULED,
                        LocalDate.now())
                .stream()
                .map(ProblemRevisionResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<ProblemRevisionResponse> getHistory(String email) {
        User user = getUser(email);

        return revisionRepository
                .findAllByProblemUserIdAndStatusOrderByCompletedAtDesc(
                        user.getId(),
                        RevisionStatus.COMPLETED)
                .stream()
                .map(ProblemRevisionResponse::from)
                .toList();
    }

    @Transactional
    public ProblemRevisionResponse complete(
            Long revisionId,
            String email) {

        User user = getUser(email);

        ProblemRevision revision = revisionRepository
                .findByIdAndProblemUserId(revisionId, user.getId())
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Revision not found"));

        if (revision.getStatus() != RevisionStatus.SCHEDULED) {
            throw new ResponseStatusException(
                    HttpStatus.CONFLICT,
                    "Revision is not scheduled or has already been completed");
        }

        // Prevent completing a revision before its scheduled date.
        if (revision.getScheduledDate().isAfter(LocalDate.now())) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Revision is not due yet");
        }

        LocalDate today = LocalDate.now();

        revision.setStatus(RevisionStatus.COMPLETED);
        revision.setCompletedAt(LocalDateTime.now());

        ProblemRevision saved = revisionRepository.save(revision);

        long completedCount = revisionRepository
                .findAllByProblemIdAndProblemUserIdAndStatus(
                        revision.getProblem().getId(),
                        user.getId(),
                        RevisionStatus.COMPLETED)
                .size();

        int index = (int) Math.min(
                Math.max(completedCount - 1, 0),
                INTERVALS.length - 1);

        LocalDate nextDate = today.plusDays(INTERVALS[index]);

        ProblemRevision next = new ProblemRevision();
        next.setProblem(revision.getProblem());
        next.setScheduledDate(nextDate);
        next.setStatus(RevisionStatus.SCHEDULED);
        revisionRepository.save(next);

        return ProblemRevisionResponse.from(saved);
    }

    private User getUser(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.UNAUTHORIZED,
                        "User not found"));
    }

    private Problem getOwnedProblem(Long problemId, Long userId) {
        return problemRepository.findByIdAndUserId(problemId, userId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "Problem not found"));
    }
}
