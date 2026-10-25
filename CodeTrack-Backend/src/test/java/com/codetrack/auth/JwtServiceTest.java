
package com.codetrack.auth;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;

class JwtServiceTest {

    private static final String SECRET =
            "test-secret-key-that-is-at-least-32-bytes-long";
    private static final String DIFFERENT_SECRET =
            "different-test-secret-that-is-32-bytes-long";

    private JwtService jwtService;
    private SecretKey differentKey;

    @BeforeEach
    void setUp() {
        jwtService = new JwtService(SECRET, 60_000);
        differentKey = Keys.hmacShaKeyFor(
                DIFFERENT_SECRET.getBytes(StandardCharsets.UTF_8));
    }

    @Test
    void rejectsTokenSignedWithDifferentSecret() {
        String forgedToken = Jwts.builder()
                .subject("test@example.com")
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(differentKey)
                .compact();

        assertFalse(jwtService.isTokenValid(forgedToken));
        assertThrows(
                Exception.class,
                () -> jwtService.extractClaims(forgedToken));
    }

    @Test
    void rejectsExpiredToken() {
        Date now = new Date();
        String expiredToken = Jwts.builder()
                .subject("test@example.com")
                .issuedAt(new Date(now.getTime() - 120_000))
                .expiration(new Date(now.getTime() - 60_000))
                .signWith(Keys.hmacShaKeyFor(
                        SECRET.getBytes(StandardCharsets.UTF_8)))
                .compact();

        assertFalse(jwtService.isTokenValid(expiredToken));
        assertThrows(
                Exception.class,
                () -> jwtService.extractClaims(expiredToken));
    }

    @Test
    void rejectsMalformedToken() {
        assertFalse(jwtService.isTokenValid("not.a.valid.jwt"));
        assertThrows(
                Exception.class,
                () -> jwtService.extractClaims("not.a.valid.jwt"));
    }

    @Test
    void rejectsSecretShorterThan32Bytes() {
        assertThrows(
                IllegalArgumentException.class,
                () -> new JwtService("too-short", 60_000));
    }
}
