
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

    private static final int[] REVISION_INTERVALS = {1, 3, 7, 14, 30};

    private final ProblemRevisionRepository revisionRepository;
    private final ProblemRepository problemRepository;
    private final UserRepository userRepository;

    public ProblemRevisionService(
            ProblemRevisionRepository revisionRepository,
            ProblemRepository problemRepository,
            UserRepository userRepository) {
        this.revisionRepository = revisionRepository;
        this.problemRepository = problemRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public ProblemRevisionResponse schedule(Long problemId, LocalDate scheduledDate, String email) {
        User user = getUser(email);
        Problem problem = getOwnedProblem(problemId, user);

        if (problem.getStatus() != ProblemStatus.SOLVED) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                    "Only solved problems can be scheduled for revision");
        }

        if (scheduledDate == null || scheduledDate.isBefore(LocalDate.now())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                    "Revision date cannot be in the past");
        }

        boolean alreadyScheduled = revisionRepository
                .existsByProblemIdAndProblemUserIdAndStatus(
                        problemId, user.getId(), RevisionStatus.SCHEDULED);

        if (alreadyScheduled) {
            throw new ResponseStatusException(HttpStatus.CONFLICT,
                    "This problem already has a scheduled revision");
        }

        ProblemRevision revision = new ProblemRevision();
        revision.setProblem(problem);
        revision.setScheduledDate(scheduledDate);
        revision.setStatus(RevisionStatus.SCHEDULED);

        return ProblemRevisionResponse.from(revisionRepository.save(revision));
    }

    @Transactional(readOnly = true)
    public List<ProblemRevisionResponse> getDue(String email) {
        User user = getUser(email);

        return revisionRepository
                .findAllByProblemUserIdAndStatusAndScheduledDateLessThanEqualOrderByScheduledDateAsc(
                        user.getId(), RevisionStatus.SCHEDULED, LocalDate.now())
                .stream()
                .map(ProblemRevisionResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<ProblemRevisionResponse> getUpcoming(String email) {
        User user = getUser(email);

        return revisionRepository
                .findUpcomingWithProblem(
                        user.getId(), RevisionStatus.SCHEDULED, LocalDate.now())
                .stream()
                .map(ProblemRevisionResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<ProblemRevisionResponse> getHistory(String email) {
        User user = getUser(email);

        return revisionRepository
                .findAllByProblemUserIdAndStatusOrderByCompletedAtDesc(
                        user.getId(), RevisionStatus.COMPLETED)
                .stream()
                .map(ProblemRevisionResponse::from)
                .toList();
    }

    @Transactional
    public ProblemRevisionResponse complete(Long revisionId, String email) {
        User user = getUser(email);

        ProblemRevision revision = revisionRepository
                .findByIdAndProblemUserId(revisionId, user.getId())
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "Revision not found"));

        if (revision.getStatus() != RevisionStatus.SCHEDULED) {
            throw new ResponseStatusException(HttpStatus.CONFLICT,
                    "Only scheduled revisions can be completed");
        }

        if (revision.getScheduledDate().isAfter(LocalDate.now())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                    "This revision is not due yet");
        }

        revision.setStatus(RevisionStatus.COMPLETED);
        revision.setCompletedAt(LocalDateTime.now());

        ProblemRevision completed = revisionRepository.save(revision);
        scheduleNextRevision(revision, user.getId());

        return ProblemRevisionResponse.from(completed);
    }

    private void scheduleNextRevision(ProblemRevision completed, Long userId) {
        List<ProblemRevision> history = revisionRepository
                .findAllByProblemIdAndProblemUserIdAndStatus(
                        completed.getProblem().getId(), userId, RevisionStatus.COMPLETED);

        int completedCount = history.size();
        int intervalIndex = Math.min(completedCount - 1, REVISION_INTERVALS.length - 1);
        int daysUntilNext = REVISION_INTERVALS[intervalIndex];

        ProblemRevision next = new ProblemRevision();
        next.setProblem(completed.getProblem());
        next.setScheduledDate(LocalDate.now().plusDays(daysUntilNext));
        next.setStatus(RevisionStatus.SCHEDULED);

        revisionRepository.save(next);
    }

    private User getUser(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "User not found"));
    }

    private Problem getOwnedProblem(Long problemId, User user) {
        return problemRepository.findByIdAndUserId(problemId, user.getId())
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "Problem not found"));
    }
}
