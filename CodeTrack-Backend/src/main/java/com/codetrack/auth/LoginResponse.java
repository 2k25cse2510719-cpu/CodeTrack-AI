
package com.codetrack.auth;

public record LoginResponse(
        Long id,
        String name,
        String email,
        String token
) {}
