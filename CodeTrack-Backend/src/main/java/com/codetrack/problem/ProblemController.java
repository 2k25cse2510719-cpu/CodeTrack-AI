
package com.codetrack.problem;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
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
    public List<ProblemResponse> getAll(Authentication authentication) {
        return service.getAll(authentication.getName())
                .stream()
                .map(ProblemResponse::from)
                .toList();
    }

    @GetMapping("/{id}")
    public ProblemResponse getOne(
            @PathVariable Long id,
            Authentication authentication) {
        return ProblemResponse.from(
                service.getById(id, authentication.getName()));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProblemResponse create(
            @Valid @RequestBody ProblemRequest request,
            Authentication authentication) {
        return ProblemResponse.from(
                service.create(request, authentication.getName()));
    }

    @PutMapping("/{id}")
    public ProblemResponse update(
            @PathVariable Long id,
            @Valid @RequestBody ProblemRequest request,
            Authentication authentication) {
        return ProblemResponse.from(
                service.update(id, request, authentication.getName()));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(
            @PathVariable Long id,
            Authentication authentication) {
        service.delete(id, authentication.getName());
    }
}
