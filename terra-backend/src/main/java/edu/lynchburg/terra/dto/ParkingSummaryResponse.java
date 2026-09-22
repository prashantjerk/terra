package edu.lynchburg.terra.dto;

import java.util.List;

public class ParkingSummaryResponse {
    private long totalAvailableSpaces;
    private List<String> availableSpaceIds;
    private List<SpaceStatus> allSpaces;

    public ParkingSummaryResponse(long totalAvailableSpaces, List<String> availableSpaceIds, List<SpaceStatus> allSpaces) {
        this.totalAvailableSpaces = totalAvailableSpaces;
        this.availableSpaceIds = availableSpaceIds;
        this.allSpaces = allSpaces;
    }

    public static class SpaceStatus {
        private String spaceId;
        private Boolean isOccupied;

        public SpaceStatus(String spaceId, Boolean isOccupied) {
            this.spaceId = spaceId;
            this.isOccupied = isOccupied;
        }

        public String getSpaceId() { return spaceId; }
        public Boolean getIsOccupied() { return isOccupied; }
    }

    public long getTotalAvailableSpaces() { return totalAvailableSpaces; }
    public List<String> getAvailableSpaceIds() { return availableSpaceIds; }
    public List<SpaceStatus> getAllSpaces() { return allSpaces; }
}