
package com.codetrack.auth;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthMeController {

    private final UserRepository userRepository;

    public AuthMeController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @GetMapping("/me")
    public ResponseEntity<?> me(Authentication authentication) {
        if (authentication == null || !authentication.isAuthenticated()) {
            return ResponseEntity.status(401).body(
                Map.of("message", "Authentication required")
            );
        }

        return userRepository.findByEmail(authentication.getName())
            .map(user -> ResponseEntity.ok(Map.of(
                "id", user.getId(),
                "name", user.getName(),
                "email", user.getEmail()
            )))
            .orElseGet(() -> ResponseEntity.status(401).body(
                Map.of("message", "User not found")
            ));
    }
}
