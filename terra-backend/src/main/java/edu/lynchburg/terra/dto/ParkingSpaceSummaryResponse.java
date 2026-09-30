package edu.lynchburg.terra.dto;

public record ParkingSpaceSummaryResponse(long totalSpaces, long occupiedSpaces,
                                          long availableSpaces, long unknownSpaces) {}
