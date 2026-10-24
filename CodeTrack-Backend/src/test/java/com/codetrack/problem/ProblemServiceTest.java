
package com.codetrack.problem;

import com.codetrack.auth.User;
import com.codetrack.auth.UserRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.server.ResponseStatusException;

import java.util.Collections;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ProblemServiceTest {

    @Mock
    private ProblemRepository repository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private ProblemService service;

    @Test
    void rejectsAccessToProblemNotOwnedByUser() {
        User user = org.mockito.Mockito.mock(User.class);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(user.getId()).thenReturn(3L);
        when(repository.findByIdAndUserId(10L, 3L))
                .thenReturn(Optional.empty());

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.getById(10L, "test@example.com")
        );

        assertEquals(404, exception.getStatusCode().value());
    }

    @Test
    void getAllReturnsOnlyCurrentUsersProblems() {
        User user = org.mockito.Mockito.mock(User.class);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(user.getId()).thenReturn(3L);
        when(repository.findAllByUserIdOrderByCreatedAtDesc(3L))
                .thenReturn(Collections.emptyList());

        var result = service.getAll("test@example.com");

        assertEquals(0, result.size());
        verify(repository).findAllByUserIdOrderByCreatedAtDesc(3L);
    }

    @Test
    void createSavesProblemForCurrentUser() {
        User user = org.mockito.Mockito.mock(User.class);
        ProblemRequest request = org.mockito.Mockito.mock(ProblemRequest.class);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));

        when(request.title()).thenReturn("Two Sum");
        when(request.platform()).thenReturn("LeetCode");
        when(request.difficulty()).thenReturn(null);
        when(request.topic()).thenReturn(null);
        when(request.url()).thenReturn(null);
        when(request.status()).thenReturn(null);
        when(request.solvedDate()).thenReturn(null);
        when(request.notes()).thenReturn(null);

        when(repository.save(org.mockito.ArgumentMatchers.any(Problem.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        Problem result = service.create(request, "test@example.com");

        assertEquals("Two Sum", result.getTitle());
        verify(repository).save(org.mockito.ArgumentMatchers.any(Problem.class));
    }

    @Test
    void updateRejectsProblemNotOwnedByUser() {
        User user = org.mockito.Mockito.mock(User.class);
        ProblemRequest request = org.mockito.Mockito.mock(ProblemRequest.class);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(user.getId()).thenReturn(3L);
        when(repository.findByIdAndUserId(10L, 3L))
                .thenReturn(Optional.empty());

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.update(10L, request, "test@example.com")
        );

        assertEquals(404, exception.getStatusCode().value());
    }

    @Test
    void deleteRejectsProblemNotOwnedByUser() {
        User user = org.mockito.Mockito.mock(User.class);

        when(userRepository.findByEmail("test@example.com"))
                .thenReturn(Optional.of(user));
        when(user.getId()).thenReturn(3L);
        when(repository.findByIdAndUserId(10L, 3L))
                .thenReturn(Optional.empty());

        ResponseStatusException exception = assertThrows(
                ResponseStatusException.class,
                () -> service.delete(10L, "test@example.com")
        );

        assertEquals(404, exception.getStatusCode().value());
    }
}
