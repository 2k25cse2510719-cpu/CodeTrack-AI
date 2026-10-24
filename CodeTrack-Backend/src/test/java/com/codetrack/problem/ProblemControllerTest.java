
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

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProblemControllerTest {

    private static final String AUTH_URL = "/api/v1/auth";
    private static final String PROBLEMS_URL = "/api/v1/problems";

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private String token;

    @BeforeEach
    void setUp() throws Exception {
        String unique = UUID.randomUUID().toString().replace("-", "");
        String email = "problemtest" + unique + "@example.com";
        String password = "TestPassword123";

        registerUser("Problem Test User", email, password);
        token = loginUser(email, password);
    }

    @Test
    void unauthenticatedRequestIsRejected() throws Exception {
        mockMvc.perform(get(PROBLEMS_URL))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void invalidJwtIsRejected() throws Exception {
        mockMvc.perform(get(PROBLEMS_URL)
                        .header("Authorization", "Bearer invalid.jwt.token"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void authenticatedUserCanCreateProblem() throws Exception {
        mockMvc.perform(post(PROBLEMS_URL)
                        .header("Authorization", bearerToken())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(problemJson("Two Sum")))
                .andExpect(status().is2xxSuccessful())
                .andExpect(jsonPath("$.id").exists())
                .andExpect(jsonPath("$.title").value("Two Sum"));
    }

    @Test
    void authenticatedUserCanListProblems() throws Exception {
        createProblem("Two Sum");

        mockMvc.perform(get(PROBLEMS_URL)
                        .header("Authorization", bearerToken()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].title").value("Two Sum"));
    }

    @Test
    void authenticatedUserCanRetrieveProblemById() throws Exception {
        long id = createProblem("Valid Parentheses");

        mockMvc.perform(get(PROBLEMS_URL + "/" + id)
                        .header("Authorization", bearerToken()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(id))
                .andExpect(jsonPath("$.title").value("Valid Parentheses"));
    }

    @Test
    void authenticatedUserCanUpdateProblem() throws Exception {
        long id = createProblem("Old Title");

        mockMvc.perform(put(PROBLEMS_URL + "/" + id)
                        .header("Authorization", bearerToken())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(problemJson("Updated Title")))
                .andExpect(status().is2xxSuccessful())
                .andExpect(jsonPath("$.title").value("Updated Title"));
    }

    @Test
    void authenticatedUserCanDeleteProblem() throws Exception {
        long id = createProblem("Delete Me");

        mockMvc.perform(delete(PROBLEMS_URL + "/" + id)
                        .header("Authorization", bearerToken()))
                .andExpect(status().is2xxSuccessful());

        mockMvc.perform(get(PROBLEMS_URL + "/" + id)
                        .header("Authorization", bearerToken()))
                .andExpect(status().isNotFound());
    }

    @Test
    void nonexistentProblemReturnsNotFound() throws Exception {
        long nonexistentId = 9_000_000_000L;

        mockMvc.perform(get(PROBLEMS_URL + "/" + nonexistentId)
                        .header("Authorization", bearerToken()))
                .andExpect(status().isNotFound());
    }

    @Test
    void invalidProblemInputIsRejected() throws Exception {
        String invalidJson = """
                {
                    "title": "",
                    "platform": "LeetCode",
                    "difficulty": "EASY",
                    "topic": "Arrays",
                    "url": "https://leetcode.com/problems/two-sum/",
                    "status": "TODO",
                    "solvedDate": null,
                    "notes": "Invalid title test"
                }
                """;

        mockMvc.perform(post(PROBLEMS_URL)
                        .header("Authorization", bearerToken())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(invalidJson))
                .andExpect(status().is4xxClientError());
    }

    @Test
    void userCannotAccessAnotherUsersProblem() throws Exception {
        long id = createProblem("Private Problem");
        String otherToken = registerAndLoginAnotherUser();

        mockMvc.perform(get(PROBLEMS_URL + "/" + id)
                        .header("Authorization", "Bearer " + otherToken))
                .andExpect(status().isNotFound());
    }

    @Test
    void userCannotUpdateAnotherUsersProblem() throws Exception {
        long id = createProblem("Private Problem");
        String otherToken = registerAndLoginAnotherUser();

        mockMvc.perform(put(PROBLEMS_URL + "/" + id)
                        .header("Authorization", "Bearer " + otherToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(problemJson("Unauthorized Update")))
                .andExpect(status().isNotFound());

        mockMvc.perform(get(PROBLEMS_URL + "/" + id)
                        .header("Authorization", bearerToken()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("Private Problem"));
    }

    @Test
    void userCannotDeleteAnotherUsersProblem() throws Exception {
        long id = createProblem("Private Problem");
        String otherToken = registerAndLoginAnotherUser();

        mockMvc.perform(delete(PROBLEMS_URL + "/" + id)
                        .header("Authorization", "Bearer " + otherToken))
                .andExpect(status().isNotFound());

        mockMvc.perform(get(PROBLEMS_URL + "/" + id)
                        .header("Authorization", bearerToken()))
                .andExpect(status().isOk());
    }

    private long createProblem(String title) throws Exception {
        MvcResult result = mockMvc.perform(post(PROBLEMS_URL)
                        .header("Authorization", bearerToken())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(problemJson(title)))
                .andExpect(status().is2xxSuccessful())
                .andReturn();

        JsonNode response = objectMapper.readTree(
                result.getResponse().getContentAsString()
        );

        assertTrue(response.hasNonNull("id"),
                "Created problem should have an ID");

        return response.get("id").asLong();
    }

    private void registerUser(
            String name, String email, String password
    ) throws Exception {
        String json = """
                {
                    "name": "%s",
                    "email": "%s",
                    "password": "%s"
                }
                """.formatted(name, email, password);

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
                result.getResponse().getContentAsString()
        ).path("token").asText();

        assertNotNull(jwt);
        assertFalse(jwt.isBlank(), "Login should return a JWT");

        return jwt;
    }

    private String registerAndLoginAnotherUser() throws Exception {
        String unique = UUID.randomUUID().toString().replace("-", "");
        String email = "anotheruser" + unique + "@example.com";
        String password = "TestPassword123";

        registerUser("Another Test User", email, password);
        return loginUser(email, password);
    }

    private String bearerToken() {
        return "Bearer " + token;
    }

    private String problemJson(String title) {
        return """
                {
                    "title": "%s",
                    "platform": "LeetCode",
                    "difficulty": "EASY",
                    "topic": "Arrays",
                    "url": "https://leetcode.com/problems/two-sum/",
                    "status": "TODO",
                    "solvedDate": null,
                    "notes": "Created by integration test"
                }
                """.formatted(title);
    }
}
