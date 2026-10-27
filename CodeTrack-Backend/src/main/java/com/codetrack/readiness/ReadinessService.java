package com.codetrack.readiness;

import com.codetrack.problem.Problem;
import com.codetrack.problem.ProblemRevisionResponse;
import com.codetrack.problem.ProblemRevisionService;
import com.codetrack.problem.ProblemService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.net.http.HttpClient;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class ReadinessService {

    private final ProblemService problemService;
    private final ProblemRevisionService revisionService;
    private final ObjectMapper objectMapper;
    private final RestClient restClient;

    public ReadinessService(
            ProblemService problemService,
            ProblemRevisionService revisionService,
            ObjectMapper objectMapper,
            @Value("${app.readiness.python-url}") String pythonUrl) {

        this.problemService = problemService;
        this.revisionService = revisionService;
        this.objectMapper = objectMapper;

        HttpClient jdkClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .build();

        JdkClientHttpRequestFactory requestFactory =
                new JdkClientHttpRequestFactory(jdkClient);

        this.restClient = RestClient.builder()
                .baseUrl(pythonUrl.replaceAll("/+$", ""))
                .requestFactory(requestFactory)
                .build();
    }

    public ReadinessResponse getReadiness(String email) {
        List<Problem> problems = problemService.getAll(email);

        List<Map<String, Object>> problemData = problems.stream()
                .map(problem -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put("id", problem.getId());
                    data.put("title", problem.getTitle());
                    data.put("platform", problem.getPlatform());
                    data.put("difficulty", problem.getDifficulty());
                    data.put("topic", problem.getTopic());
                    data.put("selectedPattern", problem.getSelectedPattern());
                    data.put("verifiedPattern", problem.getVerifiedPattern());
                    data.put("status", problem.getStatus().name());
                    data.put("solvedDate", problem.getSolvedDate());
                    return data;
                })
                .toList();

        // Together these cover scheduled revisions due today or earlier,
        // future scheduled revisions, and completed revision history.
        List<ProblemRevisionResponse> revisions = new ArrayList<>();
        revisions.addAll(revisionService.getDue(email));
        revisions.addAll(revisionService.getUpcoming(email));
        revisions.addAll(revisionService.getHistory(email));

        List<Map<String, Object>> revisionData = revisions.stream()
                .map(revision -> {
                    Map<String, Object> data = new LinkedHashMap<>();
                    data.put("problemId", revision.problemId());
                    data.put("scheduledDate", revision.scheduledDate());
                    data.put("completedAt", revision.completedAt());
                    data.put("status", revision.status().name());
                    return data;
                })
                .toList();

        Map<String, Object> payload = Map.of(
                "problems", problemData,
                "revisions", revisionData
        );

        JsonNode response = restClient.post()
                .uri("/predict/readiness")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .body(payload)
                .retrieve()
                .body(JsonNode.class);

        if (response == null || response.isNull()) {
            throw new IllegalStateException(
                    "Python readiness service returned an empty response.");
        }

        return new ReadinessResponse(
                response.path("features"),
                response.path("readiness")
        );
    }
}
