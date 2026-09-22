package edu.lynchburg.terra.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class ParkingStatusUpdateRequest {
    @NotBlank(message = "Space ID is required")
    private String spaceId;

    @NotNull(message = "Occupancy status is required")
    private Boolean isOccupied;

    public String getSpaceId() { return spaceId; }
    public void setSpaceId(String spaceId) { this.spaceId = spaceId; }

    public Boolean getIsOccupied() { return isOccupied; }
    public void setIsOccupied(Boolean isOccupied) { this.isOccupied = isOccupied; }
}