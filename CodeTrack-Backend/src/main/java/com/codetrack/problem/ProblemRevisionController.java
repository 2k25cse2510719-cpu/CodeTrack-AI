
package com.codetrack.problem;

import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/revisions")
public class ProblemRevisionController {

    private final ProblemRevisionService service;

    public ProblemRevisionController(ProblemRevisionService service) {
        this.service = service;
    }

    @PostMapping("/problems/{problemId}")
    @ResponseStatus(HttpStatus.CREATED)
    public ProblemRevisionResponse schedule(
            @PathVariable Long problemId,
            @Valid @RequestBody ProblemRevisionRequest request,
            Authentication authentication) {
        return service.schedule(
                problemId,
                request.scheduledDate(),
                authentication.getName());
    }

    @GetMapping("/due")
    public List<ProblemRevisionResponse> getDue(
            Authentication authentication) {
        return service.getDue(authentication.getName());
    }

    @GetMapping("/upcoming")
    public List<ProblemRevisionResponse> getUpcoming(
            Authentication authentication) {
        return service.getUpcoming(authentication.getName());
    }

    @GetMapping("/history")
    public List<ProblemRevisionResponse> getHistory(
            Authentication authentication) {
        return service.getHistory(authentication.getName());
    }

    @PostMapping("/{revisionId}/complete")
    public ProblemRevisionResponse complete(
            @PathVariable Long revisionId,
            Authentication authentication) {
        return service.complete(revisionId, authentication.getName());
    }
}
