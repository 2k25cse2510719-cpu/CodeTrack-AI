
package com.codetrack.problem;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProblemRevisionControllerTest {

    private static final String AUTH_URL = "/api/v1/auth";
    private static final String PROBLEMS_URL = "/api/v1/problems";
    private static final String REVISIONS_URL = "/api/v1/revisions";

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private String token;

    @BeforeEach
    void setUp() throws Exception {
        String unique = UUID.randomUUID().toString().replace("-", "");
        String email = "revisiontest" + unique + "@example.com";
        String password = "TestPassword123";

        registerUser(email, password);
        token = loginUser(email, password);
    }

    @Test
    void unauthenticatedDueRequestIsRejected() throws Exception {
        mockMvc.perform(get(REVISIONS_URL + "/due"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void canScheduleRevisionForSolvedProblem() throws Exception {
        long problemId = createSolvedProblem("Two Sum");

        mockMvc.perform(post(REVISIONS_URL + "/problems/" + problemId)
                        .header("Authorization", bearerToken())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"scheduledDate":"2099-01-01"}
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.problemId").value(problemId))
                .andExpect(jsonPath("$.status").value("SCHEDULED"));
    }

    @Test
    void cannotScheduleRevisionForUnsolvedProblem() throws Exception {
        long problemId = createProblem("TODO Problem", "TODO");

        mockMvc.perform(post(REVISIONS_URL + "/problems/" + problemId)
                        .header("Authorization", bearerToken())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"scheduledDate":"2099-01-01"}
                                """))
                .andExpect(status().isBadRequest());
    }

    @Test
    void cannotScheduleRevisionForAnotherUsersProblem() throws Exception {
        long problemId = createSolvedProblem("Private Problem");
        String otherToken = registerAndLoginAnotherUser();

        mockMvc.perform(post(REVISIONS_URL + "/problems/" + problemId)
                        .header("Authorization", "Bearer " + otherToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"scheduledDate":"2099-01-01"}
                                """))
                .andExpect(status().isNotFound());
    }

    @Test
    void dueAndHistoryEndpointsRequireAuthentication() throws Exception {
        mockMvc.perform(get(REVISIONS_URL + "/due"))
                .andExpect(status().isUnauthorized());

        mockMvc.perform(get(REVISIONS_URL + "/history"))
                .andExpect(status().isUnauthorized());
    }

    private long createSolvedProblem(String title) throws Exception {
        return createProblem(title, "SOLVED");
    }

    private long createProblem(String title, String status) throws Exception {
        String json = """
                {
                    "title": "%s",
                    "platform": "LeetCode",
                    "difficulty": "EASY",
                    "topic": "Arrays",
                    "status": "%s",
                    "solvedDate": "2026-10-25",
                    "notes": "Revision integration test"
                }
                """.formatted(title, status);

        MvcResult result = mockMvc.perform(post(PROBLEMS_URL)
                        .header("Authorization", bearerToken())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json))
                .andExpect(status().isCreated())
                .andReturn();

        JsonNode response = objectMapper.readTree(
                result.getResponse().getContentAsString());

        assertTrue(response.hasNonNull("id"));
        return response.get("id").asLong();
    }

    private void registerUser(String email, String password)
            throws Exception {
        String json = """
                {
                    "name": "Revision Test User",
                    "email": "%s",
                    "password": "%s"
                }
                """.formatted(email, password);

        mockMvc.perform(post(AUTH_URL + "/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json))
                .andExpect(status().isCreated());
    }

    private String loginUser(String email, String password)
            throws Exception {
        String json = """
                {
                    "email": "%s",
                    "password": "%s"
                }
                """.formatted(email, password);

        MvcResult result = mockMvc.perform(post(AUTH_URL + "/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json))
                .andExpect(status().isOk())
                .andReturn();

        String jwt = objectMapper.readTree(
                result.getResponse().getContentAsString())
                .path("token").asText();

        assertFalse(jwt.isBlank());
        return jwt;
    }

    private String registerAndLoginAnotherUser() throws Exception {
        String unique = UUID.randomUUID().toString().replace("-", "");
        String email = "anotherrevision" + unique + "@example.com";
        String password = "TestPassword123";

        registerUser(email, password);
        return loginUser(email, password);
    }

    private String bearerToken() {
        return "Bearer " + token;
    }
}
