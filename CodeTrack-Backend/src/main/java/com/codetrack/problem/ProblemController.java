package com.codetrack.problem;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/problems")
public class ProblemController {
    private final ProblemService service;

    public ProblemController(ProblemService service) {
        this.service = service;
    }

    @GetMapping
    public List<Problem> getAll() {
        return service.getAll();
    }

    @GetMapping("/{id}")
    public Problem getOne(@PathVariable Long id) {
        return service.getById(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Problem create(@Valid @RequestBody ProblemRequest request) {
        return service.create(request);
    }

    @PutMapping("/{id}")
    public Problem update(@PathVariable Long id, @Valid @RequestBody ProblemRequest request) {
        return service.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        service.delete(id);
    }
}
