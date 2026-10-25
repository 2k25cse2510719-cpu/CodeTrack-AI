
package com.codetrack.problem;

import com.codetrack.auth.User;
import com.codetrack.auth.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ProblemRevisionServiceTest {

    @Mock
    private ProblemRepository problemRepository;

    @Mock
    private ProblemRevisionRepository revisionRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private ProblemRevisionService service;

    private User user;
    private Problem problem;

    @BeforeEach
    void setUp() {
        user = mock(User.class);
        when(user.getId()).thenReturn(7L);

        problem = new Problem();
        problem.setId(12L);
        problem.setTitle("Two Sum");
        problem.setStatus(ProblemStatus.SOLVED);
    }

    @Test
    void schedulesRevisionForOwnedSolvedProblem() {
        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(problemRepository.findByIdAndUserId(12L, 7L))
                .thenReturn(Optional.of(problem));
        when(revisionRepository
                .existsByProblemIdAndProblemUserIdAndStatus(
                        12L, 7L, RevisionStatus.SCHEDULED))
                .thenReturn(false);
        when(revisionRepository.save(any(ProblemRevision.class)))
                .thenAnswer(invocation -> {
                    ProblemRevision revision = invocation.getArgument(0);
                    revision.setScheduledDate(LocalDate.now().plusDays(1));
                    return revision;
                });

        var result = service.schedule(
                12L, LocalDate.now().plusDays(1), "test@example.com");

        assertEquals(12L, result.problemId());
        assertEquals("Two Sum", result.problemTitle());
        assertEquals(RevisionStatus.SCHEDULED, result.status());
        verify(revisionRepository).save(any(ProblemRevision.class));
    }

    @Test
    void rejectsSchedulingForUnsolvedProblem() {
        problem.setStatus(ProblemStatus.TODO);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(problemRepository.findByIdAndUserId(12L, 7L))
                .thenReturn(Optional.of(problem));

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.schedule(
                        12L, LocalDate.now(), "test@example.com"));

        assertEquals(400, exception.getStatusCode().value());
        verify(revisionRepository, never()).save(any());
    }

    @Test
    void rejectsPastRevisionDate() {
        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(problemRepository.findByIdAndUserId(12L, 7L))
                .thenReturn(Optional.of(problem));

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.schedule(
                        12L, LocalDate.now().minusDays(1),
                        "test@example.com"));

        assertEquals(400, exception.getStatusCode().value());
        verify(revisionRepository, never()).save(any());
    }

    @Test
    void rejectsDuplicateScheduledRevision() {
        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(problemRepository.findByIdAndUserId(12L, 7L))
                .thenReturn(Optional.of(problem));
        when(revisionRepository
                .existsByProblemIdAndProblemUserIdAndStatus(
                        12L, 7L, RevisionStatus.SCHEDULED))
                .thenReturn(true);

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.schedule(
                        12L, LocalDate.now(), "test@example.com"));

        assertEquals(409, exception.getStatusCode().value());
        verify(revisionRepository, never()).save(any());
    }

    @Test
    void rejectsSchedulingProblemOwnedByAnotherUser() {
        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(problemRepository.findByIdAndUserId(12L, 7L))
                .thenReturn(Optional.empty());

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.schedule(
                        12L, LocalDate.now(), "test@example.com"));

        assertEquals(404, exception.getStatusCode().value());
        verify(revisionRepository, never()).save(any());
    }

    @Test
    void returnsDueRevisionsForCurrentUser() {
        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(revisionRepository
                .findAllByProblemUserIdAndStatusAndScheduledDateLessThanEqualOrderByScheduledDateAsc(
                        7L, RevisionStatus.SCHEDULED, LocalDate.now()))
                .thenReturn(List.of());

        var result = service.getDue("test@example.com");

        assertTrue(result.isEmpty());
        verify(revisionRepository)
                .findAllByProblemUserIdAndStatusAndScheduledDateLessThanEqualOrderByScheduledDateAsc(
                        7L, RevisionStatus.SCHEDULED, LocalDate.now());
    }

    @Test
    void returnsCompletedRevisionHistory() {
        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(revisionRepository
                .findAllByProblemUserIdAndStatusOrderByCompletedAtDesc(
                        7L, RevisionStatus.COMPLETED))
                .thenReturn(List.of());

        var result = service.getHistory("test@example.com");

        assertTrue(result.isEmpty());
        verify(revisionRepository)
                .findAllByProblemUserIdAndStatusOrderByCompletedAtDesc(
                        7L, RevisionStatus.COMPLETED);
    }

    @Test
    void completesRevisionAndSchedulesNextOne() {
        ProblemRevision revision = new ProblemRevision();
        revision.setProblem(problem);
        revision.setScheduledDate(LocalDate.now());
        revision.setStatus(RevisionStatus.SCHEDULED);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(revisionRepository.findByIdAndProblemUserId(50L, 7L))
                .thenReturn(Optional.of(revision));
        when(revisionRepository.save(any(ProblemRevision.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));
        when(revisionRepository
                .findAllByProblemIdAndProblemUserIdAndStatus(
                        12L, 7L, RevisionStatus.COMPLETED))
                .thenReturn(List.of(revision));

        var result = service.complete(50L, "test@example.com");

        assertEquals(RevisionStatus.COMPLETED, result.status());
        assertNotNull(result.completedAt());

        ArgumentCaptor<ProblemRevision> captor =
                ArgumentCaptor.forClass(ProblemRevision.class);
        verify(revisionRepository, times(2)).save(captor.capture());

        ProblemRevision next = captor.getAllValues().get(1);
        assertEquals(RevisionStatus.SCHEDULED, next.getStatus());
        assertEquals(LocalDate.now().plusDays(1), next.getScheduledDate());
    }

    @Test
    void rejectsCompletingRevisionBeforeScheduledDate() {
        ProblemRevision revision = new ProblemRevision();
        revision.setProblem(problem);
        revision.setScheduledDate(LocalDate.now().plusDays(2));
        revision.setStatus(RevisionStatus.SCHEDULED);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(revisionRepository.findByIdAndProblemUserId(50L, 7L))
                .thenReturn(Optional.of(revision));

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.complete(50L, "test@example.com"));

        assertEquals(400, exception.getStatusCode().value());
        assertEquals(RevisionStatus.SCHEDULED, revision.getStatus());
        assertNull(revision.getCompletedAt());
        verify(revisionRepository, never()).save(any());
    }

    @Test
    void rejectsCompletingRevisionOwnedByAnotherUser() {
        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(revisionRepository.findByIdAndProblemUserId(50L, 7L))
                .thenReturn(Optional.empty());

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.complete(50L, "test@example.com"));

        assertEquals(404, exception.getStatusCode().value());
        verify(revisionRepository, never()).save(any());
    }

    @Test
    void rejectsCompletingAlreadyCompletedRevision() {
        ProblemRevision revision = new ProblemRevision();
        revision.setProblem(problem);
        revision.setStatus(RevisionStatus.COMPLETED);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(revisionRepository.findByIdAndProblemUserId(50L, 7L))
                .thenReturn(Optional.of(revision));

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.complete(50L, "test@example.com"));

        assertEquals(409, exception.getStatusCode().value());
        verify(revisionRepository, never()).save(any());
    }
}
