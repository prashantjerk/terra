package edu.lynchburg.terra.dto;

import jakarta.validation.constraints.NotNull;

public record UpdateParkingSpaceRequest(@NotNull Boolean occupied) {}
