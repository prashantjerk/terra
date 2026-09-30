package edu.lynchburg.terra.dto;

import jakarta.validation.constraints.*;

public record CreateParkingSpaceRequest(
    @NotBlank @Pattern(regexp = "(?!summary$)[A-Za-z0-9_-]{1,32}") String spaceId,
    @NotBlank @Size(max = 100) String label,
    Boolean occupied
) {}
