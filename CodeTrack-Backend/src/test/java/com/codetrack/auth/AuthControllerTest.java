
package com.codetrack.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void healthEndpointIsPublic() throws Exception {
        mockMvc.perform(get("/api/health"))
                .andExpect(status().isOk());
    }

    @Test
    void currentUserEndpointRejectsUnauthenticatedRequest()
            throws Exception {
        mockMvc.perform(get("/api/v1/auth/me"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void loginRejectsInvalidCredentials() throws Exception {
        LoginRequest request = new LoginRequest(
                "missing-user@example.com",
                "WrongPassword123!"
        );

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void registrationRejectsInvalidInput() throws Exception {
        RegisterRequest request = new RegisterRequest(
                "",
                "not-an-email",
                "short"
        );

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }


@Test
void registrationCreatesNewAccount() throws Exception {
    String uniqueEmail = "test-" + java.util.UUID.randomUUID()
            + "@example.com";

    RegisterRequest request = new RegisterRequest(
            "Test User",
            uniqueEmail,
            "StrongPass123!"
    );

    var result = mockMvc.perform(post("/api/v1/auth/register")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
            .andReturn();

    System.out.println("REGISTRATION STATUS: "
            + result.getResponse().getStatus());
    System.out.println("REGISTRATION BODY: "
            + result.getResponse().getContentAsString());

    org.junit.jupiter.api.Assertions.assertEquals(
            201, result.getResponse().getStatus());
}


    @Test
    void duplicateEmailReturnsConflict() throws Exception {
        String uniqueEmail = "duplicate-" + java.util.UUID.randomUUID()
                + "@example.com";

        RegisterRequest request = new RegisterRequest(
                "Test User",
                uniqueEmail,
                "StrongPass123!"
        );

        String body = objectMapper.writeValueAsString(request);

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isCreated());

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.message").exists());
    }
}
