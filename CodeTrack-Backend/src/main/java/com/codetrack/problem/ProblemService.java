package com.codetrack.problem;

import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;

@Service
public class ProblemService {
    private final ProblemRepository repository;

    public ProblemService(ProblemRepository repository) {
        this.repository = repository;
    }

    public List<Problem> getAll() {
        return repository.findAllByOrderByCreatedAtDesc();
    }

    public Problem getById(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Problem not found"));
    }

    public Problem create(ProblemRequest request) {
        Problem problem = new Problem();
        apply(problem, request);
        return repository.save(problem);
    }

    public Problem update(Long id, ProblemRequest request) {
        Problem problem = getById(id);
        apply(problem, request);
        return repository.save(problem);
    }

    public void delete(Long id) {
        Problem problem = getById(id);
        repository.delete(problem);
    }

    private void apply(Problem problem, ProblemRequest request) {
       problem.setTitle(request.title().trim());
problem.setPlatform(request.platform());
problem.setDifficulty(request.difficulty());
problem.setTopic(request.topic());
problem.setUrl(request.url());
problem.setStatus(request.status() == null ? ProblemStatus.TODO : request.status());
problem.setSolvedDate(request.solvedDate());
problem.setNotes(request.notes());
    }
}
