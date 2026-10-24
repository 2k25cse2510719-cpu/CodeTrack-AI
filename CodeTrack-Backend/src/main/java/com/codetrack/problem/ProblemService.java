package com.codetrack.problem;

import com.codetrack.auth.User;
import com.codetrack.auth.UserRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Service
public class ProblemService {

    private final ProblemRepository repository;
    private final UserRepository userRepository;

    public ProblemService(
            ProblemRepository repository,
            UserRepository userRepository) {
        this.repository = repository;
        this.userRepository = userRepository;
    }

    @Transactional(readOnly = true)
    public List<Problem> getAll(String email) {
        User user = getUser(email);
        return repository.findAllByUserIdOrderByCreatedAtDesc(user.getId());
    }

    @Transactional(readOnly = true)
    public Problem getById(Long id, String email) {
        User user = getUser(email);

        return repository.findByIdAndUserId(id, user.getId())
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "Problem not found"));
    }

    public Problem create(ProblemRequest request, String email) {
        User user = getUser(email);

        Problem problem = new Problem();
        problem.setUser(user);
        apply(problem, request);

        return repository.save(problem);
    }

    public Problem update(Long id, ProblemRequest request, String email) {
        Problem problem = getById(id, email);
        apply(problem, request);
        return repository.save(problem);
    }

    public void delete(Long id, String email) {
        Problem problem = getById(id, email);
        repository.delete(problem);
    }

    private User getUser(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.UNAUTHORIZED, "User not found"));
    }

    private void apply(Problem problem, ProblemRequest request) {
        problem.setTitle(request.title().trim());
        problem.setPlatform(request.platform());
        problem.setDifficulty(request.difficulty());
        problem.setTopic(request.topic());
        problem.setSelectedPattern(request.selectedPattern());

        // verifiedPattern is intentionally not writable through the regular user API.
        // A trusted curation/admin workflow can populate it separately.

        problem.setUrl(request.url());
        problem.setStatus(
                request.status() == null
                        ? ProblemStatus.TODO
                        : request.status());
        problem.setSolvedDate(request.solvedDate());
        problem.setNotes(request.notes());
    }
}
