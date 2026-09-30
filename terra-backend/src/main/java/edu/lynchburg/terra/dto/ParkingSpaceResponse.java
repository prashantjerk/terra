package edu.lynchburg.terra.dto;

import java.time.LocalDateTime;
import edu.lynchburg.terra.model.ParkingSpace;

public record ParkingSpaceResponse(String spaceId, String label, Boolean occupied,
                                   LocalDateTime lastUpdated) {
    public static ParkingSpaceResponse from(ParkingSpace space) {
        return new ParkingSpaceResponse(space.getSpaceId(), space.getLabel(),
                                        space.getOccupied(), space.getLastUpdated());
    }
}
