package com.codetrack.readiness;

import com.fasterxml.jackson.databind.JsonNode;

public record ReadinessResponse(
        JsonNode features,
        JsonNode readiness
) {}